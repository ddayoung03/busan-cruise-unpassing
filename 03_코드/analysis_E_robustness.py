"""E. 교수님 피드백 반영: 인기순 경로 비교 · 스트레스 테스트(20분 지연, 점심 단체 도착) · 방문지를 줄인 예비 경로

1) 인기순 경로: 수요점수가 높은 곳부터 차례로, 규칙(영업·위 용량·식사 간격·복귀 여유)을 지킬 수 있으면 넣는다. 동선은 최적화하지 않는다.
   → 우리 최적 경로와 총 대기시간·방문 점포 수·복귀 여유를 비교.
2) 스트레스: (a) 하선 20분 지연  (b) 점심 단체 도착 = 11:30~13:30에 200명 단체가 모든 식당·시장에 줄 섬(겹침 100명당 +8분, 가정)
   → 승선 마감 30분 전(= deadline)까지 돌아오는지.
3) 예비 경로: 실패하면 장소를 하나씩 빼서(빼면 목적함수가 가장 덜 줄어드는 곳부터) 돌아올 수 있을 때까지 줄인 경로.
4) 서비스 154칸: 하선 20분 지연 시 예비 경로(B안)를 06_서비스/plan_b.json 으로.
산출: 02_정제데이터/인기순비교_1120_E.csv, 스트레스테스트_1120_E.csv, 04_그림/그림15_스트레스테스트.png
실행(프로젝트 루트): python 03_코드/analysis_E_robustness.py   (시나리오 6개를 병렬로 다시 풀어 약 5분)
"""
import json
import multiprocessing as mp
import platform
import sys
from pathlib import Path

import matplotlib
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_코드"))
D, F = ROOT / "02_정제데이터", ROOT / "04_그림"
DELAY, LUNCH, LUNCH_GROUP = 20.0, (11 * 60 + 30, 13 * 60 + 30), 200.0


def setup():
    src = (ROOT / "03_코드/run_B_model.py").read_text(encoding="utf-8")
    ns = {"__file__": str(ROOT / "03_코드/run_B_model.py")}
    exec(src[:src.index("# 1) 시나리오별")], ns)   # 문제·시나리오 정의만
    return ns["P"], ns["SCEN"]


P, SCEN = setup()
from cruise_route_optw import PLAN_SAFETY, Scenario, fmt  # noqa: E402


def popular(sc):
    """인기순: 수요점수 높은 순서대로 넣을 수 있으면 넣는다(가장 이른 가능한 시각)."""
    cur, t, st, lm, route = sc.depot, sc.start, 0.0, None, []
    for n in sorted(P.cands, key=lambda n: -P.score(n, sc)):
        if not P.can_add(route, n):
            continue
        o = P.options(cur, t, st, lm, n, sc, wait_choice=False, slack=PLAN_SAFETY)
        if o:
            o = o[0]
            route.append(n)
            cur, t, st, lm = n, o["end"], o["st"], o["lm"]
    return route


def lunch_crowd(sc, route):
    return {n: [(float(m), LUNCH_GROUP / 100.0) for m in range(LUNCH[0], LUNCH[1] + 1, 30)]
            for n in route if P.A[n]["wait_peak_min"] > 0}


def stressed(sc, kind, route):
    if kind == "기본":
        return sc
    if kind == "하선 20분 지연":
        return Scenario(**{**sc.__dict__, "start": sc.start + DELAY})
    return Scenario(**{**sc.__dict__, "crowd": lunch_crowd(sc, route)})


def metrics(route, sc, plan=None):
    ev = P.evaluate(route, sc, plan=plan)
    idle = sum(s["queue_start"] - s["leave"] - P.T[s["from"], s["node"]] for s in ev["stops"])
    return ev, {"방문 점포 수": len(route), "총 대기(분)": round(ev["queue_min"] + idle, 1), "줄 대기(분)": round(ev["queue_min"], 1),
                "기다림(분)": round(idle, 1),
                "복귀": fmt(ev["return_min"]), "복귀 여유(분)": round(ev["slack_min"], 1),
                "규칙 준수": ev["feasible"], "목적함수": ev["objective"]}


def backup(route, sc):
    """예비 경로: 규칙을 지킬 때까지 장소를 하나씩 뺀다(목적함수가 가장 큰 쪽을 남김)."""
    r = list(route)
    while r and not P.evaluate(r, sc)["feasible"]:
        r = max(([*r[:i], *r[i + 1:]] for i in range(len(r))), key=lambda x: P.evaluate(x, sc)["objective"] if x else -1e9)
    return r


