"""D. 확률·동역학 분석: 대기행렬(M/M/c) · 마르코프 연쇄 정상분포 밸런싱 · A/B 시뮬레이션 · 2차원 선형 미분방정식

최적화 모델(cruise_route_optw)은 그대로 두고, 그 최적 루트(S1 상위 K개)를 입력으로 쓴다.
| 값 | 출처 | 성격 |
|---|---|---|
| 루트·시간표·만족도 | OPTW v4 (S1 북항 당일 기항, 상위 K개) | 모델 결과 |
| 배경 가동률(앱 없을 때) | 0.3 + 0.5 × 모델의 시간대 혼잡계수 | 가정 |
| 창구·테이블 수 c, 처리 분 | cruise_route_optw.SERVICE (업종별, 모델 수용인원과 같은 표) | 가정 |
| 앱 이용 승객 수·하선 간격 | N_APP, 100명씩 10분 간격 | 가정 |
| 순위별 선택 확률 | RANK_P (검색 결과 위치 편향 형태) | 가정 |
| 미분방정식 α·κ·β·δ·s | ODE | 가정 (γ만 대기행렬 결과로 보정) |

1) 대기행렬: 가게 = M/M/c. 앉아 먹는 곳은 테이블 c·서비스 = 체류시간, 포장·노점은 주문 창구 c·서비스 = 처리 시간.
   배경 가동률 ρ_bg(t)에 앱 이용 일행 도착 λ_app을 더해, 앱 때문에 늘어난 대기 Wq(λ_bg+λ_app) − Wq(λ_bg)를 계산한다(ρ ≥ 1이면 과부하, 대기 상한 120분).
   늘어난 대기만큼 뒤 일정이 밀리며, 승선 마감 30분 전(= 시나리오 deadline)을 넘기면 지각.
2) 밸런싱: 루트 선택확률 p_k ∝ exp(U_k/τ), U_k = 루트 만족도 − 0.8 × 혼잡으로 늘어난 대기. p → 혼잡 → U → p 를 반복해 수렴(고정점).
   승객 흐름을 '터미널 → 가게 → … → 터미널'로 도는 마르코프 연쇄로 보고, 전이행렬의 정상분포 π(가게별 장기 방문 비중)와
   수렴 속도(게으른 연쇄 (I+P)/2 의 둘째 고윳값)를 구한다.
3) A/B 시뮬레이션(같은 승객·같은 날, 몬테카를로): C 앱 없음(제약 무시 계획 = 유명한 곳 위주) / A 루트 나열(균등 선택) /
   B 순위 표시(위치 편향) / B* 밸런싱 순위(2의 고정점). 차이 = 추천 효과(다른 조건이 같으므로 인과 해석 가능, 단 시뮬레이션).
4) 미분방정식: x = 주간 앱 이용 승객(백 명), y = 혼잡으로 늘어난 대기(분).
   dx/dt = s + (κ−α)x − βy,  dy/dt = γx − δy  →  야코비안 고윳값으로 거동 분류(안정 마디점/안정 나선/안장점 …).
   γ = δ × (앱 이용자 100명당 늘어난 대기) — B(순위)와 B*(밸런싱)에서 각각 대기행렬로 잰다.
산출: 02_정제데이터/확률모델_*_1120_D.csv, 04_그림/그림11_마르코프수렴.png, 그림12_AB시뮬레이션.png, 그림13_위상도.png
실행(프로젝트 루트): python 03_코드/analysis_D_stochastic.py   (S1 상위 루트는 처음 한 번 약 5분 계산 후 캐시)
"""
import json
import math
import platform
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_코드"))
from cruise_route_optw import LAMBDA, PARTY, SERVICE, Problem, Scenario, congestion, fmt   # 창구 수·처리 분·일행 크기 가정은 모델과 공유  # noqa: E402

plt.rcParams["font.family"] = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False
D, F = ROOT / "02_정제데이터", ROOT / "04_그림"
save = lambda df, name: df.to_csv(D / name, index=False, encoding="utf-8-sig")

