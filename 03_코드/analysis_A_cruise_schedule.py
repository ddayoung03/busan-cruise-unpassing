"""A. 부산항 크루즈 입출항 신고정보(실적, 2023.1~2026.7) 분석

원천: 01_원천데이터/data.go.kr/busan_cruise_report/부산항 크루즈 입출항 신고정보.csv (data.go.kr 15164568)
실행: python 03_코드/analysis_A_cruise_schedule.py   (프로젝트 루트에서)
산출: 02_정제데이터/기항일여부_1118_A.csv, 체류시간요약_1118_A.csv, 연도별실적_1118_A.csv, 04_그림/그림4·5
"""
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

plt.rcParams["font.family"] = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False

ROOT = Path(__file__).resolve().parents[1]
raw = pd.read_csv(ROOT / "01_원천데이터/data.go.kr/busan_cruise_report/부산항 크루즈 입출항 신고정보.csv",
                  encoding="cp949")

df = pd.DataFrame({
    "ship": raw["선박명"],
    "arr": pd.to_datetime(raw["입항일시"]),
    "dep": pd.to_datetime(raw["출항일시"]),
    "berth": raw["부두명"],
    "pax": raw["외국인 승객수"].fillna(0) + raw["한국인 승객수"].fillna(0),
    "board": raw["당항 승선 승객수"].fillna(0),   # 부산에서 타는 승객(모항)
    "alight": raw["당항 하선 승객수"].fillna(0),  # 부산에서 내리는 승객(모항)
    "purpose": raw["입항목적"],
})
df = df.drop_duplicates(["ship", "arr"])
allcalls = df[df["arr"] >= "2023-01-01"].copy()   # 연간 실적용(체류 필터 전 전체 신고)
df["terminal"] = df["berth"].map(lambda b: "영도" if "영도" in str(b) else "북항")
df["dwell_h"] = (df["dep"] - df["arr"]).dt.total_seconds() / 3600
df = df[(df["dwell_h"] > 0) & (df["dwell_h"] < 96) & (df["arr"] >= "2023-01-01")].copy()
df["type"] = pd.cut(df["dwell_h"], [0, 8, 13, 96], labels=["기항(8h 이하)", "기항(8~13h)", "오버나잇"])
df["year"], df["month"] = df["arr"].dt.year, df["arr"].dt.month
df["date"] = df["arr"].dt.normalize()
df["arr_h"] = df["arr"].dt.hour + df["arr"].dt.minute / 60
df["dep_h"] = df["dep"].dt.hour + df["dep"].dt.minute / 60
# 상륙 가능 시간 = 체류 − 하선·입국심사 1.5h − 출항 전 승선마감 1h (가정, 선사 공지 관행)
df["shore_h"] = (df["dwell_h"] - 2.5).clip(lower=0)

# 1) 체류시간 요약
summary = df.groupby("type", observed=True).agg(
    항차=("ship", "count"), 승객=("pax", "sum"), 체류_중앙값h=("dwell_h", "median"),
    상륙가능_중앙값h=("shore_h", "median"), 접안_중앙값=("arr_h", "median"), 이안_중앙값=("dep_h", "median"),
).round(2)
summary["항차비중%"] = (summary["항차"] / summary["항차"].sum() * 100).round(1)
summary["승객비중%"] = (summary["승객"] / summary["승객"].sum() * 100).round(1)
summary.to_csv(ROOT / "02_정제데이터/체류시간요약_1118_A.csv", encoding="utf-8-sig")

overall = {
    "항차": len(df),
    "체류_중앙값h": round(df["dwell_h"].median(), 2),
    "승객가중_평균_상륙가능h": round((df["shore_h"] * df["pax"]).sum() / df["pax"].sum(), 2),
    "상륙가능_8h이하_승객%": round(df.loc[df["shore_h"] <= 8, "pax"].sum() / df["pax"].sum() * 100, 1),
    "모항(승선+하선)_승객비중%": round((df["board"] + df["alight"]).sum() / df["pax"].sum() * 100, 1),
}

