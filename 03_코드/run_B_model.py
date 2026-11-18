"""B. OPTW 실행 — 시나리오 6개, 기준선 비교, 민감도·고정루트 위험, 분산 배정, 지수, 골목 방문 시나리오, 지도

실행: python 03_코드/run_B_model.py   (프로젝트 루트에서, 약 20분)
Colab: 03_코드 폴더를 올리고 `%run 03_코드/run_B_model.py` (Linux는 나눔고딕 설치 필요: 수업 노트북 셀 1)
"""
import os
import sys
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "03_코드"))
from cruise_route_optw import Problem, Scenario, fmt, CORE_GU

plt.rcParams["font.family"] = "Malgun Gothic" if platform.system() == "Windows" else "NanumGothic"
plt.rcParams["axes.unicode_minus"] = False
D, F = ROOT / "02_정제데이터", ROOT / "04_그림"
save = lambda df, name, **kw: df.to_csv(D / name, encoding="utf-8-sig", **kw)

nodes = pd.read_csv(D / "food_nodes_1118_B.csv")
P = Problem(nodes, pd.read_csv(D / "travel_time_1118_B.csv"))
H = lambda h, mi=0: h * 60 + mi

# 시나리오 시각: 부산항 크루즈 입출항 신고 실적(2023~2026.7) 중앙값
#  - 8~13h 기항: 입항 07:00·출항 18:00 / 8h 이하 기항: 입항 10:30·출항 17:15
#  - 하선·입국심사 90분 후 출발, 승선 마감 = 출항 60분 전, 루트 복귀 = 승선 마감 30분 전
#  → S1의 '루트에 쓸 수 있는 시간' = 08:30~16:30 = 8시간 (A의 상륙가능시간 8.5h에서 복귀 여유 30분)
SCEN = [
    Scenario("S1 북항 당일 기항(07~18시)", "D1", H(8, 30), H(17)),
    Scenario("S2 영도 짧은 기항(10:30~17:15)", "D2", H(12), H(16, 15)),
    Scenario("S3 오버나잇 2일차(원도심 밖 1곳 필수)", "D1", H(9), H(19), must_far=True),
    Scenario("S4 모항 승선 전(체크인 15:30)", "D1", H(10), H(15, 30)),
    Scenario("S5 비기항일(크루즈 혼잡 없음)", "D1", H(8, 30), H(17), cruise_day=False),
    Scenario("S6 S1 + 대만 선호 가중(예시)", "D1", H(8, 30), H(17), nationality="tw"),
]
S1 = SCEN[0]

# 1) 시나리오별 상위 3개 방문집합 + 같은 제약의 탐욕법
rows, best = [], {}
for sc in SCEN:
    top = P.solve(sc, k=3)
    best[sc.name] = top[0]
    g = P.greedy(sc)
    for rank, r in [(str(i), r) for i, r in enumerate(top, 1)] + [("탐욕법(같은 제약)", g)]:
        rows.append({"시나리오": sc.name, "순위": rank, "루트": " → ".join(r["names"]), "목적함수": r["objective"],
                     "만족도": r["satisfaction"], "줄대기(분)": r["queue_min"], "규칙상 기다림(분)": r["idle_min"],
                     "이동(분)": r["travel_min"], "복귀": fmt(r["return_min"]), "1인 지출(원)": r["spend_krw"],
                     "원도심 밖 노드": len(r["far_nodes"]), "필수조건 충족": r.get("meets_must_far", True)})
res = pd.DataFrame(rows)
save(res, "루트결과_1118_B.csv", index=False)

# 2) 제약 무시 계획(위험 사례): 이동+체류만 보고 일정을 채우면 어떤 규칙이 깨지나
naive_rows = []
for sc in SCEN[:5]:
    ev = P.evaluate(P.naive_plan(sc), sc)
    naive_rows.append({"시나리오": sc.name, "방문 수": len(ev["route"]), "줄대기(분)": ev["queue_min"],
                       "복귀": fmt(ev["return_min"]), **{f"위반:{k}": v for k, v in ev["violations"].items()},
                       "루트": " → ".join(ev["names"])})
naive_df = pd.DataFrame(naive_rows)
save(naive_df, "제약무시계획_1118_B.csv", index=False)