# ---------------- 가정 ----------------
RHO_BG = (0.3, 0.5)                                # 앱 없을 때 배경 가동률 = 0.3 + 0.5 × 시간대 혼잡계수(점심 피크 0.8) — 가정
N_APP = 60                                         # 출시 초기: 한 배 약 3,000명 × 앱 이용 2% — 가정 (6그룹, 10분 간격 하선)
SWEEP = [30, 60, 90, 120, 150, 210, 300]           # 수용 한계 곡선용 앱 이용자 수
GROUPS, STAGGER = 6, 10
RANK_DECAY = 0.55                                  # 순위 표시 때 r위 선택 확률 ∝ 0.55^r (검색 결과 위치 편향 형태) — 가정
TAU = 10.0                                         # 밸런싱 로짓 온도(점) — 가정
W_CAP = 120.0                                      # 과부하(ρ≥1) 때 대기 상한(분)
K = 5
RUNS = 400
ODE = dict(s=0.3, alpha=0.30, kappa=0.20, beta=0.02, delta=0.5)   # 주 단위 — 가정

nodes = pd.read_csv(D / "food_nodes_1118_B.csv")
P = Problem(nodes, pd.read_csv(D / "travel_time_1118_B.csv"))
S1 = Scenario("S1 북항 당일 기항(07~18시)", "D1", 8 * 60 + 30, 17 * 60)

# ---------------- S1 상위 K 루트 (캐시) ----------------
CACHE = D / "S1상위루트_v4_1120_D.json"
if CACHE.exists():
    top = json.loads(CACHE.read_text(encoding="utf-8"))
else:
    top = [{"route": r["route"], "timeline": [list(x) for x in r["timeline"]], "objective": r["objective"]} for r in P.solve(S1, k=K)]
    CACHE.write_text(json.dumps(top, ensure_ascii=False), encoding="utf-8")
naive = P.naive_plan(S1)[:7]   # 앱 없는 관광객: 줄·소화·영업을 모른 채 유명한 곳 7곳(제약 무시 계획 앞 7곳)


def stops_of(route, plan=None):
    ev = P.evaluate(route, S1, plan=plan)
    return ev, tuple((s["node"], s["queue_start"], s["queue"]) for s in ev["stops"] if s["queue"] > 0 or P.A[s["node"]]["wait_peak_min"] > 0)


# 후보 = 최적 상위 K개(서로 비슷함) + 분산 배정 6그룹 루트(서로 겹치지 않게 다시 푼 것, run_dispersion k8 결과)
cand = [(r["route"], r["timeline"]) for r in top]
DISP = D / "_disp_k8.json"
if DISP.exists():
    cand += [(g["route"], None) for g in json.loads(DISP.read_text(encoding="utf-8"))["disp"] if g["route"]]
ROUTES, seen = [], set()   # (이름, 계획 목적함수, 복귀, ((노드, 줄서기, 계획대기)…), 규칙 준수, 루트) — 튜플: dict 키로 쓴다
for route, plan in cand:
    if tuple(route) in seen:
        continue
    seen.add(tuple(route))
    ev, st = stops_of(route, plan)
    if ev["feasible"]:
        ROUTES.append((None, ev["objective"], ev["return_min"], st, True, tuple(route)))
ROUTES = [(f"{i + 1}위", *r[1:]) for i, r in enumerate(sorted(ROUTES, key=lambda r: -r[1]))]   # 만족도 순 = 표시 순위
RANK_P = [RANK_DECAY ** i for i in range(len(ROUTES))]
ev_n, st_n = stops_of(naive)
NAIVE = ("앱 없음(유명한 곳 위주)", ev_n["objective"], ev_n["return_min"], st_n, ev_n["feasible"], tuple(naive))


# ---------------- 1) 대기행렬 M/M/c ----------------
def wq_min(lam, mu, c):
    """Erlang C 평균 대기(분). lam·mu = 시간당. ρ ≥ 1 이면 과부하 → 상한."""
    if lam <= 0:
        return 0.0
    a = lam / mu
    if a >= c:
        return W_CAP
    term, s = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        s += term
    last = term * a / c / (1 - a / c)
    return min(W_CAP, last / (s + last) / (c * mu - lam) * 60)


