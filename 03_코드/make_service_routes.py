"""서비스(Busan Bite Pass)용 최적 루트 사전 계산.

승객이 고르는 조건 = 하선 터미널 × 하선 시각 × 돌아다닐 수 있는 시간.
조건 격자마다 OPTW 최적해를 미리 풀어 06_서비스/routes.json 으로 저장한다(웹앱은 가장 가까운 칸을 보여 준다).
  터미널 2 (북항 D1, 영도 D2) × 하선 08:00~13:00 30분 간격 11 × 가용 3~9시간 7 = 154칸
  승선 마감 = 하선 + 가용시간 + 30분(복귀 여유)
실행(프로젝트 루트): python 03_코드/make_service_routes.py [작업 수, 기본 14]   — 약 20~30분
"""
import json
import multiprocessing as mp
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "06_서비스"


def setup():
    sys.path.insert(0, str(ROOT / "03_코드"))
    src = (ROOT / "03_코드/run_B_model.py").read_text(encoding="utf-8")
    ns = {"__file__": str(ROOT / "03_코드/run_B_model.py")}
    exec(src[:src.index("# 1) 시나리오별")], ns)   # 문제 정의만 (모델 계산은 하지 않음)
    return ns["P"]


def solve_cell(args):
    depot, start, hours = args
    from cruise_route_optw import Scenario
    P = solve_cell.P
    sc = Scenario(f"{depot}-{start}-{hours}", depot, start, start + hours * 60 + 30)
    t0 = time.time()
    res = P.solve(sc, k=1)
    if not res:
        return {"depot": depot, "start": start, "hours": hours, "stops": [], "sec": round(time.time() - t0)}
    route = res[0]["route"]
    ev = P.evaluate(route, sc, plan=res[0]["timeline"])   # 최적화가 정한 줄 서기 시각을 따른다(가장 이른 시각이 아니라)
    stops = [{"node": s["node"], "leave": round(s["leave"]), "queue_start": round(s["queue_start"]), "queue": round(s["queue"]),
              "begin": round(s["begin"]), "end": round(s["end"]), "from": s["from"]} for s in ev["stops"]]
    return {"depot": depot, "start": start, "hours": hours, "objective": ev["objective"], "return": round(ev["return_min"]),
            "feasible": ev["feasible"], "stops": stops, "sec": round(time.time() - t0)}


def init():
    solve_cell.P = setup()


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    cells = [(d, s, h) for d in ("D1", "D2") for s in range(8 * 60, 13 * 60 + 1, 30) for h in range(3, 10)]
    done = {}
    part = OUT / "_routes_partial.json"
    if part.exists():   # 중단 후 이어서
        done = {(c["depot"], c["start"], c["hours"]): c for c in json.loads(part.read_text(encoding="utf-8"))}
    todo = [c for c in cells if c not in done]
    print(f"{len(cells)}칸 중 {len(todo)}칸 계산", flush=True)
    with mp.Pool(int(sys.argv[1]) if len(sys.argv) > 1 else 14, initializer=init) as pool:
        for i, r in enumerate(pool.imap_unordered(solve_cell, todo), 1):
            done[(r["depot"], r["start"], r["hours"])] = r
            part.write_text(json.dumps(list(done.values()), ensure_ascii=False), encoding="utf-8")
            print(f"[{i}/{len(todo)}] {r['depot']} {r['start'] // 60:02d}:{r['start'] % 60:02d} {r['hours']}h → {len(r['stops'])}곳, {r['sec']}s", flush=True)
    (OUT / "routes.json").write_text(json.dumps(sorted(done.values(), key=lambda c: (c["depot"], c["start"], c["hours"])),
                                                ensure_ascii=False), encoding="utf-8")
    part.unlink(missing_ok=True)
    print("done", flush=True)