# 3) S1 검증: (a) 최적 방문집합 민감도(대기 ±30%, 20회 재최적화) (b) 고정 루트 위험(대기 ±30%·이동 ±20%, 1000회)
sens = P.sensitivity(S1, runs=20)
risk = P.fixed_route_risk(S1, best[S1.name])
val_df = pd.DataFrame([{"지표": "최적 방문집합 유지율(재최적화 20회)", "값": round(sens["keep_rate"], 3)},
                       {"지표": "고정 루트 전체 규칙 준수율(1000회)", "값": round(risk["feasible_rate"], 4)},
                       {"지표": "고정 루트 복귀 지각 확률(1000회)", "값": round(risk["late_prob"], 4)}]
                      + [{"지표": f"고정 루트 위반율: {k}", "값": round(v, 4)} for k, v in risk["viol_rates"].items() if k != "복귀 지각"]
                      + [
                       {"지표": "고정 루트 복귀 여유 중앙값(분)", "값": round(risk["slack_median"], 1)},
                       {"지표": "고정 루트 복귀 여유 하위 5%(분)", "값": round(risk["slack_p5"], 1)}])
save(val_df, "검증_1118_B.csv", index=False)

# 4) 분산 배정 vs 전원 같은 루트 (같은 배 6그룹, 10분 간격 하선, 30분 안 겹침 1그룹당 +k분) — k 민감도 4/8/12
FAST = os.environ.get("FAST") == "1"   # 1이면 분산·골목·서사(오래 걸림) 생략, 기존 CSV 유지
disp_rows, disp_plans, d8 = [], None, []
for k in ([] if FAST else [4.0, 8.0]):
    plans = P.dispersion(S1, groups=6, crowd_add=k)
    d_ev = P.joint_eval(plans)
    s_ev = P.joint_eval(P.same_route_plans(S1, best[S1.name]["route"], groups=6, crowd_add=k))
    if k == 8.0:
        disp_plans, d8, s8 = plans, d_ev, s_ev
    for label, ev in [("전원 같은 루트", s_ev), ("분산 배정", d_ev)]:
        disp_rows.append({"겹침당 추가대기(분)": k, "배정": label,
                          "그룹 평균 줄대기(분)": round(np.mean([e["queue_min"] for e in ev]), 1),
                          "최대 줄대기(분)": max(e["queue_min"] for e in ev),
                          "복귀 지각 그룹": sum(e["violations"]["복귀 지각"] for e in ev),
                          "규칙 위반 그룹": sum(not e["feasible"] for e in ev),
                          "공동평가 수렴": ev[0]["converged"]})
disp_df = pd.DataFrame(disp_rows)
if not FAST:
  save(disp_df, "분산효과_1118_B.csv", index=False)
  save(pd.DataFrame([{"그룹": i + 1, "출발": fmt(S1.start + 10 * i), "루트": " → ".join(e["names"]),
                    "줄대기(분)": e["queue_min"], "복귀": fmt(e["return_min"]), "위반 없음": e["feasible"]}
                   for i, e in enumerate(d8)]), "분산배정_1118_B.csv", index=False)

# 5) 확산 지표(모델): 원도심(중·동·영도구) 밖 노드 지출 비중
def far_share(routes):
    tot = sum(P.A[n]["price_krw"] for r in routes for n in r)
    far = sum(P.A[n]["price_krw"] for r in routes for n in r if P.is_far(n))
    return round(far / max(1, tot) * 100, 1)
spread_df = pd.DataFrame([{"대상": sc.name, "원도심 밖 지출비중%": far_share([best[sc.name]["route"]])} for sc in SCEN]
                         + ([] if FAST else [{"대상": "S1 분산 배정(규칙 준수 그룹만)", "원도심 밖 지출비중%": far_share([e["route"] for e in d8 if e["feasible"]])}]))
save(spread_df, "확산지수_모델_1118_B.csv", index=False)