def mu_c(n):
    a = P.A[n]
    c, m = SERVICE.get(a["category"], (12, None))
    return 60.0 / (m or max(a["stay_min"], 1)), c


def lam_bg(n, h):
    """배경(앱 없는 손님) 도착률: 가동률 ρ_bg(t) = 0.3 + 0.5 × 혼잡계수(t) 가 되게. 앱 손님이 늘린 대기만 더한다
    (모델의 기본 줄 대기는 그대로 두고, 앱 때문에 '추가로' 생기는 대기를 Erlang C 로 잰다)."""
    mu, c = mu_c(n)
    return (RHO_BG[0] + RHO_BG[1] * congestion(h * 60 + 30)) * c * mu


def simulate(mix, rng=None, n_app=N_APP, wnoise=0.0):
    """mix: 루트(ROUTES 원소) → 승객 수. 그룹별 하선 지연을 반영해 가게·시간대 도착을 세고,
    늘어난 대기를 누적해 루트별 결과를 낸다."""
    arr = {}
    types = []
    for rt, cnt in mix.items():
        for g in range(GROUPS):
            m = cnt / GROUPS / PARTY          # 일행 수
            if m <= 0:
                continue
            types.append((rt, g * STAGGER, m))
            for n, qs, _ in rt[3]:
                key = (n, int((qs + g * STAGGER) // 60))
                arr[key] = arr.get(key, 0.0) + m
    extra = {}
    for (n, h), m in arr.items():
        mu, c = mu_c(n)
        lb = lam_bg(n, h)
        e = wq_min(lb + m, mu, c) - wq_min(lb, mu, c)
        if rng is not None and wnoise:
            e *= rng.uniform(1 - wnoise, 1 + wnoise)
        extra[n, h] = (e, (lb + m) / (c * mu))
    out = []
    for rt, off, m in types:
        delay = sum(extra[n, int((qs + off) // 60)][0] for n, qs, _ in rt[3])
        ret = rt[2] + off + delay
        out.append({"route": rt[0], "people": m * PARTY, "delay": delay, "late": ret > S1.deadline() + 1e-9 or not rt[4],
                    "score": rt[1] - LAMBDA * delay})
    rho_max = max((v[1] for v in extra.values()), default=0)
    visits = {}
    for rt, cnt in mix.items():
        for n in rt[5]:
            visits[n] = visits.get(n, 0) + cnt
    return out, rho_max, visits


def summarize(res, visits):
    df = pd.DataFrame(res)
    w = df["people"] / df["people"].sum()
    v = np.array(list(visits.values()), float)
    share = v / v.sum()
    return {"평균 만족도": float((df["score"] * w).sum()), "평균 추가 대기(분)": float((df["delay"] * w).sum()),
            "지각·규칙위반 비율": float((df["late"] * w).sum()), "가게 집중도 HHI": float((share ** 2).sum())}


# ---------------- 2) 밸런싱(고정점) + 마르코프 정상분포 ----------------
def mix_of(p, n=N_APP):
    return {ROUTES[k]: n * p[k] for k in range(len(ROUTES)) if p[k] > 0}


def balance(n=N_APP, iters=200):
    p = np.array(RANK_P[:len(ROUTES)], float)
    p /= p.sum()
    hist = []
    for it in range(iters):
        res, _, _ = simulate(mix_of(p, n), n_app=n)
        d = pd.DataFrame(res).groupby("route").apply(lambda g: np.average(g["delay"], weights=g["people"]), include_groups=False)
        U = np.array([ROUTES[k][1] - LAMBDA * d.get(ROUTES[k][0], 0.0) for k in range(len(ROUTES))])
        q = np.exp((U - U.max()) / TAU)
        q /= q.sum()
        step = np.abs(q - p).sum()
        hist.append(step)
        p = p + (q - p) / (it + 2)                   # 연속 평균법(MSA): 수렴 보장
        if step < 1e-5:
            break
    return p, hist


def markov(p_routes):
    """승객 흐름 전이행렬(터미널 포함) → 정상분포·수렴."""
    states = [S1.depot] + sorted({n for k, pk in enumerate(p_routes) if pk > 0 for n in ROUTES[k][5]})
    ix = {s: i for i, s in enumerate(states)}
    T = np.zeros((len(states), len(states)))
    for k, pk in enumerate(p_routes):
        if pk <= 0:
            continue
        seq = [S1.depot, *ROUTES[k][5], S1.depot]
        for a, b in zip(seq, seq[1:]):
            T[ix[a], ix[b]] += pk
    T /= T.sum(1, keepdims=True)
    L = 0.5 * (np.eye(len(states)) + T)          # 게으른 연쇄: 주기성 제거, 정상분포는 같다
    pi = np.zeros(len(states)); pi[0] = 1.0     # 모두 터미널에서 출발
    ev = np.linalg.eig(L.T)
    stat = np.real(ev[1][:, np.argmin(np.abs(ev[0] - 1))]); stat = stat / stat.sum()
    gaps = []
    for _ in range(60):
        pi = pi @ L
        gaps.append(np.abs(pi - stat).sum())
    lam2 = sorted(np.abs(ev[0]))[-2]
    return states, stat, gaps, lam2


p_bal, bal_hist = balance()
ARMS = {
    "C 앱 없음": {NAIVE: N_APP},
    "A 루트 나열(순위 없음)": mix_of(np.ones(len(ROUTES)) / len(ROUTES)),
    "B 순위 표시": mix_of(np.array(RANK_P[:len(ROUTES)]) / sum(RANK_P[:len(ROUTES)])),
    "B* 밸런싱 순위": mix_of(p_bal),
}

# ---------------- 3) A/B 몬테카를로 ----------------
rng = np.random.default_rng(7)
rows = []
for arm, base in ARMS.items():
    for r in range(RUNS):
        if arm.startswith("C"):
            mix = base
        else:   # 승객 개개인이 확률대로 고른다 → 다항분포
            keys = list(base)
            pk = np.array([base[k] for k in keys]) / N_APP
            cnt = rng.multinomial(N_APP, pk)
            mix = {k: c for k, c in zip(keys, cnt) if c}
        res, rho, vis = simulate(mix, rng, wnoise=0.3)
        rows.append({"배정": arm, "회차": r, **summarize(res, vis), "최대 가동률 ρ": rho})
ab = pd.DataFrame(rows)
ab_sum = ab.groupby("배정", sort=False).agg(["mean", "std"]).drop(columns="회차").round(3)
ab_sum.columns = [f"{a} ({b})" for a, b in ab_sum.columns]
ab_sum = ab_sum.reset_index()
save(ab_sum, "확률모델_AB시뮬레이션_1120_D.csv")

# ---------------- 마르코프 결과 ----------------
mk_rows, mk = [], {}
for name, p in [("B 순위 표시", np.array(RANK_P[:len(ROUTES)]) / sum(RANK_P[:len(ROUTES)])), ("B* 밸런싱 순위", p_bal),
                ("1위 루트만", np.eye(len(ROUTES))[0])]:
    states, stat, gaps, lam2 = markov(p)
    mk[name] = (states, stat, gaps, lam2)
    for s, v in zip(states, stat):
        mk_rows.append({"배정": name, "상태": P.A[s]["name_ko"], "정상분포 π": round(float(v), 4)})
    mk_rows.append({"배정": name, "상태": "(둘째 고윳값 |λ2|)", "정상분포 π": round(float(lam2), 4)})
save(pd.DataFrame(mk_rows), "확률모델_마르코프정상분포_1120_D.csv")
save(pd.DataFrame({
    "순위": [r[0] for r in ROUTES], "만족도(계획)": [r[1] for r in ROUTES], "복귀": [fmt(r[2]) for r in ROUTES],
    "순위 표시 확률": np.round(np.array(RANK_P[:len(ROUTES)]) / sum(RANK_P[:len(ROUTES)]), 3),
    "밸런싱 확률(수렴)": np.round(p_bal, 3), "경로": [" → ".join(P.A[n]["name_ko"] for n in r[5]) for r in ROUTES]}),
     "확률모델_밸런싱확률_1120_D.csv")


# ---------------- 4) 2차원 선형 미분방정식 ----------------
def gamma_static(p):
    """앱 이용자 100명당 평균 추가 대기(분) — 대기행렬의 0명 → 운영점(N_APP) 할선 기울기.
    (접선은 과부하 상한에 걸리면 0이 되어 왜곡되므로 할선으로 선형화한다)"""
    sm = summarize(*[simulate(mix_of(p, N_APP), n_app=N_APP)[i] for i in (0, 2)])
    return sm["평균 추가 대기(분)"] / N_APP * 100


def classify(J):
    ev = np.linalg.eigvals(J)
    tr, det = np.trace(J), np.linalg.det(J)
    if det < 0:
        kind = "안장점(불안정)"
    elif abs(ev[0].imag) > 1e-12:
        kind = "안정 나선(감쇠 진동)" if tr < 0 else ("중심(순환)" if abs(tr) < 1e-12 else "불안정 나선")
    else:
        kind = "안정 마디점(진동 없이 수렴)" if tr < 0 else "불안정 마디점"
    return ev, kind


o = ODE
ode_rows, traj = [], {}
for name, p in [("B 순위 표시", np.array(RANK_P[:len(ROUTES)]) / sum(RANK_P[:len(ROUTES)])), ("B* 밸런싱 순위", p_bal)]:
    gs = max(gamma_static(p), 1e-6)
    g = o["delta"] * gs
    J = np.array([[o["kappa"] - o["alpha"], -o["beta"]], [g, -o["delta"]]])
    ev, kind = classify(J)
    xs = np.linalg.solve(-J, [o["s"], 0.0])
    tconst = 1 / max(1e-9, -max(ev.real))
    ode_rows.append({"배정": name, "100명당 추가대기(분)": round(gs, 2), "γ": round(g, 3),
                     "고윳값1": f"{ev[0]:.3f}", "고윳값2": f"{ev[1]:.3f}", "분류": kind,
                     "평형 이용자(백 명/주)": round(xs[0], 2), "평형 추가대기(분)": round(xs[1], 1), "수렴 시간상수(주)": round(tconst, 1)})
    t, X, dt = [0.0], [np.array([0.0, 0.0])], 0.05
    for _ in range(int(40 / dt)):
        x = X[-1]
        X.append(x + dt * (J @ x + np.array([o["s"], 0.0]))); t.append(t[-1] + dt)
    traj[name] = (np.array(t), np.array(X), J, xs)
ode_df = pd.DataFrame(ode_rows)
save(ode_df, "확률모델_미분방정식_1120_D.csv")

# ---------------- 수용 한계: 앱 이용자 수를 늘리면 ----------------
sw = []
for n in SWEEP:
    pb, _ = balance(n)
    for name, p in [("A 루트 나열", np.ones(len(ROUTES)) / len(ROUTES)), ("B 순위 표시", np.array(RANK_P) / sum(RANK_P)), ("B* 밸런싱 순위", pb)]:
        res, rho, vis = simulate(mix_of(p, n), n_app=n)
        sm = summarize(res, vis)
        sw.append({"앱 이용자(명)": n, "배정": name, "평균 추가 대기(분)": round(sm["평균 추가 대기(분)"], 1),
                   "지각·규칙위반 비율": round(sm["지각·규칙위반 비율"], 3), "최대 가동률 ρ": round(rho, 2)})
sw = pd.DataFrame(sw)
save(sw, "확률모델_수용한계_1120_D.csv")

# ---------------- 그림 ----------------
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for name, (states, stat, gaps, lam2) in mk.items():
    ax[0].semilogy(range(1, len(gaps) + 1), np.maximum(gaps, 1e-12), label=f"{name} (|λ2|={lam2:.2f})")
ax[0].set_xlabel("단계(승객이 한 곳 이동)"); ax[0].set_ylabel("정상분포와의 거리 ‖π_t − π‖₁"); ax[0].legend(fontsize=8)
ax[0].set_title("마르코프 연쇄: 정상분포로 수렴")
for name in ["1위 루트만", "B* 밸런싱 순위"]:
    states, stat, _, _ = mk[name]
    lab = [P.A[s]["name_ko"].split("(")[0][:7] for s in states[1:]]
    ax[1].barh([f"{l}" for l in lab], stat[1:] / stat[1:].sum(), alpha=0.6, label=name)
ax[1].set_xlabel("장기 방문 비중 π (터미널 제외)"); ax[1].set_title("가게별 정상분포: 한 곳 몰림 vs 밸런싱"); ax[1].legend(fontsize=8)
ax[1].tick_params(axis="y", labelsize=7)
fig.tight_layout(); fig.savefig(F / "그림11_마르코프수렴.png", dpi=160); plt.close(fig)

cols = ["평균 만족도", "평균 추가 대기(분)", "지각·규칙위반 비율", "가게 집중도 HHI"]
fig, ax = plt.subplots(1, 4, figsize=(13, 3.6))
for a, c in zip(ax, cols):
    a.bar(range(len(ab_sum)), ab_sum[f"{c} (mean)"], yerr=ab_sum[f"{c} (std)"], color=["#9FB3C4", "#328CC1", "#0B3C5D", "#E8573F"])
    a.set_xticks(range(len(ab_sum))); a.set_xticklabels([s.split(" ")[0] for s in ab_sum["배정"]]); a.set_title(c, fontsize=10)
fig.suptitle(f"A/B 시뮬레이션 (앱 이용 {N_APP}명, {RUNS}회): C 앱 없음 · A 나열 · B 순위 · B* 밸런싱", fontsize=11)
fig.tight_layout(); fig.savefig(F / "그림12_AB시뮬레이션.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for a, (name, (t, X, J, xs)) in zip(ax, traj.items()):
    gx = np.linspace(0, max(X[:, 0].max(), xs[0]) * 1.4 + 0.1, 18); gy = np.linspace(0, max(X[:, 1].max(), xs[1]) * 1.4 + 0.1, 18)
    XX, YY = np.meshgrid(gx, gy)
    U = J[0, 0] * XX + J[0, 1] * YY + o["s"]; V = J[1, 0] * XX + J[1, 1] * YY
    a.streamplot(XX, YY, U, V, color="#C9D6E0", density=0.9)
    a.plot(X[:, 0], X[:, 1], color="#E8573F", lw=2); a.plot(*xs, "o", color="#0B3C5D")
    r = ode_df.set_index("배정").loc[name]
    a.set_title(f"{name}: {r['분류']}\n고윳값 {r['고윳값1']}, {r['고윳값2']}", fontsize=9)
    a.set_xlabel("x 앱 이용 승객(백 명/주)"); a.set_ylabel("y 혼잡으로 늘어난 대기(분)")
fig.tight_layout(); fig.savefig(F / "그림13_위상도.png", dpi=160); plt.close(fig)

fig, ax = plt.subplots(1, 2, figsize=(11, 4))
for (name, g), col in zip(sw.groupby("배정", sort=False), ["#328CC1", "#0B3C5D", "#E8573F"]):
    ax[0].plot(g["앱 이용자(명)"], g["평균 추가 대기(분)"], "o-", color=col, label=name)
    ax[1].plot(g["앱 이용자(명)"], g["최대 가동률 ρ"], "o-", color=col, label=name)
ax[0].set_ylabel("앱 때문에 늘어난 평균 대기(분)"); ax[1].set_ylabel("가장 붐비는 가게 가동률 ρ"); ax[1].axhline(1, color="gray", ls="--", lw=1)
for a in ax:
    a.set_xlabel("한 배의 앱 이용자(명)"); a.legend(fontsize=8)
fig.suptitle("대기행렬(M/M/c): 이용자가 늘수록 순위만 매긴 추천이 먼저 무너진다 (좌석·가동률은 가정)", fontsize=10)
fig.tight_layout(); fig.savefig(F / "그림14_수용한계.png", dpi=160); plt.close(fig)

print("루트:", *[f"{r[0]} 만족 {r[1]} 복귀 {fmt(r[2])} 규칙 {r[4]}" for r in ROUTES], sep="\n  ")
print("앱 없음:", " → ".join(P.A[n]["name_ko"] for n in naive), "규칙", ev_n["feasible"])
print("밸런싱 확률:", np.round(p_bal, 3), f"({len(bal_hist)}회 반복, 마지막 변화 {bal_hist[-1]:.1e})")
print(ab_sum.to_string(index=False))
print(ode_df.to_string(index=False))
