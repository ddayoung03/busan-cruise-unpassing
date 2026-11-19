"""B. 최적 루트 → 시간표(언제 어디로, 어떻게 이동, 줄·식사 몇 시) + 지도

입력: 02_정제데이터/루트결과_1118_B.csv(시나리오별 1위 루트), food_nodes·travel_time
산출: 02_정제데이터/루트시간표_1118_B.csv, 04_그림/그림8_S1~S6루트지도.png(실제 지도 타일 위), 04_그림/루트지도_1118_B.html(folium 있을 때)
실행: python 03_코드/make_itinerary.py   (프로젝트 루트에서, 수 초)
시간표는 최적화와 같은 규칙(evaluate)으로 '가장 이른 가능한 줄 서기'를 다시 계산한 것이다.
"""
import platform
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_코드"))
from cruise_route_optw import fmt   # noqa: E402

# run_B_model.py의 설정부(문제·시나리오 정의)만 실행한다. 모델 계산('# 1)' 이후)은 돌리지 않는다.
_src = (ROOT / "03_코드/run_B_model.py").read_text(encoding="utf-8")
_ns = {"__file__": str(ROOT / "03_코드/run_B_model.py")}
exec(_src[:_src.index("# 1) 시나리오별")], _ns)
SCEN, P = _ns["SCEN"], _ns["P"]

plt.rcParams["font.family"] = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"
D, F = ROOT / "02_정제데이터", ROOT / "04_그림"
travel = pd.read_csv(D / "travel_time_1118_B.csv")
name2id = {P.A[n]["name_ko"]: n for n in P.ids}
res = pd.read_csv(D / "루트결과_1118_B.csv", dtype={"순위": str})


def mode_of(a, b):
    t = travel[(travel.from_id == a) & (travel.to_id == b)].copy()
    t["eff"] = t["minutes"] + (t["mode"] == "taxi") * 5
    r = t.sort_values("eff").iloc[0]
    return ("도보" if r["mode"] == "walk" else "택시"), r["eff"]


rows = []
for sc in SCEN:
    top = res[(res["시나리오"] == sc.name) & (res["순위"] == "1")].iloc[0]
    route = [name2id[x] for x in top["루트"].split(" → ")]
    ev = P.evaluate(route, sc)
    rows.append({"시나리오": sc.name, "순서": 0, "장소": P.A[sc.depot]["name_ko"], "이동": "", "이동(분)": "",
                 "도착": "", "줄 서기": "", "줄(분)": "", "먹기 시작": "", "떠남": fmt(sc.start), "메뉴·가격": "하선"})
    for i, s in enumerate(ev["stops"], 1):
        md, mins = mode_of(s["from"], s["node"])
        a = P.A[s["node"]]
        node = P.nodes.loc[s["node"]]
        rows.append({"시나리오": sc.name, "순서": i, "장소": a["name_ko"], "이동": md, "이동(분)": round(mins),
                     "도착": fmt(s["leave"] + mins), "줄 서기": fmt(s["queue_start"]), "줄(분)": round(s["queue"]),
                     "먹기 시작": fmt(s["begin"]), "떠남": fmt(s["end"]),
                     "메뉴·가격": f"{node['category']} · {int(a['price_krw']):,}원"})
    md, mins = mode_of(route[-1], sc.depot)
    rows.append({"시나리오": sc.name, "순서": len(route) + 1, "장소": P.A[sc.depot]["name_ko"] + " (복귀)", "이동": md,
                 "이동(분)": round(mins), "도착": fmt(ev["return_min"]), "줄 서기": "", "줄(분)": "", "먹기 시작": "",
                 "떠남": "", "메뉴·가격": f"승선 마감 {fmt(sc.deadline() + 30)} (여유 {round(ev['slack_min'])}분)"})
    print(sc.name, "목적함수(시간표 재계산)", ev["objective"], "/ 최적화", top["목적함수"], "/ 규칙 위반 없음", ev["feasible"])
tt = pd.DataFrame(rows)
tt.to_csv(D / "루트시간표_1118_B.csv", index=False, encoding="utf-8-sig")

