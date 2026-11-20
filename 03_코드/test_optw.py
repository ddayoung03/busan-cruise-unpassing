"""OPTW 규칙 점검 (Codex 1차 검토 반례). 실행: python 03_코드/test_optw.py"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent))
import cruise_route_optw as M  # noqa: E402
from cruise_route_optw import Problem, Scenario

M.PLAN_SAFETY = 0.0   # 규칙 테스트는 안전 여유 없이(여유 테스트는 맨 끝)

BASE = dict(category="시장", lat=35.1, lon=129.04, open_min=0, close_min=1440, meal_flag=0, stomach=0.5,
            stay_min=30, price_krw=10000, wait_peak_min=0, busan_score=80, gu="중구")


def problem(rows, minutes=1.0):
    nodes = pd.DataFrame([{**BASE, "node_id": "D", "name_ko": "터미널", "category": "터미널", "busan_score": 0}]
                         + [{**BASE, **r} for r in rows])
    ids = nodes["node_id"].tolist()
    travel = pd.DataFrame([{"from_id": a, "to_id": b, "mode": "walk", "minutes": minutes}
                           for a in ids for b in ids if a != b])
    return Problem(nodes, travel)


# 반례 1: 10:50 출발이면 11:00 식사창까지 9분 기다려야 식사 가능 → 경로가 나와야 한다
P = problem([{"node_id": "M", "name_ko": "식당", "meal_flag": 1, "stomach": 1.0}])
r = P.solve(Scenario("t", "D", 10 * 60 + 50, 13 * 60 + 30), k=1)
assert r and r[0]["route"] == ["M"], r
assert r[0]["timeline"][0][4] >= 11 * 60, "식사창 시작 전에 식사하면 안 됨"

# 반례 2: 포만도 2.5짜리 두 곳, 체류 100분 → 체류 중 소화하면 둘 다 방문 가능
P = problem([{"node_id": "A", "name_ko": "a", "stomach": 2.5, "stay_min": 100},
             {"node_id": "B", "name_ko": "b", "stomach": 2.5, "stay_min": 100}])
r = P.solve(Scenario("t", "D", 9 * 60, 18 * 60), k=1)
assert sorted(r[0]["route"]) == ["A", "B"], r

# 평가기는 최적화가 만든 루트를 위반 없이 재현해야 한다
ev = P.evaluate(r[0]["route"], Scenario("t", "D", 9 * 60, 18 * 60))
assert ev["feasible"], ev["violations"]

# 식사 간 120분: 두 식당은 붙여 먹을 수 없다
P = problem([{"node_id": "M1", "name_ko": "m1", "meal_flag": 1, "stomach": 1.0},
             {"node_id": "M2", "name_ko": "m2", "meal_flag": 1, "stomach": 1.0}])
r = P.solve(Scenario("t", "D", 11 * 60, 16 * 60), k=1)[0]
if len(r["route"]) == 2:
    b = [x[4] for x in r["timeline"]]
    assert b[1] - b[0] >= 120, b
# 2차 반례 1: 줄 대기 20분이면 10:50에 줄 서서 11:01에 식사 시작 가능 → 11:40 한도 안에 끝나야 한다
P = problem([{"node_id": "M", "name_ko": "식당", "meal_flag": 1, "stomach": 1.0, "wait_peak_min": 20,
              "close_min": 11 * 60 + 40}])
sc = Scenario("t", "D", 10 * 60 + 49, 12 * 60 + 10, cruise_day=False)
r = P.solve(sc, k=1)
assert r and r[0]["route"] == ["M"], r
assert 11 * 60 <= r[0]["timeline"][0][4] < 11 * 60 + 10, r[0]["timeline"]

# 2차 반례 5: 원도심 밖 필수인데 탐욕이 근거리만 고르면 평가기가 위반으로 잡아야 한다
P = problem([{"node_id": "N", "name_ko": "near", "busan_score": 80},
             {"node_id": "F", "name_ko": "far", "busan_score": 0, "gu": "동래구"}])
sc = Scenario("t", "D", 9 * 60, 18 * 60, must_far=True)
assert not P.evaluate(["N"], sc)["feasible"]
assert P.evaluate(["N"], sc)["violations"]["원도심 밖 필수"] == 1

# 브레이크타임: 15~17시 브레이크면 14:30 시작 60분 체류는 불가
P = problem([{"node_id": "B", "name_ko": "b", "stay_min": 60, "break_start": 900, "break_end": 1020}])
assert not P.open_ok("B", 14 * 60 + 30, 15 * 60 + 30) and P.open_ok("B", 13 * 60, 14 * 60)

# 공동 평가: 같은 노드에 두 그룹 → 수렴하고, 반환된 일정이 자기 혼잡 규칙과 맞아야 한다
P = problem([{"node_id": "Q", "name_ko": "q", "wait_peak_min": 0}])
plans = [(Scenario("g1", "D", 600, 900, crowd_add=20.0), ["Q"], None, 100.0),
         (Scenario("g2", "D", 620, 900, crowd_add=20.0), ["Q"], None, 100.0)]
evs = P.joint_eval(plans)
assert evs[0]["converged"]
s1, s2 = evs[0]["visits"][0][1], evs[1]["visits"][0][1]
assert (abs(s1 - s2) < 30) == (evs[0]["queue_min"] > 0), (s1, s2, evs[0]["queue_min"])
# 계획 안전 여유: 여유 20분이면 마감 20분 전까지 돌아오는 루트만 나온다
M.PLAN_SAFETY = 20.0
P = problem([{"node_id": "L", "name_ko": "l", "stay_min": 50}])
assert P.solve(Scenario("t", "D", 600, 600 + 50 + 2 + 30), k=1) == [], "마감 직전 복귀는 계획하면 안 됨"
r = P.solve(Scenario("t", "D", 600, 600 + 50 + 2 + 30 + 20), k=1)
assert r and r[0]["return_min"] <= 600 + 50 + 2 + 20 - 20 + 1e-9 + 20, r
print("OK")
