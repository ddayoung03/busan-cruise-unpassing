"""A. 데이터랩 외국인 카드소비(구·월) × 크루즈 월별 승객 — 원도심 3구 vs 비교 3구

원천: 01_원천데이터/datalab/외국인_구별월별_202510_202609.csv
      (한국관광데이터랩 > 외래객 지역별 방한현황, 2026-11-18 조회 화면 응답에서 추출)
      foreign_card_total·food = 외국인 신용카드 관광소비(전체·식음료업). 단위는 화면 표기와 대조 필요 [확인 필요] → 비중·상관만 사용.
실행: python 03_코드/analysis_A_datalab.py   (프로젝트 루트에서)
산출: 02_정제데이터/외국인소비_원도심비교_1118_A.csv
주의: 월 10개(2025.10~2026.7) 겹침뿐이고 계절성과 섞여 있다 → 연관이지 인과 아님.
"""
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
d = pd.read_csv(ROOT / "01_원천데이터/datalab/외국인_구별월별_202510_202609.csv", dtype={"ym": str})
d["core"] = np.where(d["gu"].isin(["중구", "동구", "영도구"]), "원도심", "비교")
m = d.pivot_table(index="ym", columns="core", values=["foreign_card_total", "foreign_card_food"], aggfunc="sum")

raw = pd.read_csv(ROOT / "01_원천데이터/data.go.kr/busan_cruise_report/부산항 크루즈 입출항 신고정보.csv", encoding="cp949")
calls = pd.DataFrame({"ship": raw["선박명"], "arr": pd.to_datetime(raw["입항일시"]),
                      "pax": raw["외국인 승객수"].fillna(0) + raw["한국인 승객수"].fillna(0)}).drop_duplicates(["ship", "arr"])
cruise = calls.groupby(calls["arr"].dt.strftime("%Y%m"))["pax"].sum()

out = pd.DataFrame({
    "크루즈승객": cruise.reindex(m.index),
    "원도심 외국인소비 비중%": (m["foreign_card_total"]["원도심"] / m["foreign_card_total"].sum(axis=1) * 100).round(1),
    "원도심 식음료 비중%": (m["foreign_card_food"]["원도심"] / m["foreign_card_food"].sum(axis=1) * 100).round(1),
    "원도심 소비 중 식음료%": (m["foreign_card_food"]["원도심"] / m["foreign_card_total"]["원도심"] * 100).round(1),
    "비교구 소비 중 식음료%": (m["foreign_card_food"]["비교"] / m["foreign_card_total"]["비교"] * 100).round(1),
    "원도심 식음료(지수, 2025.10=100)": (m["foreign_card_food"]["원도심"] / m["foreign_card_food"]["원도심"].iloc[0] * 100).round(1),
    "비교 식음료(지수, 2025.10=100)": (m["foreign_card_food"]["비교"] / m["foreign_card_food"]["비교"].iloc[0] * 100).round(1),
})
out.index.name = "연월"
out.to_csv(ROOT / "02_정제데이터/외국인소비_원도심비교_1118_A.csv", encoding="utf-8-sig")
print(out.to_string())
ov = out.dropna(subset=["크루즈승객"])
print(f"\n겹치는 달 {len(ov)}개 · 크루즈승객 vs 원도심 식음료 비중 상관 r = {ov['크루즈승객'].corr(ov['원도심 식음료 비중%']):.2f}"
      f" · vs 원도심 소비 비중 r = {ov['크루즈승객'].corr(ov['원도심 외국인소비 비중%']):.2f}")

