"""B. 부산광역시_부산맛집정보 서비스(공공데이터포털 15063472, 부산시·visitbusan) 전체 수집

키: 프로젝트 루트 .ent 의 'datagokrkey = ...' (산출물에 키를 남기지 않는다)
산출: 01_원천데이터/data.go.kr/busan_food_api/busan_food_{kr,en,ja,chs}.csv
실행: python 03_코드/collect_B_busanfood.py   (프로젝트 루트에서)
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = re.search(r"datagokrkey\s*=\s*(\S+)", (ROOT / ".ent").read_text(encoding="utf-8")).group(1)
OUT = ROOT / "01_원천데이터/data.go.kr/busan_food_api"
OUT.mkdir(parents=True, exist_ok=True)

for lang in ["Kr", "En", "Ja", "Chs"]:
    rows, page = [], 1
    while True:
        url = f"https://apis.data.go.kr/6260000/FoodService/getFood{lang}?" + urllib.parse.urlencode(
            {"serviceKey": KEY, "pageNo": page, "numOfRows": 500, "resultType": "json"})
        body = json.load(urllib.request.urlopen(url, timeout=60))[f"getFood{lang}"]
        items = body.get("item", [])
        rows += items
        if not items or len(rows) >= int(body.get("totalCount", 0)):
            break
        page += 1
    df = pd.DataFrame(rows).drop(columns=["MAIN_IMG_NORMAL", "MAIN_IMG_THUMB"], errors="ignore")
    df.to_csv(OUT / f"busan_food_{lang.lower()}.csv", index=False, encoding="utf-8-sig")
    print(lang, len(df))
