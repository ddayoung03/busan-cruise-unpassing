"""B. 최적 루트 → 시간표(언제 어디로, 어떻게 이동, 줄·식사 몇 시) + 지도

입력: 02_정제데이터/루트결과_1118_B.csv(시나리오별 1위 루트), food_nodes·travel_time
산출: 02_정제데이터/루트시간표_1118_B.csv, 04_그림/그림8_S1~S6루트지도.png, 04_그림/루트지도_1118_B.html(folium 있을 때)
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

# 지도 그림(시나리오별): 좌표 위 번호·화살표 (배경지도 없음) + 오른쪽 시간표
for k, sc in enumerate(SCEN, 1):
    s1 = tt[tt["시나리오"] == sc.name]
    pts = [sc.depot] + [name2id[x] for x in s1["장소"].iloc[1:-1]] + [sc.depot]
    term = "영도 크루즈터미널" if sc.depot == "D2" else "북항 크루즈터미널"
    fig, (ax, lx) = plt.subplots(1, 2, figsize=(11, 6.5), gridspec_kw={"width_ratios": [1.3, 1]})
    for n in P.cands:
        ax.scatter(P.A[n]["lon"], P.A[n]["lat"], s=25, color="#cfd6de", zorder=1)
    for a_, b_ in zip(pts, pts[1:]):
        ax.annotate("", xy=(P.A[b_]["lon"], P.A[b_]["lat"]), xytext=(P.A[a_]["lon"], P.A[a_]["lat"]),
                    arrowprops=dict(arrowstyle="->", color="#e07a2f", lw=1.8), zorder=2)
    for i, n in enumerate(pts[1:-1], 1):
        ax.scatter(P.A[n]["lon"], P.A[n]["lat"], s=260, color="#1f3b63", zorder=3)
        ax.text(P.A[n]["lon"], P.A[n]["lat"], str(i), color="white", ha="center", va="center", fontsize=10, zorder=4)
    ax.scatter(P.A[sc.depot]["lon"], P.A[sc.depot]["lat"], marker="s", s=160, color="black", zorder=3)
    ax.text(P.A[sc.depot]["lon"] + 0.003, P.A[sc.depot]["lat"] - 0.004, term, fontsize=9)
    ax.set_title(f"{sc.name} ({fmt(sc.start)} 하선 → {s1['도착'].iloc[-1]} 복귀)", fontsize=11)
    ax.set_xlabel("경도"); ax.set_ylabel("위도"); ax.set_aspect(1.2)
    lx.axis("off")
    lines = [f"{fmt(sc.start)}  {term} 출발"] + [
        f"{r['먹기 시작']}  {r['순서']}. {r['장소'].split('(')[0]}  ({r['이동']} {r['이동(분)']}분, 줄 {r['줄(분)']}분)"
        for _, r in s1.iloc[1:-1].iterrows()] + [f"{s1['도착'].iloc[-1]}  터미널 복귀 ({s1['메뉴·가격'].iloc[-1]})"]
    lx.text(0, 0.95, "\n\n".join(lines), va="top", fontsize=10)
    plt.tight_layout(rect=[0, 0, 1, 0.95]); plt.savefig(F / f"그림8_S{k}루트지도.png", dpi=200); plt.close()

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