# ---------- 실제 지도(OpenStreetMap 표준 타일, © OpenStreetMap contributors) 위 루트 ----------
# OSM 타일 이용정책: 소량·캐시·User-Agent 명시·출처 표기. 한 번 받은 타일은 01_원천데이터/map_tiles에 캐시한다.
import io, math, urllib.request
from PIL import Image
TILE_DIR = ROOT / "01_원천데이터/map_tiles"   # 타일 캐시(.gitignore)
TILE_DIR.mkdir(parents=True, exist_ok=True)
R_ = 6378137.0
merc = lambda lon, lat: (math.radians(lon) * R_, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * R_)


def tile(z, x, y):
    f = TILE_DIR / f"{z}_{x}_{y}.png"
    for attempt in range(6):   # 연결이 불안정해 재시도
        if f.exists():
            break
        try:
            req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png",
                                         headers={"User-Agent": "busan-cruise-route-study/1.0"})
            f.write_bytes(urllib.request.urlopen(req, timeout=20).read())
        except OSError:
            continue
    return Image.open(f).convert("RGB")


def basemap(ax, lon0, lat0, lon1, lat1, max_tiles=16):
    """경위도 범위를 덮는 타일을 받아 웹 메르카토르 좌표로 ax에 깐다."""
    for z in range(17, 9, -1):
        n = 2 ** z
        tx = lambda lon: int((lon + 180) / 360 * n)
        ty = lambda lat: int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
        x0, x1, y0, y1 = tx(lon0), tx(lon1), ty(lat1), ty(lat0)
        if (x1 - x0 + 1) * (y1 - y0 + 1) <= max_tiles:
            break
    img = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            img.paste(tile(z, x, y), ((x - x0) * 256, (y - y0) * 256))
    lon_of = lambda x: x / n * 360 - 180
    lat_of = lambda y: math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
    l, b_ = merc(lon_of(x0), lat_of(y1 + 1)); r, t = merc(lon_of(x1 + 1), lat_of(y0))
    ax.imshow(img, extent=(l, r, b_, t), zorder=0)
    (ex0, ey0), (ex1, ey1) = merc(lon0, lat0), merc(lon1, lat1)
    ax.set_xlim(ex0, ex1); ax.set_ylim(ey0, ey1); ax.set_axis_off()


