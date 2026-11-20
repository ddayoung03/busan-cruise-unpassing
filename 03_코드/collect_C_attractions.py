"""C. 볼거리 수요점수: '부산 여행' 영상의 외국인 댓글에서 명소 언급 수를 센다 (collect_C_youtube.py와 같은 방식)

음식 댓글(food tour 영상)에는 명소 언급이 거의 없어(감천 6·광안리 7·나머지 0~2) 여행 영상 댓글을 따로 모은다.
점수 = 50 + 50·ln(1+m)/ln(1+M)  (M = 이 자료 안 최다 언급) → 음식 수요점수와 같은 식·같은 50~100 범위.
  ※ 음식·볼거리는 서로 다른 영상 묶음 안에서의 상대 점수다(두 묶음 사이의 절대 비교는 아님).
키: .ent 의 youtubeapikey. 작성자 이름은 저장하지 않는다.
산출: 01_원천데이터/youtube/comments_travel_raw.csv, 02_정제데이터/명소언급_1119_C.csv
실행: python 03_코드/collect_C_attractions.py   (프로젝트 루트에서)
"""
import json
import math
import re
import urllib.parse
import urllib.request
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = re.search(r"youtubeapikey\s*=\s*(\S+)", (ROOT / ".ent").read_text(encoding="utf-8")).group(1)
QUERIES = {"en": "Busan travel vlog", "zh": "釜山旅游", "ja": "釜山 観光"}
N_VIDEOS, MAX_PAGES = 10, 2
RAW = ROOT / "01_원천데이터/youtube/comments_travel_raw.csv"

# 명소 사전: 한국어 이름 → 영·중·일 표기(소문자 포함 검색)
ATTR = {
    "북항 친수공원": ["north port", "waterfront park", "bukhang", "北港", "親水公園", "亲水公园"],
    "용두산공원·부산타워": ["busan tower", "yongdusan", "龙头山", "龍頭山", "釜山塔", "釜山タワー", "竜頭山"],
    "감천문화마을": ["gamcheon", "甘川", "カムチョン"],
    "흰여울문화마을": ["huinnyeoul", "huinyeoul", "白浅滩", "白淺灘", "ヒンヨウル"],
    "40계단": ["40 steps", "40 stairs", "40阶", "40階段"],
    "보수동 책방골목": ["bosu", "book street", "宝水洞", "寶水洞", "古書店街", "旧书街"],
    "초량 이바구길": ["ibagu", "168 steps", "168 stairs", "168阶", "168階段", "草梁"],
    "해운대해수욕장": ["haeundae beach", "海云台海", "海雲台海", "ヘウンデビーチ", "海雲台ビーチ"],
    "광안리해수욕장": ["gwangalli", "gwangan", "广安里", "廣安里", "広安里", "クァンアンリ"],
    "태종대": ["taejongdae", "太宗台", "テジョンデ"],
    "송도해상케이블카": ["songdo", "松岛", "松島", "cable car", "缆车", "纜車", "ケーブルカー"],
}


def api(endpoint, **params):
    url = f"https://www.googleapis.com/youtube/v3/{endpoint}?" + urllib.parse.urlencode({**params, "key": KEY})
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.load(r)


def lang_of(t):
    if re.search(r"[぀-ヿ]", t):
        return "ja"
    if re.search(r"[가-힣]", t):
        return "ko"
    if re.search(r"[一-鿿]", t):
        return "zh"
    if re.search(r"[A-Za-z]{3}", t):
        return "en"
    return "other"


if not RAW.exists():
    rows = []
    for ql, q in QUERIES.items():
        vids = [i["id"]["videoId"] for i in api("search", part="snippet", q=q, type="video", maxResults=N_VIDEOS,
                                                relevanceLanguage=ql, order="relevance")["items"]]
        for v in vids:
            token = None
            for _ in range(MAX_PAGES):
                try:
                    res = api("commentThreads", part="snippet", videoId=v, maxResults=100, textFormat="plainText",
                              **({"pageToken": token} if token else {}))
                except Exception:   # 댓글 비활성 영상
                    break
                for it in res.get("items", []):
                    t = it["snippet"]["topLevelComment"]["snippet"]["textDisplay"]
                    rows.append({"query": ql, "video": v, "lang": lang_of(t), "text": t.replace("\n", " ")})
                token = res.get("nextPageToken")
                if not token:
                    break
    pd.DataFrame(rows).drop_duplicates(["video", "text"]).to_csv(RAW, index=False, encoding="utf-8-sig")

raw = pd.read_csv(RAW)
raw = raw[raw["lang"].isin(["en", "zh", "ja"])]
texts = raw["text"].fillna("").astype(str).str.lower()
out = []
for name, al in ATTR.items():
    hit = raw[texts.apply(lambda s: any(a.lower() in s for a in al))]
    out.append({"name_ko": name, "mentions": len(hit), **{f"n_{L}": int((hit["lang"] == L).sum()) for L in ["en", "zh", "ja"]}})
df = pd.DataFrame(out)
M = df["mentions"].max()
df["demand_score"] = (50 + 50 * df["mentions"].apply(lambda m: math.log1p(m)) / math.log1p(M)).round(1)
df.to_csv(ROOT / "02_정제데이터/명소언급_1119_C.csv", index=False, encoding="utf-8-sig")
print(f"댓글 {len(raw)}개 (영 {sum(raw.lang == 'en')}, 중 {sum(raw.lang == 'zh')}, 일 {sum(raw.lang == 'ja')}), 영상 {raw.video.nunique()}개")
print(df.sort_values("mentions", ascending=False).to_string(index=False))
