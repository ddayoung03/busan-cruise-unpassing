"""모델 v4: 볼거리 노드(먹지 않는 곳) 10곳을 노드 표와 이동시간 표에 더한다.

볼거리 = category '볼거리', meal_flag 0, stomach 0(머무는 동안 소화), 줄 대기 0(가정).
| 값        | 출처                                                                          |
|-----------|-------------------------------------------------------------------------------|
| 좌표      | OSM Nominatim (검색어는 coord_source 열)                                        |
| 운영시간  | OSM opening_hours(북항친수공원) / 운영사 안내(부산타워·책방골목 문화관) / 야외 상시 / 미확인은 추정 |
| 수요점수  | 02_정제데이터/명소언급_1119_C.csv (부산 여행 영상 외국인 댓글 언급 수)               |
| 머무는 시간 | 팀 추정 (현장 확인 전)                                                        |
| 이동시간  | OSRM table(택시) + 직선 1.5km 이하 도보(거리×1.3÷4.5km/h) — 기존 travel_time과 같은 규칙 |
흰여울문화마을은 이미 카페 노드(N10)라 넣지 않는다.
실행(프로젝트 루트): python 03_코드/make_attraction_nodes.py   — v3 표는 *_v3백업.csv 로 한 번만 보관
"""
import json
import shutil
import sys
import time
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
D = ROOT / "02_정제데이터"
sys.path.insert(0, str(ROOT / "03_코드"))
from cruise_route_optw import haversine_km  # noqa: E402

NODES, TRAVEL = D / "food_nodes_1118_B.csv", D / "travel_time_1118_B.csv"
for f in (NODES, TRAVEL):
    bak = f.with_name(f.stem + "_v3백업.csv")
    if not bak.exists():
        shutil.copy(f, bak)
nodes = pd.read_csv(NODES.with_name(NODES.stem + "_v3백업.csv"))
travel = pd.read_csv(TRAVEL.with_name(TRAVEL.stem + "_v3백업.csv"))
score = pd.read_csv(D / "명소언급_1119_C.csv").set_index("name_ko")

H = lambda h: int(h * 60)
# id, 이름(명소언급 키), 영문, 구, 위도, 경도, 여는·닫는 시각, 시간 출처, 머무는 분, 요금, OSM 검색어
A = [
    ("A01", "북항 친수공원", "Busan North Port Waterfront Park", "동구", 35.1100862, 129.0458678, H(5), H(24), "OSM opening_hours Mo-Su 05:00-24:00", 30, 0, "북항친수공원"),
    ("A02", "용두산공원·부산타워", "Yongdusan Park & Busan Tower", "중구", 35.1013015, 129.0322296, H(10), H(22), "예매처 안내 10:00-22:00(입장 21:30 마감)", 40, 8500, "부산타워"),
    ("A03", "감천문화마을", "Gamcheon Culture Village", "사하구", 35.0963371, 129.0087897, H(9), H(18), "추정: 야외 마을, 상점·안내소 낮 시간", 60, 0, "감천문화마을"),
    ("A04", "40계단", "40 Steps Culture Street", "중구", 35.1039013, 129.0346592, 0, H(24), "야외 상시", 20, 0, "40계단"),
    ("A05", "보수동 책방골목", "Bosu-dong Book Street", "중구", 35.1033486, 129.0269106, H(10), H(18), "문화관 10:00-18:00(월 휴관), 가게별 상이", 30, 0, "보수동 책방골목"),
    ("A06", "초량 이바구길", "Choryang Ibagu-gil (168 Steps)", "동구", 35.1171674, 129.0351679, 0, H(24), "야외 상시", 30, 0, "168계단"),
    ("A07", "해운대해수욕장", "Haeundae Beach", "해운대구", 35.1592859, 129.1586091, 0, H(24), "야외 상시", 40, 0, "해운대해수욕장"),
    ("A08", "광안리해수욕장", "Gwangalli Beach", "수영구", 35.1508879, 129.1167806, 0, H(24), "야외 상시", 40, 0, "광안리해수욕장"),
    ("A09", "태종대", "Taejongdae", "영도구", 35.05851, 129.0876858, H(9), H(18), "추정: 유원지 낮 시간", 60, 0, "태종대"),
    ("A10", "송도해상케이블카", "Songdo Marine Cable Car", "서구", 35.0689247, 129.0220234, H(9), H(20), "09:00 시작(안내), 마감 미확인→20:00 추정", 50, 19000, "송도해상케이블카"),
]
rows = [{"node_id": i, "name_ko": k, "name_en": e, "gu": g, "category": "볼거리", "lat": la, "lon": lo,
         "open_min": o, "close_min": c, "meal_flag": 0, "stomach": 0.0, "stay_min": st, "price_krw": pr,
         "wait_peak_min": 0, "wait_source": "줄 없음 가정", "hours_source": hs, "coord_source": f"OSM Nominatim: {q}",
         "note": "볼거리(먹지 않음)", "demand_mentions": int(score.at[k, "mentions"]),
         "demand_score": float(score.at[k, "demand_score"]), "data_source": "OSM·여행영상 댓글·팀 추정(머무는 시간)"}
        for i, k, e, g, la, lo, o, c, hs, st, pr, q in A]
nodes = pd.concat([nodes, pd.DataFrame(rows)], ignore_index=True)

# 이동시간: 새 노드가 낀 쌍만 OSRM table 한 번으로
ids, new = list(nodes["node_id"]), {r["node_id"] for r in rows}
coords = ";".join(f"{lo},{la}" for la, lo in zip(nodes["lat"], nodes["lon"]))
req = urllib.request.Request(f"https://router.project-osrm.org/table/v1/driving/{coords}?annotations=duration,distance",
                             headers={"User-Agent": "student-research-script/1.0"})
tab = json.load(urllib.request.urlopen(req, timeout=60))
assert tab.get("code") == "Ok", tab.get("code")
P = nodes.set_index("node_id")
add = []
for i, a in enumerate(ids):
    for j, b in enumerate(ids):
        if a == b or not ({a, b} & new):
            continue
        add.append({"from_id": a, "to_id": b, "mode": "taxi", "minutes": round(tab["durations"][i][j] / 60, 1),
                    "km": round(tab["distances"][i][j] / 1000, 3), "source": "OSRM"})
        km = haversine_km(P.at[a, "lat"], P.at[a, "lon"], P.at[b, "lat"], P.at[b, "lon"])
        if km <= 1.5:
            add.append({"from_id": a, "to_id": b, "mode": "walk", "minutes": round(km * 1.3 / 4.5 * 60, 1),
                        "km": round(km, 3), "source": "모형추정"})
travel = pd.concat([travel, pd.DataFrame(add)], ignore_index=True)

nodes.to_csv(NODES, index=False, encoding="utf-8-sig")
travel.to_csv(TRAVEL, index=False, encoding="utf-8-sig")
print(f"노드 {len(nodes)}곳(볼거리 {len(rows)}), 이동 {len(travel)}행(+{len(add)})")
print(pd.DataFrame(rows)[["node_id", "name_ko", "gu", "demand_mentions", "demand_score", "stay_min"]].to_string(index=False))