def draw_route(ax, pts, lab_terminal, numbers=True):
    xy = [merc(P.A[n]["lon"], P.A[n]["lat"]) for n in pts]
    for (x0, y0), (x1, y1) in zip(xy, xy[1:]):
        an = ax.annotate("", xy=(x1, y1), xytext=(x0, y0), zorder=2, annotation_clip=False,
                         arrowprops=dict(arrowstyle="-|>", color="#E8573F", lw=2.4, mutation_scale=16, shrinkA=9, shrinkB=9))
        an.arrow_patch.set_clip_box(ax.bbox)   # 확대 패널 밖으로 나가는 화살표는 잘라낸다
    if numbers:
        for i, (x, y) in enumerate(xy[1:-1], 1):
            ax.scatter(x, y, s=330, color="#0B3C5D", edgecolor="white", linewidth=1.5, zorder=3)
            ax.text(x, y, str(i), color="white", ha="center", va="center", fontsize=11, fontweight="bold", zorder=4)
    tx_, ty_ = xy[0]
    ax.scatter(tx_, ty_, marker="s", s=200, color="#1D1D1D", edgecolor="white", zorder=3)
    if lab_terminal:
        ax.text(tx_, ty_, "  " + lab_terminal, fontsize=10, fontweight="bold", va="center", zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", fc="white", ec="none", alpha=0.8))


def bounds(ns, pad=0.25, min_span=0.012):
    lons = [P.A[n]["lon"] for n in ns]; lats = [P.A[n]["lat"] for n in ns]
    cx, cy = (min(lons) + max(lons)) / 2, (min(lats) + max(lats)) / 2
    sx = max(max(lons) - min(lons), min_span) * (1 + 2 * pad) / 2
    sy = max(max(lats) - min(lats), min_span * 0.8) * (1 + 2 * pad) / 2
    return cx - sx, cy - sy, cx + sx, cy + sy


CREDIT = "지도: © OpenStreetMap contributors"
for k, sc in enumerate(SCEN, 1):
    s1 = tt[tt["시나리오"] == sc.name]
    pts = [sc.depot] + [name2id[x] for x in s1["장소"].iloc[1:-1]] + [sc.depot]
    term = "영도 크루즈터미널" if sc.depot == "D2" else "북항 크루즈터미널"
    core = [n for n in pts[1:-1] if P.A[n]["gu"] in ("중구", "영도구", "서구")]   # 남포동·자갈치 밀집 구역
    wide = len(core) < len(pts) - 2 and len(core) >= 2
    if wide:   # 원도심 밖까지 가는 루트: 전체 + 원도심 확대
        fig, (ax, ax2) = plt.subplots(1, 2, figsize=(13, 6.2), gridspec_kw={"width_ratios": [1.15, 1]})
        basemap(ax, *bounds(pts, pad=0.12)); draw_route(ax, pts, term)
        basemap(ax2, *bounds(core + [sc.depot], pad=0.18)); draw_route(ax2, pts, term)
        ax.set_title("전체 루트", fontsize=12); ax2.set_title("원도심 확대", fontsize=12)
    else:
        fig, ax = plt.subplots(figsize=(9, 6.2))
        basemap(ax, *bounds(pts, pad=0.18)); draw_route(ax, pts, term)
    fig.text(0.99, 0.01, CREDIT, ha="right", va="bottom", fontsize=8, color="#555555")
    plt.tight_layout(rect=[0, 0.03, 1, 1]); plt.savefig(F / f"그림8_S{k}루트지도.png", dpi=170); plt.close()
    from PIL import ImageChops   # 흰 여백만 잘라낸다 (bbox_inches='tight'는 잘린 화살표까지 포함해 쓰지 않음)
    im = Image.open(F / f"그림8_S{k}루트지도.png").convert("RGB")
    bb = ImageChops.difference(im, Image.new("RGB", im.size, "white")).getbbox()
    im.crop((max(bb[0] - 12, 0), max(bb[1] - 12, 0), min(bb[2] + 12, im.width), min(bb[3] + 12, im.height))).save(F / f"그림8_S{k}루트지도.png")

try:
    import folium
    m = folium.Map(location=[35.13, 129.07], zoom_start=12, tiles="OpenStreetMap")
    for color, sc in zip(["#1f3b63", "#e07a2f", "#2e8b57", "#8e44ad", "#c0392b", "#16a085"], SCEN):
        sub = tt[tt["시나리오"] == sc.name]
        ids = [sc.depot] + [name2id[x] for x in sub["장소"].iloc[1:-1]] + [sc.depot]
        fg = folium.FeatureGroup(name=sc.name)
        folium.PolyLine([[P.A[n]["lat"], P.A[n]["lon"]] for n in ids], color=color, weight=4).add_to(fg)
        for _, r in sub.iloc[1:-1].iterrows():
            n = name2id[r["장소"]]
            folium.CircleMarker([P.A[n]["lat"], P.A[n]["lon"]], radius=9, color=color, fill=True,
                                tooltip=f"{r['순서']}. {r['장소']} | 도착 {r['도착']} · 줄 {r['줄(분)']}분 · 식사 {r['먹기 시작']}~{r['떠남']}").add_to(fg)
        fg.add_to(m)
    for d in ["D1", "D2"]:
        folium.Marker([P.A[d]["lat"], P.A[d]["lon"]], tooltip=P.A[d]["name_ko"]).add_to(m)
    folium.LayerControl().add_to(m)
    m.save(str(F / "루트지도_1118_B.html"))
except ImportError:
    print("folium 없음: html 지도 생략")
print(tt[tt["시나리오"] == SCEN[0].name].drop(columns="시나리오").to_string(index=False))
