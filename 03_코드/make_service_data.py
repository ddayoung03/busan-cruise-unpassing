"""서비스(Busan Bite Pass) 데이터 만들기 → 06_서비스/data.js, 06_서비스/map_wide.jpg, map_core.jpg

- 장소: food_nodes(영업·좌표·가격) + 부산시 맛집 API(영·일 이름과 메뉴) + 손으로 쓴 중국어·영어 이름(시장·마을 등)
- 루트: make_service_routes.py 결과(routes.json)에 구간별 이동수단(도보/택시)을 붙인다
- 상인 예보: 2026.5.8 2척 동시 기항일 골목 방문 시나리오(가게별·시간대별 예상 인원, 예시)
- 지도: OpenStreetMap 타일을 이어 붙인 배경 이미지 2장(부산 전체, 원도심) + 웹 메르카토르 범위
실행(프로젝트 루트): python 03_코드/make_service_data.py
"""
import json
import math
import re
import urllib.request
from pathlib import Path

import pandas as pd
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
D, OUT = ROOT / "02_정제데이터", ROOT / "06_서비스"
API = ROOT / "01_원천데이터/data.go.kr/busan_food_api"
TILES = ROOT / "01_원천데이터/map_tiles"
OUT.mkdir(exist_ok=True)

# 공식 이름이 없는 곳(시장·마을·노점)과 중국어 이름은 직접 표기
MANUAL = {
    "D1": ("Busan Port International Cruise Terminal", "釜山港国际客运码头(北港)", "釜山港国際旅客ターミナル(北港)"),
    "D2": ("Yeongdo Cruise Terminal", "影岛邮轮码头", "影島クルーズターミナル"),
    "N04": ("BIFF Square Seed Hotteok", "BIFF广场坚果糖饼", "BIFF広場 シアッホットク"),
    "N05": ("Bupyeong Kkangtong Market", "富平罐头市场", "富平カントン市場"),
    "N06": ("Gukje Market Food Alley", "国际市场美食街", "国際市場 グルメ通り"),
    "N10": ("Huinnyeoul Culture Village", "白浅滩文化村", "ヒンヨウル文化マウル"),
    "N11": ("Bongnae-dong Warehouse Cafés", "凤莱洞仓库咖啡街", "蓬莱洞 倉庫カフェ"),
    "N15": ("Haeundae Market", "海云台市场", "海雲台市場"),
    # 볼거리(v4)
    "A01": ("Busan North Port Waterfront Park", "北港亲水公园", "北港親水公園"),
    "A02": ("Yongdusan Park · Busan Tower", "龙头山公园·釜山塔", "龍頭山公園・釜山タワー"),
    "A03": ("Gamcheon Culture Village", "甘川洞文化村", "甘川文化村"),
    "A04": ("40 Steps Culture Street", "40阶梯文化观光街", "40階段文化観光通り"),
    "A05": ("Bosu-dong Book Street", "宝水洞旧书街", "宝水洞古本屋通り"),
    "A06": ("Choryang Ibagu-gil (168 Steps)", "草梁故事路(168阶梯)", "草梁イバグキル(168階段)"),
    "A07": ("Haeundae Beach", "海云台海水浴场", "海雲台海水浴場"),
    "A08": ("Gwangalli Beach", "广安里海水浴场", "広安里海水浴場"),
    "A09": ("Taejongdae", "太宗台", "太宗台"),
    "A10": ("Songdo Marine Cable Car", "松岛海上缆车", "松島海上ケーブルカー"),
}
ZH = {"N01": "伽耶小麦冷面", "N02": "60年传统奶奶汤饭", "N03": "新发园(唐人街饺子)", "N07": "盛一家(札嘎其烤鳗鱼)", "N08": "元祖18号馄饨",
      "N09": "三进鱼糕总店", "N12": "东莱奶奶葱饼", "N13": "Hytte咖啡田浦店", "N14": "松亭三代汤饭", "N16": "海云台牛排骨",
      "N17": "88猪排骨", "N18": "P.Ark咖啡烘焙", "N19": "巨人炸鸡"}
