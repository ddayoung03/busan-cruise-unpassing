"""크루즈 미식 루트 최적화 (OPTW: 시간창 오리엔티어링 문제)

Colab 기본 라이브러리(pandas, numpy)만 사용. 파일을 Colab에 올린 뒤 import 해서 쓴다.

[입력 — 어디서 오는가]
| 값                       | 파일·출처                                     | 성격          |
|--------------------------|-----------------------------------------------|---------------|
| 노드 좌표                 | food_nodes_1118_B.csv (OSM Nominatim)          | 외부 지오코딩 |
| 노드 간 택시 시간         | travel_time_1118_B.csv (OSRM, 교통 무시)       | 외부 경로계산 |
| 노드 간 도보 시간         | travel_time_1118_B.csv (거리×1.3÷4.5km/h)      | 모형 추정     |
| 영업시간                  | food_nodes (6곳 웹 출처, 10곳 추정)            | 일부 추정     |
| 피크 대기·가격·체류·점수  | food_nodes (팀 추정)                           | 가정          |
| 국적 가중치               | NAT_WEIGHTS (부산관광공사 대만 설문)           | 근거 1건      |
| 크루즈 혼잡 가중 1.6      | CRUISE_WEIGHT (가정, 기항일 실측으로 보정 예정) | 가정          |

[모델]
목적: max  Σ 만족도_i − λ·(이동 + 오픈·식사창·소화 대기 + 줄 대기)   (λ = 0.8 점/분)
      만족도_i = demand_score_i(외국인 댓글 수요점수) × 국적 가중치(노드의 대표 메뉴)
제약: 터미널 출발 / 승선 마감 30분 전 복귀 / 영업시간 / 도착 시각별 줄 대기 /
      위 용량(포만도 ≤ 4, 100분에 1단위 소화, 체류 중에도 소화) / 식사 간 120분 / 식사 시간창
대기 결정: 각 노드에서 '가능해지는 가장 이른 시각'과, 그 뒤 90분 안의 혼잡 구간 경계(줄이 줄어드는 시각)까지
           기다리는 선택지를 모두 탐색한다(시간 이산화 정책 안에서의 정확해).
해법: 분기한정 깊이우선탐색. 상한 = 남은 노드의 (만족도 − λ·최소 유입 이동시간) 상위 합.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

LAMBDA = 0.8
STOMACH_CAP = 4.0
DIGEST_MIN = 100.0
MEAL_GAP = 120.0
MEAL_WINDOWS = [(11 * 60, 14 * 60 + 30), (17 * 60, 20 * 60 + 30)]
CONGESTION_EDGES = [10.5 * 60, 11.5 * 60, 13.5 * 60, 14.5 * 60, 17.5 * 60, 19.5 * 60]
CRUISE_WEIGHT = 1.6
CRUISE_RADIUS_KM = 3.0                 # 크루즈 혼잡 가중이 걸리는 터미널 반경
CORE_GU = {"중구", "동구", "영도구"}    # 원도심 3구. 이 밖 = '원도심 밖'(확산 대상). 확산 지표는 모두 이 정의
RETURN_BUFFER = 30.0
MAX_STOPS = 7
TAXI_OVERHEAD = 5.0                    # 택시 호출·승하차 (가정)
CROWD_WINDOW = 30.0                    # 분산 배정: 같은 노드 방문 시작이 30분 안에 겹치면 혼잡

# 국적 가중치는 '대표 메뉴 키워드'가 노드 이름에 있을 때만 적용, 나머지 1.0.
# tw: 부산관광공사 대만 관광객 설문(15,796명, 복수응답) 먹고 싶은 음식 응답률
#     돼지국밥 66.9%, 어묵 37.4%, 씨앗호떡 22.4%, 장어구이 19.4% → w = 0.85 + 0.5 × 응답률 / 66.9
#     (변환식은 팀 설계. 크루즈 승객 효용을 직접 측정한 값이 아님 → S6은 '선호 가중 예시')
_TW = {"국밥": 66.9, "어묵": 37.4, "호떡": 22.4, "장어": 19.4}
# 만족도 기본점수 열: demand_score = 외국인 YouTube 댓글 범주 언급 수 기반 수요점수(없으면 busan_score)
SCORE_COL = "demand_score"
NAT_WEIGHTS = {
    "default": {},
    "tw": {k: round(0.85 + 0.5 * v / max(_TW.values()), 3) for k, v in _TW.items()},
}


def congestion(t_min: float) -> float:
    """시간대 혼잡계수 (가정 → 현장 실측으로 보정)."""
    h = t_min / 60.0
    if 11.5 <= h < 13.5:
        return 1.0
    if 17.5 <= h < 19.5:
        return 0.9
    if 10.5 <= h < 11.5 or 13.5 <= h < 14.5:
        return 0.55
    if 14.5 <= h < 17.5:
        return 0.35
    return 0.2


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp, dl = p2 - p1, math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def fmt(m: float) -> str:
    m = int(round(m))
    return f"{m // 60:02d}:{m % 60:02d}"


@dataclass
class Scenario:
    name: str
    depot: str
    start: float
    all_aboard: float
    cruise_day: bool = True
    nationality: str = "default"
    must_far: bool = False                       # 원도심 밖 노드 1곳 이상 포함
    crowd: dict = field(default_factory=dict)    # 분산 배정: 노드별 다른 그룹의 (줄 서기 시각, 그룹 크기/100명)
    crowd_add: float = 8.0                       # 30분 안에 겹치는 100명당 추가 대기(분, 가정)

    def deadline(self):
        return self.all_aboard - RETURN_BUFFER


class Problem:
    def __init__(self, nodes: pd.DataFrame, travel: pd.DataFrame | None = None):
        self.nodes = nodes.set_index("node_id", drop=False)
        self.ids = list(self.nodes.index)
        cols = ["lat", "lon", "open_min", "close_min", "meal_flag", "stomach",
                "stay_min", "price_krw", "wait_peak_min"]
        self.A = {n: {c: float(self.nodes.at[n, c]) for c in cols}
                  | {k: str(self.nodes.at[n, k]) for k in ["category", "name_ko", "gu"]}
                  | {k: float(self.nodes.at[n, k]) if k in self.nodes else float("nan")
                     for k in ["break_start", "break_end"]}
                  | {"score": float(self.nodes.at[n, SCORE_COL if SCORE_COL in self.nodes else "busan_score"])}
                  for n in self.ids}
        self._d = {(a, b): haversine_km(self.A[a]["lat"], self.A[a]["lon"], self.A[b]["lat"], self.A[b]["lon"])
                   for a in self.ids for b in self.ids}
        self.T = self._travel_matrix(travel)
        self.cands = [n for n in self.ids if not self.A[n]["category"].startswith("터미널")]

    def _travel_matrix(self, travel):
        """노드 쌍별 최소 이동시간(분). 택시는 호출·승하차 5분 추가. CSV가 없으면 직선거리 모형."""
        T = {}
        for a in self.ids:
            for b in self.ids:
                if a != b:
                    km = self._d[a, b]
                    walk = km * 1.3 / 4.5 * 60
                    ride = TAXI_OVERHEAD + 8 + km * 1.35 / 22 * 60
                    T[a, b] = walk if km <= 1.5 else min(walk, ride)
        if travel is not None and len(travel):
            tr = travel.copy()
            tr["eff"] = tr["minutes"] + np.where(tr["mode"].astype(str).str.contains("taxi"), TAXI_OVERHEAD, 0.0)
            for (a, b), m in tr.groupby(["from_id", "to_id"])["eff"].min().items():
                if (a, b) in T:
                    T[a, b] = float(m)
        return T

    def dist_from(self, depot, nid):
        return self._d[depot, nid]

    def is_far(self, nid):
        return self.A[nid]["gu"] not in CORE_GU

    def wait(self, nid, t, sc: Scenario, noise=None):
        w = self.A[nid]["wait_peak_min"] * congestion(t)
        if sc.cruise_day and self.dist_from(sc.depot, nid) <= CRUISE_RADIUS_KM:
            w *= CRUISE_WEIGHT
        if noise is not None:
            w *= noise.get(nid, 1.0)
        overlap = sum(wt for b, wt in sc.crowd.get(nid, []) if abs(b - t) < CROWD_WINDOW)
        return w + sc.crowd_add * overlap

    def score(self, nid, sc: Scenario):
        w = 1.0
        for kw, v in NAT_WEIGHTS.get(sc.nationality, {}).items():
            if kw in self.A[nid]["name_ko"]:
                w = v
                break
        return self.A[nid]["score"] * w

    def open_ok(self, n, begin, end):
        """영업시간 안이고, 브레이크타임(break_start~break_end)과 겹치지 않는가."""
        r = self.A[n]
        if begin < r["open_min"] or end > r["close_min"]:
            return False
        bs, be = r.get("break_start"), r.get("break_end")
        return not (bs == bs and be == be and begin < be and end > bs)   # NaN이면 브레이크 없음

    def first_queue_time(self, n, base, target, sc, noise=None):
        """줄 서기 시각 s0 ≥ base 중 s0 + 줄대기(s0) ≥ target 인 가장 이른 시각(1분 단위)."""
        if base + self.wait(n, base, sc, noise) >= target:
            return base
        qmax = self.A[n]["wait_peak_min"] * CRUISE_WEIGHT * 1.5 + sc.crowd_add * sum(wt for v in sc.crowd.values() for _, wt in v)
        s0 = max(base, math.floor(target - qmax))
        while s0 < target:
            if s0 + self.wait(n, s0, sc, noise) >= target:
                return s0
            s0 += 1.0
        return target

    # ---------- 한 노드로 가는 선택지 (DFS·탐욕·평가가 모두 같은 규칙을 쓴다) ----------
    def options(self, cur, t, st, lm, n, sc, noise=None, tnoise=1.0, wait_choice=True, not_before=-1e9):
        """현재 (위치 cur, 시각 t, 포만도 st, 마지막 식사 시작 lm)에서 n을 방문하는 실행가능한 선택지들."""
        r = self.A[n]
        arr = t + self.T[cur, n] * tnoise
        base = max(arr, r["open_min"], not_before)
        # 섭취 시작(begin = 줄 서기 + 줄 대기)이 만족해야 할 하한: 소화·식사 간격·식사창
        need = st - (STOMACH_CAP - r["stomach"])
        lo = t + need * DIGEST_MIN if need > 0 else -1e9
        if r["meal_flag"] == 1 and lm is not None:
            lo = max(lo, lm + MEAL_GAP)
        windows = MEAL_WINDOWS if r["meal_flag"] == 1 else [(-1e9, 1e9)]
        starts = []
        bs_, be = r.get("break_start"), r.get("break_end")
        hit = be == be and be is not None and be > base and base + self.wait(n, base, sc, noise) + r["stay_min"] > bs_
        bases = [base] + ([be] if hit else [])   # 지금 가면 브레이크와 겹칠 때만 재개장 후보 추가
        for a, b in windows:
            target = max(lo, a)
            for bs0 in bases:
                s0 = self.first_queue_time(n, bs0, target, sc, noise)   # begin ≥ target 이 되는 가장 이른 줄 서기
                if s0 is not None and s0 + self.wait(n, s0, sc, noise) <= b:
                    starts.append(s0)
        if wait_choice:
            starts += [e for s0 in list(starts) for e in CONGESTION_EDGES if s0 < e <= s0 + 90]
        out = []
        for s0 in sorted(set(starts)):
            q = self.wait(n, s0, sc, noise)
            begin = s0 + q
            if begin < lo - 1e-9 or not any(a <= begin <= b for a, b in windows):
                continue
            end = begin + r["stay_min"]
            if not self.open_ok(n, begin, end) or end + self.T[n, sc.depot] * tnoise > sc.deadline():
                continue
            st_b = max(0.0, st - (begin - t) / DIGEST_MIN) + r["stomach"]
            if st_b > STOMACH_CAP + 1e-9:
                continue
            st_e = max(0.0, st_b - r["stay_min"] / DIGEST_MIN)   # 체류 중에도 소화
            out.append({"arr": arr, "idle": s0 - arr, "q": q, "begin": begin, "end": end, "st": st_e,
                        "lm": begin if r["meal_flag"] == 1 else lm,
                        "gain": self.score(n, sc) - LAMBDA * (begin - t)})
        return out

    # ---------------- 분기한정 ----------------
    def solve(self, sc: Scenario, k=3, noise=None):
        depot, cands = sc.depot, self.cands
        scores = {n: self.score(n, sc) for n in cands}
        opt = {n: scores[n] - LAMBDA * min(self.T[m, n] for m in self.ids if m != n) for n in cands}
        min_step = min(self.A[n]["stay_min"] for n in cands) + min(self.T.values())
        best: list = []

        def record(obj, route, tl):
            if sc.must_far and not any(self.is_far(n) for n in route):
                return
            key = frozenset(route)
            for i, (o, r, _) in enumerate(best):
                if frozenset(r) == key:
                    if obj > o:
                        best[i] = (obj, list(route), list(tl))
                        best.sort(key=lambda x: -x[0])
                    return
            best.append((obj, list(route), list(tl)))
            best.sort(key=lambda x: -x[0])
            del best[k:]

        def kth():
            return best[-1][0] if len(best) >= k else -1e18

        def dfs(cur, t, st, lm, route, obj, tl):
            if route:
                record(obj - LAMBDA * self.T[cur, depot], route, tl)
            if len(route) >= MAX_STOPS:
                return
            slots = min(MAX_STOPS - len(route), int((sc.deadline() - t) // max(1.0, min_step)))
            rest = sorted((opt[n] for n in cands if n not in route and opt[n] > 0), reverse=True)
            if obj + sum(rest[:slots]) <= kth():
                return
            for n in cands:
                if n in route:
                    continue
                for o in self.options(cur, t, st, lm, n, sc, noise):
                    dfs(n, o["end"], o["st"], o["lm"], route + [n], obj + o["gain"],
                        tl + [(n, o["arr"], o["idle"], o["q"], o["begin"], o["end"])])

        dfs(depot, sc.start, 0.0, None, [], 0.0, [])
        return [self.describe(o, r, tl, sc) for o, r, tl in best]

    def describe(self, obj, route, tl, sc):
        last = tl[-1][5]
        return {
            "scenario": sc.name, "objective": round(obj, 1), "route": route,
            "names": [self.A[n]["name_ko"] for n in route],
            "return_min": last + self.T[route[-1], sc.depot],
            "queue_min": round(sum(x[3] for x in tl), 1),
            "idle_min": round(sum(x[2] for x in tl), 1),
            "travel_min": round(sum(self.T[a, b] for a, b in zip([sc.depot] + route, route + [sc.depot])), 1),
            "satisfaction": round(sum(self.score(n, sc) for n in route), 1),
            "spend_krw": int(sum(self.A[n]["price_krw"] for n in route)),
            "far_nodes": [n for n in route if self.is_far(n)],
            "timeline": tl,
        }

    # ---------------- 기준선 ----------------
    def greedy(self, sc: Scenario):
        """같은 제약·같은 목적함수의 근시안적 탐욕법(수업 recommend_course_under_budget 방식에 제약 추가).
        매 단계 '이득 ÷ 소요시간'이 가장 큰 실행가능 노드를 고르고 되돌아보지 않는다."""
        cur, t, st, lm, route, tl, obj = sc.depot, sc.start, 0.0, None, [], [], 0.0
        while len(route) < MAX_STOPS:
            pick = None
            for n in self.cands:
                if n in route:
                    continue
                for o in self.options(cur, t, st, lm, n, sc):
                    eff = o["gain"] / max(1.0, o["end"] - t)
                    if o["gain"] > 0 and (pick is None or eff > pick[0]):
                        pick = (eff, n, o)
            if pick is None:
                break
            _, n, o = pick
            route.append(n); obj += o["gain"]
            tl.append((n, o["arr"], o["idle"], o["q"], o["begin"], o["end"]))
            cur, t, st, lm = n, o["end"], o["st"], o["lm"]
        if not route:
            return None
        out = self.describe(obj - LAMBDA * self.T[cur, sc.depot], route, tl, sc)
        out["meets_must_far"] = not sc.must_far or bool(out["far_nodes"])   # 근시안 탐색은 필수 조건을 놓칠 수 있다
        return out

    def naive_plan(self, sc: Scenario):
        """제약 무시 계획: 대기·위 용량·식사 규칙을 보지 않고 이동+체류만으로 일정을 채운 계획(위험 사례)."""
        route, t, cur = [], sc.start, sc.depot
        while True:
            best, be = None, 0
            for n in self.cands:
                if n in route:
                    continue
                r, tt = self.A[n], self.T[cur, n]
                if t + tt + r["stay_min"] + self.T[n, sc.depot] > sc.deadline():
                    continue
                eff = (self.score(n, sc) - LAMBDA * tt) / max(1.0, r["stay_min"] + tt)
                if eff > be:
                    best, be = n, eff
            if best is None:
                break
            t += self.T[cur, best] + self.A[best]["stay_min"]
            route.append(best); cur = best
        return route

    # ---------------- 평가 ----------------
    def evaluate(self, route, sc: Scenario, noise=None, tnoise=1.0, plan=None):
        """고정된 순서를 실제로 걸었을 때. 최적화와 같은 규칙(options)으로 '가장 이른 가능한 줄 서기'를 고른다.
        plan(최적화 시간표)이 있으면 계획한 줄 서기 시각보다 먼저 서지 않는다. 규칙을 지킬 수 없는 방문은
        도착 즉시 줄 선다고 보고 어떤 규칙이 깨졌는지 센다."""
        t, cur, st, lm, obj, queue = sc.start, sc.depot, 0.0, None, 0.0, 0.0
        viol = {"영업·브레이크": 0, "위 용량": 0, "식사 간격·시간창": 0, "복귀 지각": 0,
                "방문 수 초과": 0, "원도심 밖 필수": 0}
        visits = []
        for i, n in enumerate(route):
            r = self.A[n]
            nb = plan[i][4] - plan[i][3] if plan else -1e9
            opts = self.options(cur, t, st, lm, n, sc, noise, tnoise, wait_choice=False, not_before=nb)
            if opts:
                o = opts[0]
                q, begin, end, st_n, lm_n = o["q"], o["begin"], o["end"], o["st"], o["lm"]
                s0 = begin - q
            else:  # 규칙을 지킬 수 없음 → 도착 즉시 줄 선다고 보고 위반 진단
                arr = t + self.T[cur, n] * tnoise
                s0 = max(arr, r["open_min"], nb)
                q = self.wait(n, s0, sc, noise)
                begin, end = s0 + q, s0 + q + r["stay_min"]
                st_b = max(0.0, st - (begin - t) / DIGEST_MIN) + r["stomach"]
                viol["영업·브레이크"] += not self.open_ok(n, begin, end)
                viol["위 용량"] += st_b > STOMACH_CAP + 1e-9
                if r["meal_flag"] == 1:
                    viol["식사 간격·시간창"] += bool((lm is not None and begin - lm < MEAL_GAP)
                                                 or not any(a <= begin <= b for a, b in MEAL_WINDOWS))
                st_n = max(0.0, st_b - r["stay_min"] / DIGEST_MIN)
                lm_n = begin if r["meal_flag"] == 1 else lm
            obj += self.score(n, sc) - LAMBDA * (begin - t)
            queue += q
            visits.append((n, s0))
            t, cur, st, lm = end, n, st_n, lm_n
        back = t + self.T[cur, sc.depot] * tnoise
        viol["복귀 지각"] = int(back > sc.deadline() + 1e-9)
        viol["방문 수 초과"] = int(len(route) > MAX_STOPS)
        viol["원도심 밖 필수"] = int(sc.must_far and not any(self.is_far(n) for n in route))
        return {"route": route, "names": [self.A[n]["name_ko"] for n in route],
                "objective": round(obj - LAMBDA * (back - t), 1), "queue_min": round(queue, 1),
                "return_min": back, "slack_min": sc.deadline() - back,
                "violations": viol, "feasible": sum(viol.values()) == 0, "visits": visits}

    # ---------------- 검증 ----------------
    def sensitivity(self, sc: Scenario, runs=200, pct=0.3, seed=0):
        """최적 방문집합 민감도: 대기 ±30%를 알고 다시 풀었을 때 같은 방문 장소 집합이 뽑히는 비율."""
        base = self.solve(sc, k=1)[0]
        key = frozenset(base["route"])
        rng = np.random.default_rng(seed)
        keep, freq = 0, {}
        for _ in range(runs):
            noise = {n: rng.uniform(1 - pct, 1 + pct) for n in self.ids}
            r = self.solve(sc, k=1, noise=noise)[0]
            keep += frozenset(r["route"]) == key
            for n in r["route"]:
                freq[n] = freq.get(n, 0) + 1
        return {"keep_rate": keep / runs, "base": base, "node_freq": {n: c / runs for n, c in freq.items()}}

    def fixed_route_risk(self, sc: Scenario, base, runs=1000, wpct=0.3, tpct=0.2, seed=1):
        """배포한 루트·시간표 고정(계획보다 일찍 줄 서지 않음) + 대기 ±30%·이동 ±20% 오차.
        전체 규칙 준수율, 규칙별 위반율, 복귀 여유."""
        rng = np.random.default_rng(seed)
        slack, ok, vc = [], 0, {}
        for _ in range(runs):
            noise = {n: rng.uniform(1 - wpct, 1 + wpct) for n in self.ids}
            ev = self.evaluate(base["route"], sc, noise, rng.uniform(1 - tpct, 1 + tpct), plan=base["timeline"])
            slack.append(ev["slack_min"])
            ok += ev["feasible"]
            for k, v in ev["violations"].items():
                vc[k] = vc.get(k, 0) + (v > 0)
        slack = np.array(slack)
        return {"feasible_rate": ok / runs, "late_prob": vc.get("복귀 지각", 0) / runs,
                "viol_rates": {k: v / runs for k, v in vc.items()},
                "slack_p5": float(np.percentile(slack, 5)), "slack_median": float(np.median(slack))}

    def dispersion(self, sc: Scenario, groups=6, stagger=10.0, crowd_add=8.0, size=100.0):
        """분산 배정: 그룹 g는 하선 순서대로 stagger분씩 늦게 출발하고, 앞 그룹과 30분 안에 같은 곳에 줄 서면
        100명당 +crowd_add분. 배정 뒤에는 plans를 돌려준다(평가는 joint_eval)."""
        crowd, plans = {}, []
        for g in range(groups):
            s = Scenario(**{**sc.__dict__, "start": sc.start + stagger * g, "crowd": crowd, "crowd_add": crowd_add})
            r = (self.solve(s, k=1) or [{"route": [], "timeline": []}])[0]   # 해 없음 = 방문 없음
            plans.append((Scenario(**{**s.__dict__, "crowd": {}}), r["route"], r["timeline"], size))
            crowd = {k: list(v) for k, v in crowd.items()}
            for n, a, i, q, begin, end in r["timeline"]:
                crowd.setdefault(n, []).append((begin - q, size / 100.0))
        # 순차 배정은 앞 그룹이 뒤 그룹 혼잡을 모른다 → 공동 평가에서 위반한 그룹만 '나머지 전원' 혼잡으로 재최적화
        for _ in range(3):
            evs = self.joint_eval(plans)
            bad = [i for i, e in enumerate(evs) if not e["feasible"]]
            if not bad:
                break
            for i in bad:
                others = {}
                for j, e in enumerate(evs):
                    if j != i:
                        for n, s0 in e["visits"]:
                            others.setdefault(n, []).append((s0, plans[j][3] / 100.0))
                s = plans[i][0]
                r = (self.solve(Scenario(**{**s.__dict__, "crowd": others}), k=1) or [{"route": [], "timeline": []}])[0]
                plans[i] = (s, r["route"], r["timeline"], plans[i][3])
        return plans

    def same_route_plans(self, sc: Scenario, route, groups=6, stagger=10.0, crowd_add=8.0, size=100.0):
        """대조: 모든 그룹이 같은 최적 루트를 따른다."""
        return [(Scenario(**{**sc.__dict__, "start": sc.start + stagger * g, "crowd_add": crowd_add}), route, None, size)
                for g in range(groups)]

    def joint_eval(self, plans, iters=20):
        """여러 그룹(다른 배 포함)을 같은 규칙으로 공동 평가. 각 그룹의 혼잡 = 다른 모든 그룹의 줄 서기 시각.
        줄 서기 시각이 0.5분 이상 바뀌지 않을 때까지 반복(최대 20회)하고 수렴 여부를 함께 돌려준다."""
        evs = [self.evaluate(route, s, plan=tl) for s, route, tl, size in plans]
        converged = False
        for _ in range(iters):
            new = []
            for i, (s, route, tl, size) in enumerate(plans):
                crowd = {}
                for j, ev in enumerate(evs):
                    if j != i:
                        for n, s0 in ev["visits"]:
                            crowd.setdefault(n, []).append((s0, plans[j][3] / 100.0))
                new.append(self.evaluate(route, Scenario(**{**s.__dict__, "crowd": crowd}), plan=tl))
            diff = max([abs(a[1] - b[1]) for e0, e1 in zip(evs, new) for a, b in zip(e0["visits"], e1["visits"])] or [0])
            evs = new
            if diff < 0.5:
                converged = True
                break
        for e in evs:
            e["converged"] = converged
        return evs
