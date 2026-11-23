"""F. 현장 관측 → 대기행렬 모수 추정 (교수님 피드백: 점포 5곳 시간대별 도착·처리 시작·종료·창구 수·퇴장 기록)

기록지: 05_문서/현장관측_기록지.csv 를 복사해 01_원천데이터/현장관측/ 에 날짜별로 채워 넣는다(한 줄 = 한 일행).
  열: 날짜, 기항일(Y/N), 점포ID, 일행번호, 인원, 도착, 처리시작, 처리종료, 퇴장, 창구수, 크루즈승객(Y/N/?), 비고   (시각은 HH:MM)
  - 도착 = 줄 끝에 선 시각, 처리시작 = 주문·착석 시각, 처리종료 = 음식 받음(포장)·식사 끝(식당), 퇴장 = 가게를 떠난 시각
  - 창구수 = 그 시각에 열려 있던 주문 창구·테이블 수
추정(점포 × 기항여부 × 시간대):
  λ = 시간당 도착 일행 수, 처리 분 = 평균(처리종료 − 처리시작) → μ = 60/처리 분, c = 창구 수 최빈값,
  관측 대기 = 평균(처리시작 − 도착), Erlang C 예측 대기(같은 λ·μ·c), 가동률 ρ = λ/(cμ), 시간당 수용 인원 = c·μ·평균 인원
기항일 vs 비기항일: 점포별 평균 대기·도착 수 차이와 Welch t 값(표본이 작으면 참고용).
산출: 02_정제데이터/현장관측_추정_F.csv, 현장관측_기항일비교_F.csv
      → 모델 반영: food_nodes_1118_B.csv 에 cap_hour(시간당 수용 인원), wait_peak_min(점심 관측 대기)을 넣으면 최적화가 그 값을 쓴다.
관측일 고르기: python 03_코드/analysis_F_observation.py --plan <부산항 크루즈 스케줄 CSV>
  → 오늘 이후 승객이 많은 기항일 10개와, 같은 요일 중 기항 없는 날(앞뒤 주)을 짝지어 후보로 보여 준다.
자체 점검: python 03_코드/analysis_F_observation.py --selftest  (가상 M/M/1 표본으로 추정식 확인, 결과는 저장하지 않음)
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
OBS = ROOT / "01_원천데이터/현장관측"
COLS = ["날짜", "기항일", "점포ID", "일행번호", "인원", "도착", "처리시작", "처리종료", "퇴장", "창구수", "크루즈승객", "비고"]
STORES = {"N06": "국제시장 먹자골목(대표 노점 1곳)", "N04": "BIFF광장 씨앗호떡", "N05": "부평깡통시장(대표 노점 1곳)",
          "N08": "원조18번완당", "N07": "성일집(자갈치)"}


def erlang_wq(lam, mu, c):
    """M/M/c 평균 대기(분). 시간당 λ·μ. ρ ≥ 1 이면 inf."""
    if lam <= 0:
        return 0.0
    a = lam / mu
    if a >= c:
        return math.inf
    term, s = 1.0, 1.0
    for k in range(1, c):
        term *= a / k
        s += term
    last = term * a / c / (1 - a / c)
    return last / (s + last) / (c * mu - lam) * 60


def minutes(x):
    h, m = str(x).split(":")
    return int(h) * 60 + int(m)


def estimate(df):
    df = df.copy()
    for c in ["도착", "처리시작", "처리종료", "퇴장"]:
        df[c] = df[c].map(minutes)
    df["대기"] = df["처리시작"] - df["도착"]
    df["처리"] = df["처리종료"] - df["처리시작"]
    df["시간대"] = df["도착"] // 60
    rows = []
    for (store, cruise, h), g in df.groupby(["점포ID", "기항일", "시간대"]):
        lam = len(g)                                   # 1시간 창의 도착 일행 수
        svc = g["처리"].mean()
        mu, c = 60.0 / max(svc, 0.1), int(g["창구수"].mode().iloc[0])
        rows.append({"점포ID": store, "점포": STORES.get(store, store), "기항일": cruise, "시간대": f"{h:02d}시",
                     "도착 일행/시간 λ": lam, "평균 처리(분)": round(svc, 1), "창구 수 c": c,
                     "가동률 ρ": round(lam / (c * mu), 2), "관측 대기(분)": round(g["대기"].mean(), 1),
                     "Erlang C 예측 대기(분)": round(erlang_wq(lam, mu, c), 1),
                     "시간당 수용 인원": round(c * mu * g["인원"].mean(), 1)})
    est = pd.DataFrame(rows)
    cmp_rows = []
    for store, g in df.groupby("점포ID"):
        y, n = g[g["기항일"] == "Y"]["대기"], g[g["기항일"] == "N"]["대기"]
        t = (y.mean() - n.mean()) / math.sqrt(y.var(ddof=1) / len(y) + n.var(ddof=1) / len(n)) if len(y) > 1 and len(n) > 1 else float("nan")
        cmp_rows.append({"점포ID": store, "점포": STORES.get(store, store), "기항일 평균 대기(분)": round(y.mean(), 1),
                         "비기항일 평균 대기(분)": round(n.mean(), 1), "차이(분)": round(y.mean() - n.mean(), 1),
                         "Welch t": round(t, 2), "기항일 일행 수": len(y), "비기항일 일행 수": len(n)})
    return est, pd.DataFrame(cmp_rows)


def plan(schedule_csv, today=pd.Timestamp.today().normalize()):
    """스케줄 CSV(열 이름에 '입항'·'선명'·'승객' 또는 date·ship·passengers 포함)에서 관측일 후보 짝을 뽑는다."""
    s = pd.read_csv(schedule_csv, encoding_errors="ignore")
    pick = lambda keys: next(c for c in s.columns if any(k in str(c) for k in keys))
    s["d"] = pd.to_datetime(s[pick(["입항", "date"])].astype(str).str[:10], errors="coerce").dt.normalize()
    s = s[s["d"] >= today]
    days = s.groupby("d").agg(척=("d", "size"), 승객=(pick(["승객", "passenger"]), "sum"), 선박=(pick(["선명", "ship"]), lambda x: ", ".join(map(str, x))))
    rows = []
    soon = days[days.index < today + pd.Timedelta(weeks=6)]   # 관측은 앞으로 6주 안에
    for d, r in soon.sort_values("승객", ascending=False).head(10).iterrows():
        free = [d + pd.Timedelta(days=7 * k) for k in (-1, 1, 2) if d + pd.Timedelta(days=7 * k) not in days.index and d + pd.Timedelta(days=7 * k) >= today]
        rows.append({"기항일": d.date(), "요일": "월화수목금토일"[d.weekday()], "척": r["척"], "승객": int(r["승객"]), "선박": r["선박"],
                     "비교용 비기항일(같은 요일)": free[0].date() if free else "없음"})
    return pd.DataFrame(rows)


def selftest():
    rng = np.random.default_rng(0)
    lam, mu = 20.0, 30.0                               # 시간당 도착 20팀, 처리 2분 → ρ = 0.67, M/M/1 이론 대기 = 4분
    t, free, rows = 11 * 60.0, 11 * 60.0, []
    for i in range(4000):
        t += rng.exponential(60 / lam)
        start = max(t, free); free = start + rng.exponential(60 / mu)
        rows.append((t, start, free))
    a = np.array(rows)
    obs_wait = (a[:, 1] - a[:, 0]).mean()
    lam_hat = len(a) / ((a[-1, 0] - a[0, 0]) / 60)
    mu_hat = 60 / (a[:, 2] - a[:, 1]).mean()
    pred = erlang_wq(lam_hat, mu_hat, 1)
    assert abs(lam_hat - lam) / lam < 0.05 and abs(mu_hat - mu) / mu < 0.05, (lam_hat, mu_hat)
    assert abs(pred - 4.0) < 1.0 and abs(obs_wait - 4.0) < 1.0, (pred, obs_wait)
    print(f"selftest OK: λ̂={lam_hat:.1f} μ̂={mu_hat:.1f} 관측 대기 {obs_wait:.2f}분 · Erlang C {pred:.2f}분 (이론 4분)")


if __name__ == "__main__":
    if "--selftest" in sys.argv:
        selftest()
    elif "--plan" in sys.argv:
        print(plan(sys.argv[sys.argv.index("--plan") + 1]).to_string(index=False))
    else:
        files = sorted(OBS.glob("*.csv"))
        if not files:
            sys.exit(f"관측 기록이 없습니다: {OBS} 에 05_문서/현장관측_기록지.csv 형식으로 넣어 주세요.")
        df = pd.concat([pd.read_csv(f, dtype=str) for f in files]).dropna(subset=["도착", "처리시작", "처리종료"])
        df["인원"] = df["인원"].astype(float); df["창구수"] = df["창구수"].astype(int)
        est, cmp_ = estimate(df)
        est.to_csv(ROOT / "02_정제데이터/현장관측_추정_F.csv", index=False, encoding="utf-8-sig")
        cmp_.to_csv(ROOT / "02_정제데이터/현장관측_기항일비교_F.csv", index=False, encoding="utf-8-sig")
        print(est.to_string(index=False), "\n\n", cmp_.to_string(index=False))