CAT = {"밀면": ("Cold wheat noodles", "小麦冷面", "ミルミョン"), "국밥": ("Pork rice soup", "猪肉汤饭", "テジクッパ"), "만두": ("Dumplings", "饺子", "餃子"),
       "디저트": ("Street dessert", "街头甜点", "屋台スイーツ"), "시장": ("Market food", "市场小吃", "市場グルメ"), "해산물": ("Seafood", "海鲜", "海鮮"),
       "면": ("Noodles · wonton", "面·馄饨", "麺・ワンタン"), "어묵": ("Fish cake", "鱼糕", "おでん"), "카페": ("Café", "咖啡", "カフェ"),
       "고기": ("Korean BBQ", "韩式烤肉", "焼肉"), "치킨": ("Fried chicken", "炸鸡", "フライドチキン"), "터미널": ("Terminal", "码头", "ターミナル"),
       "볼거리": ("Sightseeing (no food)", "观光(不吃)", "観光(食事なし)")}
hm = lambda m: "" if pd.isna(m) else f"{int(m) // 60:02d}:{int(m) % 60:02d}"


def clean(t):
    t = re.sub(r"\s*\([^)]*[가-힣][^)]*\)", "", str(t))   # 영·일 이름 뒤 괄호 안 한글 제거
    t = re.sub(r"（[^）]*[가-힣][^）]*）", "", t)
    return t.strip()


nodes = pd.read_csv(D / "food_nodes_1118_B.csv")
api = {l: pd.read_csv(API / f"busan_food_{l}.csv").drop_duplicates("UC_SEQ").set_index("UC_SEQ") for l in ("kr", "en", "ja")}
places = []
for r in nodes.itertuples():
    seq = re.search(r"UC_SEQ=(\d+)", str(r.hours_source))
    seq = int(seq.group(1)) if seq else None
    name = {"ko": re.sub(r"\(.*\)", "", r.name_ko).strip()}
    menu = {}
    if seq and seq in api["en"].index:
        name["en"] = clean(api["en"].at[seq, "TITLE"])
        menu["en"] = str(api["en"].at[seq, "RPRSNTV_MENU"]).replace("\n", " · ") if pd.notna(api["en"].at[seq, "RPRSNTV_MENU"]) else ""
    if seq and seq in api["ja"].index:
        name["ja"] = clean(api["ja"].at[seq, "TITLE"])
        menu["ja"] = str(api["ja"].at[seq, "RPRSNTV_MENU"]).replace("\n", " · ") if pd.notna(api["ja"].at[seq, "RPRSNTV_MENU"]) else ""
    if seq and seq in api["kr"].index and pd.notna(api["kr"].at[seq, "RPRSNTV_MENU"]):
        menu["ko"] = str(api["kr"].at[seq, "RPRSNTV_MENU"]).replace("\n", " · ")
    if r.node_id in MANUAL:
        en, zh, ja = MANUAL[r.node_id]
        name.setdefault("en", en); name["zh"] = zh; name.setdefault("ja", ja)
    name.setdefault("zh", ZH.get(r.node_id, name.get("en", name["ko"])))
    name.setdefault("en", r.name_en); name.setdefault("ja", name["en"])
    sub = re.search(r"\((.*)\)", r.name_ko)
    menu.setdefault("ko", sub.group(1) if sub else r.category)
    cen, czh, cja = CAT.get(r.category, (r.category,) * 3)
    menu.setdefault("en", cen); menu.setdefault("ja", cja); menu["zh"] = czh
    brk = f" (브레이크 {hm(r.break_start)}–{hm(r.break_end)})" if pd.notna(r.break_start) else ""
    places.append({"id": r.node_id, "gu": r.gu, "cat": r.category, "lat": r.lat, "lon": r.lon, "price": int(r.price_krw),
                   "hours": f"{hm(r.open_min)}–{hm(r.close_min)}{brk}" if r.category != "터미널" else "",
                   "real": str(r.data_source).startswith("부산시"), "name": name, "menu": menu})