# 6) 추천빈도 지수 = 팀 부산성 점수 × 모델 추천빈도 (방문확률이 아님)
#    추천빈도 = (S1 재최적화 20회 포함률 + S1 분산 6그룹 포함률) / 2  (FAST면 재최적화 포함률만)
d8ok = [e for e in d8 if e["feasible"]]   # 규칙 위반 그룹은 추천빈도에서 제외
disp_rate = pd.Series([n for e in d8ok for n in e["route"]], dtype=object).value_counts() / max(1, len(d8ok))
idx = nodes[~nodes["category"].str.startswith("터미널")][["node_id", "name_ko", "gu", "demand_score"]].copy()
idx["북항거리km"] = idx["node_id"].map(lambda n: round(P.dist_from("D1", n), 2))
idx["추천빈도"] = idx["node_id"].map(lambda n: round(sens["node_freq"].get(n, 0) if FAST else (sens["node_freq"].get(n, 0) + disp_rate.get(n, 0)) / 2, 3))
idx["추천빈도지수"] = (idx["demand_score"] * idx["추천빈도"]).round(1)
idx = idx.sort_values("추천빈도지수", ascending=False)
save(idx, "추천빈도지수_1118_B.csv", index=False)

fc_df = story_df = pd.DataFrame()
if not FAST:
    # 7) 골목 방문 시나리오: 2026-05-08 실제 2척(실적 신고 기준). 선박별 하선·마감 시각, 그룹 크기 반영,
    #    두 배의 모든 그룹을 같은 혼잡 규칙으로 공동 평가한 '최종 일정'으로 집계. 상륙률 80%·앱 이용 10%는 가정.
    #    두 배의 선석(북항크루즈터미널 1선석, 국제여객터미널 14선석)은 모두 D1 좌표로 근사.
    SHIPS = [("SPECTRUM OF THE SEAS", 5242, H(6, 23), H(19, 15)), ("COSTA SERENA", 2589, H(11, 30), H(21))]
    LAND, APP, NG = 0.8, 0.10, 4
    all_plans = []
    for ship, pax, arr, dep in SHIPS:
        size = pax * LAND * APP / NG
        for s_, route, tl, _ in P.dispersion(Scenario(ship, "D1", arr + 90, dep - 60), groups=NG, size=size):
            all_plans.append((s_, route, tl, size))
    fin = P.joint_eval(all_plans)
    fc, ok_people, fail_people = {}, 0.0, 0.0
    for (s_, route, tl, size), ev in zip(all_plans, fin):
        if ev["feasible"] and ev["converged"]:   # 비수렴 = 실패로 집계
            ok_people += size
            for n, s0 in ev["visits"]:
                fc[(P.A[n]["name_ko"], int(s0 // 60))] = fc.get((P.A[n]["name_ko"], int(s0 // 60)), 0) + size
        else:
            fail_people += size
    fc_df = pd.Series(fc).round(0).rename("명").reset_index()
    fc_df.columns = ["골목·가게", "시(줄 서기)", "명"]
    fc_df = fc_df.pivot_table(index="골목·가게", columns="시(줄 서기)", values="명", fill_value=0)
    fc_df.loc["(참고) 규칙 위반으로 제외된 그룹 인원"] = 0
    fc_df.loc["(참고) 규칙 위반으로 제외된 그룹 인원", fc_df.columns[0]] = round(fail_people)
    save(fc_df, "골목방문시나리오_20260508_B.csv")

    # 8) 서사 루트 검증: C의 '피란수도의 한 끼'를 S1에서 실제로 걸으면?
    name2id = {P.A[n]["name_ko"]: n for n in P.cands}
    pick = lambda kw: next(n for nm, n in name2id.items() if kw in nm)
    story = [pick("국제시장"), pick("부평깡통"), pick("밀면"), pick("돼지국밥(이바구"), pick("흰여울")]
    S7 = Scenario("7시간 예산(08:30~15:30)", "D1", H(8, 30), H(16))
    srows = []
    for sc in [S1, S7]:
        ev = P.evaluate(story, sc)
        srows.append({"예산": sc.name, "루트": "피란수도의 한 끼(서사 순서)", "목적함수": ev["objective"],
                      "줄대기(분)": ev["queue_min"], "복귀": fmt(ev["return_min"]),
                      "위반": {k: v for k, v in ev["violations"].items() if v} or "없음"})
    story_df = pd.DataFrame(srows + [
                             {"예산": S1.name, "루트": "S1 최적(OPTW)", "목적함수": best[S1.name]["objective"],
                              "줄대기(분)": best[S1.name]["queue_min"], "복귀": fmt(best[S1.name]["return_min"]), "위반": "없음"}])
    save(story_df, "서사루트검증_1118_B.csv", index=False)

# ---------- 그림 ----------
g1 = res[(res["시나리오"] == S1.name) & (res["순위"].isin(["1", "탐욕법(같은 제약)"]))].set_index("순위")
nv = naive_df.iloc[0]
fig, ax = plt.subplots(1, 2, figsize=(12.5, 4.4))
labels = ["제약 무시 계획", "탐욕법(같은 제약)", "OPTW 1위"]
vals = [None, g1.loc["탐욕법(같은 제약)", "목적함수"], g1.loc["1", "목적함수"]]
ax[0].bar(labels[1:], vals[1:], color=["#9aa5b1", "#1f3b63"])
for i, v in enumerate(vals[1:]):
    ax[0].text(i, v + 5, f"{v:.0f}점", ha="center")
ax[0].set_ylim(0, max(vals[1:]) * 1.2)
viol = sum(int(nv[c]) for c in nv.index if str(c).startswith("위반:"))
ax[0].set_title(f"S1 목적함수 비교 (제약 무시 계획: {int(nv['방문 수'])}곳, 규칙 위반 {viol}건, 복귀 {nv['복귀']})", fontsize=10)
sub = (disp_df if not FAST else pd.read_csv(D / "분산효과_1118_B.csv"))
sub = sub[sub["겹침당 추가대기(분)"] == 8.0]
ax[1].bar(sub["배정"], sub["그룹 평균 줄대기(분)"], color=["#9aa5b1", "#e07a2f"])
for i, (v, late) in enumerate(zip(sub["그룹 평균 줄대기(분)"], sub["복귀 지각 그룹"])):
    ax[1].text(i, v + 3, f"{v:.0f}분 / 지각 {late}그룹", ha="center")
ax[1].set_ylim(0, sub["그룹 평균 줄대기(분)"].max() * 1.2)
ax[1].set_title("같은 배 6그룹(10분 간격, 100명씩): 그룹 평균 줄대기 (겹침 100명당 +8분 가정)", fontsize=10)
plt.tight_layout(); plt.savefig(F / "그림6_기준선비교_분산효과.png", dpi=200); plt.close()

top10 = idx.head(10).iloc[::-1]
plt.figure(figsize=(8, 4.5))
plt.barh(top10["name_ko"], top10["추천빈도지수"], color="#1f3b63")
plt.title("추천빈도 지수 상위 10 (수요점수 × 모델 추천빈도)"); plt.xlabel("지수")
plt.tight_layout(); plt.savefig(F / "그림7_추천빈도지수.png", dpi=200); plt.close()

try:
    import folium
    colors = ["#1f3b63", "#e07a2f", "#2e8b57", "#8e44ad"]
    fmap = folium.Map(location=[35.105, 129.04], zoom_start=13, tiles="CartoDB positron")
    for d in ["D1", "D2"]:
        folium.Marker([P.A[d]["lat"], P.A[d]["lon"]], tooltip=P.A[d]["name_ko"],
                      icon=folium.Icon(color="black", icon="ship", prefix="fa")).add_to(fmap)
    for c, sc in zip(colors, SCEN[:4]):
        r = best[sc.name]
        fg = folium.FeatureGroup(name=sc.name)
        folium.PolyLine([[P.A[n]["lat"], P.A[n]["lon"]] for n in [sc.depot] + r["route"] + [sc.depot]],
                        color=c, weight=4, opacity=0.8).add_to(fg)
        for i, (n, a, idl, q, begin, end) in enumerate(r["timeline"], 1):
            folium.CircleMarker([P.A[n]["lat"], P.A[n]["lon"]], radius=9, color=c, fill=True,
                                tooltip=f"{i}. {P.A[n]['name_ko']} {fmt(begin)} (줄 {q:.0f}분)").add_to(fg)
        fg.add_to(fmap)
    folium.LayerControl().add_to(fmap)
    fmap.save(str(F / "루트지도_1118_B.html"))
except ImportError:
    pass

if __name__ == "__main__":
    pd.set_option("display.width", 250, "display.max_colwidth", 150)
    for t in [res, naive_df, val_df, disp_df, spread_df, idx.head(10), story_df, fc_df]:
        print(t.to_string(), "\n")
