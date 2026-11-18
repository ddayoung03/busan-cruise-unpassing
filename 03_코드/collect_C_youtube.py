"""C. YouTube 댓글로 언어권별 부산 메뉴 언급 비교 (스무딩 로그승산비, 1주차 수업 방식)

키: 프로젝트 루트 .ent 파일의 'youtubeapikey = ...' (코드·산출물에 키를 남기지 않는다)
수집: YouTube Data API v3 search(언어별 검색어 상위 영상) → commentThreads(영상당 최대 200개)
      작성자 이름은 저장하지 않는다. 댓글 언어는 문자로 판정(가나=ja, 한자=zh, 라틴=en, 한글=제외).
산출: 01_원천데이터/youtube/comments_raw.csv(영상ID·언어·본문), 02_정제데이터/메뉴언급_언어별_1118_C.csv
실행: python 03_코드/collect_C_youtube.py   (프로젝트 루트에서)
"""
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
KEY = re.search(r"=\s*(\S+)", (ROOT / ".ent").read_text(encoding="utf-8")).group(1)
QUERIES = {"en": "Busan food tour", "zh": "釜山美食", "ja": "釜山 グルメ"}
N_VIDEOS, MAX_PAGES = 10, 2


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

raw = pd.DataFrame(rows).drop_duplicates(["video", "text"])
(ROOT / "01_원천데이터/youtube").mkdir(parents=True, exist_ok=True)
raw.to_csv(ROOT / "01_원천데이터/youtube/comments_raw.csv", index=False, encoding="utf-8-sig")

menu = pd.read_csv(ROOT / "02_정제데이터/메뉴사전_1118_C.csv")
col = {"en": "en_aliases", "zh": "zh_aliases", "ja": "ja_aliases"}
cnt = {}
for L, c in col.items():
    texts = raw.loc[raw["lang"] == L, "text"].str.lower()
    for _, m in menu.iterrows():
        al = [a.strip().lower() for a in str(m[c]).split("|") if a.strip() and a.strip() != "nan"]
        cnt[(m["item_ko"], L)] = int(texts.apply(lambda t: any(a in t for a in al)).sum()) if al else 0
df = pd.Series(cnt).unstack().reindex(columns=["en", "zh", "ja"]).fillna(0).astype(int)
n = raw["lang"].value_counts()


def log_odds(a, b, alpha=1.0):
    V = len(df)
    return np.log(((df[a] + alpha) / (df[a].sum() + V * alpha)) / ((df[b] + alpha) / (df[b].sum() + V * alpha))).round(3)


df["log_odds_en_vs_zh"] = log_odds("en", "zh")
df["log_odds_en_vs_ja"] = log_odds("en", "ja")
df.loc["(댓글 수)"] = [n.get("en", 0), n.get("zh", 0), n.get("ja", 0), np.nan, np.nan]
df.to_csv(ROOT / "02_정제데이터/메뉴언급_언어별_1118_C.csv", encoding="utf-8-sig")
print(raw["lang"].value_counts().to_string(), "\n")
print(df.to_string())