# 루트 + 구간 이동수단
travel = pd.read_csv(D / "travel_time_1118_B.csv")
travel["eff"] = travel["minutes"] + (travel["mode"] == "taxi") * 5
best = travel.sort_values("eff").drop_duplicates(["from_id", "to_id"]).set_index(["from_id", "to_id"])
routes = json.loads((OUT / "routes.json").read_text(encoding="utf-8")) if (OUT / "routes.json").exists() else []
for c in routes:
    for s in c["stops"]:
        b = best.loc[(s["from"], s["node"])]
        s["mode"], s["move"] = ("walk" if b["mode"] == "walk" else "taxi"), round(b["eff"])
    if c["stops"]:
        b = best.loc[(c["stops"][-1]["node"], c["depot"])]
        c["back_mode"], c["back_move"] = ("walk" if b["mode"] == "walk" else "taxi"), round(b["eff"])

# 상인 예보(예시): 2척 동시 기항일 가게별·시간대별 예상 인원
fc = pd.read_csv(D / "골목방문시나리오_20260508_B.csv", index_col=0)
name2id = {re.sub(r"\(.*\)", "", r.name_ko).strip(): r.node_id for r in nodes.itertuples()}
name2id.update({r.name_ko: r.node_id for r in nodes.itertuples()})
forecast = {name2id[k]: {h: int(v) for h, v in row.items() if v} for k, row in fc.iterrows() if k in name2id}


# 배경 지도(OSM 타일 이어 붙이기)
def tile(z, x, y):
    f = TILES / f"{z}_{x}_{y}.png"
    for _ in range(6):
        if f.exists():
            break
        try:
            req = urllib.request.Request(f"https://tile.openstreetmap.org/{z}/{x}/{y}.png", headers={"User-Agent": "busan-cruise-route-study/1.0"})
            f.write_bytes(urllib.request.urlopen(req, timeout=20).read())
        except OSError:
            continue
    return Image.open(f).convert("RGB")


merc = lambda lon, lat: (math.radians(lon) * 6378137, math.log(math.tan(math.pi / 4 + math.radians(lat) / 2)) * 6378137)


def basemap(name, lon0, lat0, lon1, lat1, z):
    n = 2 ** z
    fx = lambda lon: (lon + 180) / 360 * n
    fy = lambda lat: (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n
    x0, x1, y0, y1 = int(fx(lon0)), int(fx(lon1)), int(fy(lat1)), int(fy(lat0))
    img = Image.new("RGB", ((x1 - x0 + 1) * 256, (y1 - y0 + 1) * 256))
    for x in range(x0, x1 + 1):
        for y in range(y0, y1 + 1):
            img.paste(tile(z, x, y), ((x - x0) * 256, (y - y0) * 256))
    box = [round((fx(lon0) - x0) * 256), round((fy(lat1) - y0) * 256), round((fx(lon1) - x0) * 256), round((fy(lat0) - y0) * 256)]
    img.crop(box).save(OUT / f"map_{name}.jpg", quality=82)
    (l, b), (r_, t) = merc(lon0, lat0), merc(lon1, lat1)
    return {"img": f"map_{name}.jpg", "x0": l, "x1": r_, "y0": b, "y1": t, "w": box[2] - box[0], "h": box[3] - box[1]}


maps = {"wide": basemap("wide", 129.005, 35.07, 129.185, 35.215, 13),
        "core": basemap("core", 129.012, 35.078, 129.092, 35.127, 15)}

data = json.dumps({"places": places, "routes": routes, "forecast": forecast, "maps": maps,
                   "credit": "© OpenStreetMap contributors"}, ensure_ascii=False)
(OUT / "data.js").write_text("window.BBP_DATA=" + data + ";\n", encoding="utf-8")   # file://로 열어도 되도록 스크립트로
(OUT / "data.json").unlink(missing_ok=True)
print(len(places), "places,", len(routes), "routes,", len(forecast), "forecast stores")
