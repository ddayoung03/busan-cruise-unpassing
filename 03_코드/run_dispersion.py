"""B. 혼잡 분산·골목 시나리오만 따로, 병렬로 다시 계산 (run_B_model.py 4)·7)절과 같은 규칙)

실행(프로젝트 루트):
  python 03_코드/run_dispersion.py k4      # 같은 배 6그룹, 겹침 100명당 +4분
  python 03_코드/run_dispersion.py k8      # 같은 배 6그룹, +8분
  python 03_코드/run_dispersion.py alley   # 2026-05-08 실제 2척 동시 기항
  python 03_코드/run_dispersion.py merge   # 위 세 결과를 CSV로 합침
세 계산은 서로 독립이라 터미널 3개(또는 백그라운드)로 동시에 돌린다. 각 최적화의 소요시간을 로그로 남긴다.
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_코드"))
from cruise_route_optw import Scenario, fmt   # noqa: E402

_src = (ROOT / "03_코드/run_B_model.py").read_text(encoding="utf-8")
_ns = {"__file__": str(ROOT / "03_코드/run_B_model.py")}
exec(_src[:_src.index("# 1) 시나리오별")], _ns)          # 문제·시나리오 정의만
P, S1, H, D = _ns["P"], _ns["S1"], _ns["H"], _ns["D"]
OUT = ROOT / "02_정제데이터"
mode = sys.argv[1]

# 최적화 호출마다 소요시간 로그
_solve = P.solve
def logged_solve(sc, *a, **kw):
    t = time.time(); r = _solve(sc, *a, **kw)
    print(f"[{mode}] solve {sc.name[:20]} start {fmt(sc.start)} crowd={sum(len(v) for v in sc.crowd.values())} "
          f"→ {time.time() - t:.0f}s", flush=True)
    return r
P.solve = logged_solve

def ev_row(e):
    return {"route": e["route"], "names": e["names"], "queue_min": e["queue_min"], "return_min": e["return_min"],
            "feasible": e["feasible"], "late": e["violations"]["복귀 지각"], "converged": e["converged"],
            "visits": [(n, float(s0)) for n, s0 in e["visits"]]}

if mode in ("k4", "k8"):
    k = 4.0 if mode == "k4" else 8.0
    res = pd.read_csv(OUT / "루트결과_1118_B.csv", dtype={"순위": str})
    name2id = {P.A[n]["name_ko"]: n for n in P.ids}
    best = [name2id[x] for x in res[(res["시나리오"] == S1.name) & (res["순위"] == "1")].iloc[0]["루트"].split(" → ")]
    t0 = time.time()
    d_ev = P.joint_eval(P.dispersion(S1, groups=6, crowd_add=k))
    s_ev = P.joint_eval(P.same_route_plans(S1, best, groups=6, crowd_add=k))
    json.dump({"k": k, "disp": [ev_row(e) for e in d_ev], "same": [ev_row(e) for e in s_ev], "sec": time.time() - t0},
              open(OUT / f"_disp_{mode}.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[{mode}] done in {time.time() - t0:.0f}s", flush=True)

elif mode == "alley":
    SHIPS = [("SPECTRUM OF THE SEAS", 5242, H(6, 23), H(19, 15)), ("COSTA SERENA", 2589, H(11, 30), H(21))]
    LAND, APP, NG = 0.8, 0.10, 4
    t0, plans = time.time(), []
    for ship, pax, arr, dep in SHIPS:
        size = pax * LAND * APP / NG
        for s_, route, tl, _ in P.dispersion(Scenario(ship, "D1", arr + 90, dep - 60), groups=NG, size=size):
            plans.append((s_, route, tl, size))
    fin = P.joint_eval(plans)
    json.dump({"groups": [{**ev_row(e), "size": pl[3], "ship": pl[0].name} for pl, e in zip(plans, fin)], "sec": time.time() - t0},
              open(OUT / "_disp_alley.json", "w", encoding="utf-8"), ensure_ascii=False)
    print(f"[alley] done in {time.time() - t0:.0f}s", flush=True)

elif mode == "merge":
    rows, assign = [], None
    for m in ("k4", "k8"):
        j = json.load(open(OUT / f"_disp_{m}.json", encoding="utf-8"))
        for label, ev in [("전원 같은 루트", j["same"]), ("분산 배정", j["disp"])]:
            rows.append({"겹침당 추가대기(분)": j["k"], "배정": label,
                         "그룹 평균 줄대기(분)": round(np.mean([e["queue_min"] for e in ev]), 1),
                         "최대 줄대기(분)": max(e["queue_min"] for e in ev),
                         "복귀 지각 그룹": sum(e["late"] for e in ev),
                         "규칙 위반 그룹": sum(not e["feasible"] for e in ev),
                         "공동평가 수렴": ev[0]["converged"]})
        if m == "k8":
            assign = pd.DataFrame([{"그룹": i + 1, "출발": fmt(S1.start + 10 * i), "루트": " → ".join(e["names"]),
                                    "줄대기(분)": e["queue_min"], "복귀": fmt(e["return_min"]), "위반 없음": e["feasible"]}
                                   for i, e in enumerate(j["disp"])])
    pd.DataFrame(rows).to_csv(OUT / "분산효과_1118_B.csv", index=False, encoding="utf-8-sig")
    assign.to_csv(OUT / "분산배정_1118_B.csv", index=False, encoding="utf-8-sig")
    j = json.load(open(OUT / "_disp_alley.json", encoding="utf-8"))
    fc, fail = {}, 0.0
    for g in j["groups"]:
        if g["feasible"] and g["converged"]:
            for n, s0 in g["visits"]:
                key = (P.A[n]["name_ko"], int(s0 // 60)); fc[key] = fc.get(key, 0) + g["size"]
        else:
            fail += g["size"]
    fc_df = pd.Series(fc).round(0).rename("명").reset_index()
    fc_df.columns = ["골목·가게", "시(줄 서기)", "명"]
    fc_df = fc_df.pivot_table(index="골목·가게", columns="시(줄 서기)", values="명", fill_value=0)
    fc_df.loc["(참고) 규칙 위반으로 제외된 그룹 인원"] = 0
    fc_df.loc["(참고) 규칙 위반으로 제외된 그룹 인원", fc_df.columns[0]] = round(fail)
    fc_df.to_csv(OUT / "골목방문시나리오_20260508_B.csv", encoding="utf-8-sig")
    print(pd.DataFrame(rows).to_string(), "\n\n", assign.to_string(), "\n\n", fc_df.to_string())