# 그림 9: 원도심 3구 vs 비교 3구 외국인 식음료 지수 + 크루즈 승객(보조축)
import platform
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"
lab = [f"{i[2:4]}.{i[4:]}" for i in out.index]
fig, ax = plt.subplots(figsize=(9, 4.2))
ax.plot(lab, out["원도심 식음료(지수, 2025.10=100)"], "-o", color="#E8573F", lw=2.5, label="원도심 3구(중·동·영도)")
ax.plot(lab, out["비교 식음료(지수, 2025.10=100)"], "-o", color="#8FA3B3", lw=2.5, label="비교 3구(서·부산진·해운대)")
ax.set_ylabel("외국인 식음료 카드소비 지수 (2025.10=100)")
ax2 = ax.twinx(); ax2.bar(lab, out["크루즈승객"].fillna(0) / 1e4, color="#0B3C5D", alpha=0.18, label="크루즈 승객(만 명, 우축)")
ax2.set_ylabel("크루즈 승객(만 명)")
h1, l1 = ax.get_legend_handles_labels(); h2, l2 = ax2.get_legend_handles_labels()
ax.legend(h1 + h2, l1 + l2, loc="upper left", fontsize=9, frameon=False)
ax.set_zorder(ax2.get_zorder() + 1); ax.patch.set_visible(False)
ax.set_title("원도심 외국인 식음료 +76% vs 비교 지역 +57% (2025.10→2026.7)", fontsize=11)
plt.tight_layout(); plt.savefig(ROOT / "04_그림/그림9_원도심비교.png", dpi=180); plt.close()

# 교수님 피드백: 월·구·업종 카드소비 ↔ 월별 '기항 횟수'(입출항 신고 항차 수)
# 업종은 데이터랩이 주는 전체·식음료(+비식음료 = 전체 − 식음료)와 방문자 수. 겹치는 달 10개뿐이라 상관·기울기는 참고용.
ncall = calls.groupby(calls["arr"].dt.strftime("%Y%m")).size()
d["기항횟수"] = d["ym"].map(ncall)
d["foreign_card_nonfood"] = d["foreign_card_total"] - d["foreign_card_food"]
rows = []
for gu, g in d.dropna(subset=["기항횟수"]).groupby("gu", sort=False):
    for col, lab in [("foreign_visitors", "방문자"), ("foreign_card_total", "카드소비 전체"), ("foreign_card_food", "식음료"), ("foreign_card_nonfood", "비식음료(쇼핑 등)")]:
        y = g[col] / g[col].iloc[0] * 100                      # 첫 달 = 100 지수
        slope = np.polyfit(g["기항횟수"], y, 1)[0]             # 기항 1회 늘 때 지수 변화
        rows.append({"구": gu, "원도심": gu in ["중구", "동구", "영도구"], "지표": lab, "달 수": len(g),
                     "기항횟수와 상관 r": round(g["기항횟수"].corr(g[col]), 2), "기항 10회당 지수 변화": round(slope * 10, 1)})
rel = pd.DataFrame(rows)
core = d[d["core"] == "원도심"].groupby("ym")[["foreign_card_food"]].sum().join(d[d["core"] == "비교"].groupby("ym")[["foreign_card_food"]].sum(), rsuffix="_비교")
core["원도심 식음료 비중%"] = core["foreign_card_food"] / (core["foreign_card_food"] + core["foreign_card_food_비교"]) * 100
core["기항횟수"] = core.index.map(ncall)
core = core.dropna()
rel.loc[len(rel)] = {"구": "원도심 vs 비교", "원도심": True, "지표": "원도심 식음료 비중%(차이)", "달 수": len(core),
                     "기항횟수와 상관 r": round(core["기항횟수"].corr(core["원도심 식음료 비중%"]), 2),
                     "기항 10회당 지수 변화": round(np.polyfit(core["기항횟수"], core["원도심 식음료 비중%"], 1)[0] * 10, 2)}
rel.to_csv(ROOT / "02_정제데이터/기항횟수_소비관계_1120_A.csv", index=False, encoding="utf-8-sig")
print("\n월별 기항 횟수:", ncall.reindex(sorted(d["ym"].unique())).to_dict())
print(rel.to_string(index=False))
