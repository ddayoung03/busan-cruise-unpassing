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
