You are a reviewer (read-only except for your report file). Project: Korean university ideathon "부산의 맛, 로컬에서 글로컬" — team project "크루즈 관광객 미식 루트 최적화" (Busan cruise passengers, ~7h ashore, food route via OPTW = orienteering problem with time windows). Working folder: C:\Users\PTY\Desktop\지산학아이디어톤

Read: README.md, 05_문서/수업코드_분석_우리가_쓸것.md, 03_코드/cruise_route_optw.py, 03_코드/run_B_model.py, 03_코드/analysis_A_cruise_schedule.py, 02_정제데이터/*.csv and *.md, 01_원천데이터/출처목록.md and port_comparison.csv, 05_문서/서사카드_1118_C.md. Judging criteria (20 pts each): humanities interpretation, social-science verification, industrial-math modeling (fit, reproducibility, index usefulness), region-industry-academia link & feasibility, completeness.

Do a LIGHT but sharp review. Report the top issues only (max 12), ranked by severity, each with: file:line (if code), the problem, a concrete failure/consequence, and a suggested fix. Focus on:
1. Correctness bugs in the OPTW solver (branch-and-bound bound admissibility, constraints: time windows, stomach/digestion, meal gap/meal windows, return deadline, top-k recording), the greedy baseline fairness, robustness/dispersion logic, index definitions (CFAI, spread index), merchant forecast math.
2. Data/claim integrity: any number used without a source, mismatch between sources (e.g. 2025 passengers 246,584 vs 257,000), estimated values presented as facts, encoding/reproducibility issues (Colab: only pandas/numpy/scipy/matplotlib/seaborn/folium/openpyxl).
3. Whether the analysis actually supports the story (7h ashore, '부산 패싱', funnel leaks, dispersion).
You may run `python 03_코드/analysis_A_cruise_schedule.py` (fast). Do NOT run run_B_model.py (slow, ~10 min) — read its outputs in 02_정제데이터 instead.
Do not edit any project file. Write your report in Korean to 05_문서/review/REVIEW_FILE (create it), then finish.