def solve_one(i):
    sc = SCEN[i]
    best = P.solve(sc, k=1)[0]
    return sc.name, best["route"], [list(x) for x in best["timeline"]]


def svc_plan_b():
    """서비스 154칸: 하선 20분 지연 시 B안(뺄 장소)."""
    cells = json.loads((ROOT / "06_서비스/routes.json").read_text(encoding="utf-8"))
    out = []
    for c in cells:
        route = [s["node"] for s in c["stops"]]
        if not route:
            continue
        sc = Scenario("svc", c["depot"], c["start"] + DELAY, c["start"] + c["hours"] * 60 + 30)
        if P.evaluate(route, sc)["feasible"]:
            out.append({"depot": c["depot"], "start": c["start"], "hours": c["hours"], "drop": []})
            continue
        b = backup(route, sc)
        out.append({"depot": c["depot"], "start": c["start"], "hours": c["hours"], "drop": [n for n in route if n not in b],
                    "return": round(P.evaluate(b, sc)["return_min"]) if b else None})
    return out


if __name__ == "__main__":
    with mp.Pool(len(SCEN)) as pool:
        sols = pool.map(solve_one, range(len(SCEN)))
    comp, stress = [], []
    for (name, route, tl), sc in zip(sols, SCEN):
        pop = popular(sc)
        for label, r, pl in [("최적 경로", route, tl), ("인기순 경로", pop, None)]:
            _, m = metrics(r, sc, pl)
            comp.append({"시나리오": name, "경로": label, **m, "루트": " → ".join(P.A[n]["name_ko"].split("(")[0] for n in r)})
            for kind in ["기본", "하선 20분 지연", "점심 단체 도착"]:
                s2 = stressed(sc, kind, r)
                ev, m2 = metrics(r, s2, pl if kind != "하선 20분 지연" else None)
                row = {"시나리오": name, "경로": label, "상황": kind, "복귀": m2["복귀"], "복귀 여유(분)": m2["복귀 여유(분)"],
                       "규칙 준수": m2["규칙 준수"], "예비 경로": "", "예비 경로 복귀": ""}
                if not ev["feasible"]:
                    b = backup(r, s2)
                    row["예비 경로"] = "빼기: " + ", ".join(P.A[n]["name_ko"].split("(")[0] for n in r if n not in b) if b else "방문 없음"
                    row["예비 경로 복귀"] = fmt(P.evaluate(b, s2)["return_min"]) if b else ""
                stress.append(row)
    comp, stress = pd.DataFrame(comp), pd.DataFrame(stress)
    comp.to_csv(D / "인기순비교_1120_E.csv", index=False, encoding="utf-8-sig")
    stress.to_csv(D / "스트레스테스트_1120_E.csv", index=False, encoding="utf-8-sig")
    pb = svc_plan_b()
    (ROOT / "06_서비스/plan_b.json").write_text(json.dumps(pb, ensure_ascii=False), encoding="utf-8")

    plt.rcParams["font.family"] = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"
    plt.rcParams["axes.unicode_minus"] = False
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.8))
    lab = [s.split(" ")[0] for s in comp["시나리오"].unique()]
    for a, col in zip(ax, ["총 대기(분)", "방문 점포 수", "복귀 여유(분)"]):
        for j, (g, c) in enumerate([("최적 경로", "#0B3C5D"), ("인기순 경로", "#9FB3C4")]):
            v = comp[comp["경로"] == g][col].astype(float).values
            a.bar([x + j * 0.4 for x in range(len(v))], v, 0.4, color=c, label=g)
        a.set_xticks([x + 0.2 for x in range(len(lab))]); a.set_xticklabels(lab); a.set_title(col + (" = 줄 + 문 열기·식사 간격 기다림" if col.startswith("총") else ""), fontsize=10)
    ax[2].axhline(0, color="#E8573F", lw=1); ax[0].legend(fontsize=9)
    fig.suptitle("최적 경로 vs 인기순 경로 (같은 규칙, 같은 시나리오)", fontsize=12)
    fig.tight_layout(); fig.savefig(F / "그림15_인기순비교.png", dpi=160); plt.close(fig)

    print(comp.drop(columns="루트").to_string(index=False))
    print(stress.to_string(index=False))
    print("서비스 B안 필요 칸:", sum(bool(x["drop"]) for x in pb), "/", len(pb))