# 2) 연도별 실적 + 1~7월 YOY — 체류 필터 전 '전체 신고' 기준
allcalls["year"], allcalls["month"] = allcalls["arr"].dt.year, allcalls["arr"].dt.month
yr = allcalls.groupby("year").agg(항차=("ship", "count"), 승객=("pax", "sum"))
jj = allcalls[allcalls["month"] <= 7].groupby("year").agg(항차_1_7월=("ship", "count"), 승객_1_7월=("pax", "sum"))
yr = yr.join(jj)
yr["승객_1_7월_YOY%"] = (yr["승객_1_7월"].pct_change() * 100).round(1)
yr.to_csv(ROOT / "02_정제데이터/연도별실적_1118_A.csv", encoding="utf-8-sig")
# 2025 승객 수 기준 차이 설명표: 보도 → 신고 전체 → 체류분석 표본
a25 = allcalls[allcalls["year"] == 2025]
f25 = df[df["year"] == 2025]
recon = pd.DataFrame([
    {"기준": "언론 보도(부산항만공사 발표 인용)", "항차": 203, "승객": 257000, "출처": "segye 2026.7.27, fnnews 2026.1.18"},
    {"기준": "입출항 신고 전체(중복 제거)", "항차": len(a25), "승객": int(a25["pax"].sum()), "출처": "data.go.kr 15164568"},
    {"기준": "체류분석 표본(체류 0~96h)", "항차": len(f25), "승객": int(f25["pax"].sum()), "출처": "위에서 체류 96h 이상·음수 제외"},
])
recon.to_csv(ROOT / "02_정제데이터/2025승객수_기준차이_1118_A.csv", index=False, encoding="utf-8-sig")

# 3) 기항일 더미 (A 산출물 형식: date, terminal, ship, passengers, is_cruise_day)
#    정의: 배가 부두에 있는 모든 날짜(입항일~출항일). 전체 신고 기준.
stay_rows = []
for r in allcalls.itertuples():
    for d in pd.date_range(r.arr.normalize(), r.dep.normalize()):
        stay_rows.append({"date": d, "terminal": "영도" if "영도" in str(r.berth) else "북항",
                          "ship": r.ship, "passengers": r.pax})
day = (pd.DataFrame(stay_rows).groupby(["date", "terminal"])
       .agg(ship=("ship", lambda s: "|".join(s)), passengers=("passengers", "sum")).reset_index())
day["is_cruise_day"] = 1
day.to_csv(ROOT / "02_정제데이터/기항일여부_1118_A.csv", index=False, encoding="utf-8-sig")
purpose = allcalls["purpose"].value_counts()
purpose_share = f"여객상륙 {purpose.get('여객상륙', 0)}/{purpose.sum()} = {purpose.get('여객상륙', 0) / purpose.sum() * 100:.1f}% (전체 신고 2023~2026.7, 항차 기준)"
daily = df.groupby("date").agg(ships=("ship", "count"), pax=("pax", "sum"))
recent = daily[daily.index >= "2025-01-01"]
multi = (recent["ships"] >= 2).mean() * 100
peak_day = recent["pax"].idxmax()

# 4) 그림
out = ROOT / "04_그림"
fig, ax = plt.subplots(1, 2, figsize=(12, 4.3))
ax[0].hist(df["shore_h"].clip(upper=24), bins=24, weights=df["pax"] / 1000, color="#1f3b63", edgecolor="white")
med = df.loc[df["pax"] > 0, "shore_h"].median()
ax[0].axvline(8, color="#e07a2f", ls="--", lw=2, label="8시간")
ax[0].set_title("부산항 크루즈 승객의 상륙 가능 시간 (2023~2026.7 실적)")
ax[0].set_xlabel("상륙 가능 시간 = 체류-2.5h (시간)"); ax[0].set_ylabel("승객 (천 명)"); ax[0].legend()
sd = df[df["dwell_h"] <= 13]
ax[1].hist([sd["arr_h"], sd["dep_h"]], bins=range(5, 25), label=["입항 시각", "출항 시각"],
           color=["#1f3b63", "#e07a2f"])
ax[1].set_title("당일 기항 선박의 입·출항 시각"); ax[1].set_xlabel("시각"); ax[1].legend()
plt.tight_layout(); plt.savefig(out / "그림4_체류시간분포.png", dpi=200); plt.close()

piv = allcalls[allcalls["year"] >= 2024].pivot_table(index="month", columns="year", values="pax", aggfunc="sum") / 1000
piv.plot(kind="bar", figsize=(9, 4), color=["#9aa5b1", "#1f3b63", "#e07a2f"][: piv.shape[1]])
plt.title("월별 부산항 크루즈 승객 (입출항 신고 전체, 천 명)"); plt.xlabel("월"); plt.ylabel("천 명")
plt.xticks(rotation=0); plt.tight_layout(); plt.savefig(out / "그림5_월별승객.png", dpi=200); plt.close()

if __name__ == "__main__":
    print(summary.to_string()); print(overall); print(yr.to_string()); print(recon.to_string())
    print(f"2025년 이후 2척 이상 동시 입항일 비중: {multi:.1f}% / 최대 승객일 {peak_day.date()} "
          f"{int(recent.loc[peak_day, 'pax'])}명 {int(recent.loc[peak_day, 'ships'])}척")
    print(purpose_share)
