"""
Bangla Wikipedia: extra data for the "before and after AI" talk
===============================================================

Adds a few deeper cuts to bangla_wiki_data.py, all from public APIs:

    hourly_profile.csv      average views by hour of day (Bangladesh time) for
                            humans, automated bots and crawlers, 2019/2024/2026
    hourly_profile_by_access.csv  the same for desktop and mobile web, 2024/2026
    weekday_profile.csv     average daily human views by weekday
    top_articles_*.csv      most-read articles per month and per year
    cx_published_en_bn.csv  articles published with Content Translation (en -> bn)
    csd_ai_deletions.csv    deletions under speedy-deletion criterion S15
                            ("pages entirely created by AI", added 26 Aug 2025)
    ai_tagged_pages.csv     pages carrying the "AI-generated" maintenance tag
    readers_by_country.csv  human views by country (bucketed, rounded up)
    edits_by_editor_type.csv  monthly edits by humans, anonymous users and bots
    snapshot.json           article count, editors, admins, Growth mentors today

Usage:
    pip install requests pandas
    python scripts/extra_data.py [--out FOLDER] [--only STEP,STEP]

Set WIKI_CONTACT to your email address or user page URL before running.
Output folder default: data/extra/ next to scripts/. Steps: see STEPS at the end.
"""
import argparse
import calendar
import datetime as dt
import json
import os
import re
import time

import pandas as pd
import requests

# ---------------------------------------------------------------- settings
CONTACT = os.environ.get("WIKI_CONTACT", "https://bn.wikipedia.org/")
HEADERS = {"User-Agent": f"BanglaWikimediaResearch/1.0 ({CONTACT})"}
AQS = "https://wikimedia.org/api/rest_v1/metrics"
API = "https://bn.wikipedia.org/w/api.php"
PROJECT = "bn.wikipedia"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), os.pardir, "data", "extra")

TODAY = dt.date.today()
LAST_COMPLETE = TODAY.replace(day=1) - dt.timedelta(days=1)
RHYTHM_YEARS = [2019, 2024, LAST_COMPLETE.year]
BST = 6                                     # Bangladesh time = UTC+6, no DST

CSD_AI = "স১৫"                               # speedy deletion: page entirely made by an LLM
CSD_AI_ADDED = "2025-08-26"
AI_TAG = "টেমপ্লেট:কৃত্রিম বুদ্ধিমত্তা উৎপন্ন"
MENTOR_LIST = "MediaWiki:GrowthMentors.json"

# Titles in these namespaces (or these exact titles) are not articles
NON_ARTICLE = re.compile(
    r"^(বিশেষ|Special|উইকিপিডিয়া|Wikipedia|চিত্র|File|ব্যবহারকারী|User|টেমপ্লেট|Template|"
    r"বিষয়শ্রেণী|Category|সাহায্য|Help|প্রবেশদ্বার|Portal|মিডিয়াউইকি|MediaWiki|খসড়া|Draft|"
    r"মডিউল|Module|আলোচনা|Talk)[^:]*:")
SKIP_TITLES = {"প্রধান_পাতা", "-", "Main_Page"}


# ---------------------------------------------------------------- helpers
def get_json(url, params=None):
    for attempt in range(5):
        try:
            r = requests.get(url, params=params, headers=HEADERS, timeout=90)
        except requests.RequestException as e:
            print(f"    network error ({e}), retrying...")
            time.sleep(3)
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code == 404:
            return {}
        if r.status_code == 429 or r.status_code >= 500:   # rate limited / server busy
            time.sleep(10 * (attempt + 1))
            continue
        print(f"    HTTP {r.status_code}: {r.url}")
        return {}
    print(f"    gave up: {url}")
    return {}


def api(**params):
    params.update(format="json", formatversion="2")
    return get_json(API, params)


def months(year):
    last = LAST_COMPLETE.month if year == LAST_COMPLETE.year else 12
    return range(1, last + 1)


def save(df, name, index=False):
    os.makedirs(OUT, exist_ok=True)
    df.to_csv(os.path.join(OUT, f"{name}.csv"), index=index)


# ---------------------------------------------------------------- steps
def hourly_rhythm():
    """Humans sleep, bots don't: views by hour of day, Jan..last complete month."""
    print("Fetching hourly views ...")
    rows = []
    for year in RHYTHM_YEARS:
        for agent in ["user", "automated", "spider"]:
            for m in months(year):
                if m > LAST_COMPLETE.month:     # same months in every year
                    continue
                last = calendar.monthrange(year, m)[1]
                url = (f"{AQS}/pageviews/aggregate/{PROJECT}/all-access/{agent}/hourly/"
                       f"{year}{m:02d}0100/{year}{m:02d}{last:02d}23")
                for it in get_json(url).get("items", []):
                    ts = dt.datetime.strptime(it["timestamp"], "%Y%m%d%H")
                    rows.append({"year": year, "agent": agent, "month": m,
                                 "hour_bst": (ts.hour + BST) % 24, "views": it["views"]})
                time.sleep(0.2)
    df = pd.DataFrame(rows)
    profile = (df.groupby(["year", "agent", "hour_bst"])["views"].mean().round(0)
               .reset_index().rename(columns={"views": "avg_views"}))
    save(profile, "hourly_profile")
    summary = []
    for (year, agent), g in profile.groupby(["year", "agent"]):
        v = g.set_index("hour_bst")["avg_views"]
        night = v.loc[[2, 3, 4, 5]].mean()           # 2-6 am Bangladesh time
        summary.append({"year": year, "agent": agent,
                        "peak_hour_bst": int(v.idxmax()), "trough_hour_bst": int(v.idxmin()),
                        "trough_to_peak_pct": round(v.min() / v.max() * 100, 1),
                        "night_2_6am_to_daily_avg_pct": round(night / v.mean() * 100, 1)})
    save(pd.DataFrame(summary), "hourly_summary")


def hourly_by_access():
    """Same hourly profile split by desktop and mobile web, humans vs automated bots."""
    print("Fetching hourly views by access method ...")
    rows = []
    for year in [2024, LAST_COMPLETE.year]:
        for access in ["desktop", "mobile-web"]:
            for agent in ["user", "automated"]:
                for m in range(1, LAST_COMPLETE.month + 1):
                    last = calendar.monthrange(year, m)[1]
                    url = (f"{AQS}/pageviews/aggregate/{PROJECT}/{access}/{agent}/hourly/"
                           f"{year}{m:02d}0100/{year}{m:02d}{last:02d}23")
                    for it in get_json(url).get("items", []):
                        ts = dt.datetime.strptime(it["timestamp"], "%Y%m%d%H")
                        rows.append({"year": year, "access": access, "agent": agent,
                                     "hour_bst": (ts.hour + BST) % 24, "views": it["views"]})
                    time.sleep(0.2)
    df = pd.DataFrame(rows)
    profile = (df.groupby(["year", "access", "agent", "hour_bst"])["views"].mean().round(0)
               .reset_index().rename(columns={"views": "avg_views"}))
    save(profile, "hourly_profile_by_access")


def weekday_rhythm():
    print("Fetching daily views ...")
    rows = []
    for year in RHYTHM_YEARS:
        end = LAST_COMPLETE.replace(year=year)
        url = (f"{AQS}/pageviews/aggregate/{PROJECT}/all-access/user/daily/"
               f"{year}010100/{end:%Y%m%d}00")
        for it in get_json(url).get("items", []):
            day = dt.datetime.strptime(it["timestamp"][:8], "%Y%m%d")
            rows.append({"year": year, "weekday": day.strftime("%A"), "views": it["views"]})
    df = pd.DataFrame(rows)
    prof = df.groupby(["year", "weekday"])["views"].mean().round(0).reset_index()
    prof["pct_of_week_avg"] = (prof["views"] / prof.groupby("year")["views"].transform("mean")
                               * 100).round(1)
    save(prof, "weekday_profile")


def top_articles():
    print("Fetching monthly top articles ...")
    rows = []
    for year in range(2016, LAST_COMPLETE.year + 1):
        for m in months(year):
            url = f"{AQS}/pageviews/top/{PROJECT}/all-access/{year}/{m:02d}/all-days"
            items = get_json(url).get("items", [])
            for a in (items[0]["articles"] if items else []):
                t = a["article"]
                if t in SKIP_TITLES or NON_ARTICLE.match(t):
                    continue
                rows.append({"year": year, "month": m, "article": t.replace("_", " "),
                             "views": a["views"]})
            time.sleep(0.2)
    df = pd.DataFrame(rows)
    df["rank"] = df.groupby(["year", "month"])["views"].rank(ascending=False, method="first")
    save(df, "top_articles_monthly")
    # Yearly total = sum over the months in which the article made the monthly top list
    yearly = df.groupby(["year", "article"])["views"].sum().reset_index()
    yearly = yearly.sort_values(["year", "views"], ascending=[True, False])
    save(yearly.groupby("year").head(10), "top_articles_by_year")


def cx_translations():
    print("Fetching Content Translation publications (en -> bn) ...")
    rows, offset = [], 0
    while True:
        js = api(action="query", list="cxpublishedtranslations",
                 **{"from": "en"}, to="bn", limit=500, offset=offset)
        batch = js.get("result", {}).get("translations", [])
        for t in batch:
            st = t.get("stats") or {}
            rows.append({"published": t["publishedDate"][:8], "title": t["targetTitle"],
                         "source_title": t["sourceTitle"], "mt": st.get("mt"),
                         "human": st.get("human"), "any": st.get("any")})
        if len(batch) < 500:
            break
        offset += 500
        time.sleep(0.3)
    df = pd.DataFrame(rows)
    df["main_namespace"] = ~df["title"].str.contains(":", regex=False)
    save(df, "cx_published_en_bn")


def csd_ai_deletions():
    print("Fetching deletions under the AI speedy-deletion criterion ...")
    pattern = re.compile(r"স১৫|g15|জি১৫", re.I)
    rows, cont = [], {}
    while True:
        js = api(action="query", list="logevents", letype="delete", leaction="delete/delete",
                 leend=f"{CSD_AI_ADDED}T00:00:00Z", lelimit="max",
                 leprop="timestamp|title|comment", **cont)
        for ev in js.get("query", {}).get("logevents", []):
            if pattern.search(ev.get("comment") or ""):
                rows.append({"timestamp": ev["timestamp"], "title": ev["title"],
                             "comment": ev.get("comment", "")})
        if "continue" not in js:
            break
        cont = js["continue"]
    save(pd.DataFrame(rows, columns=["timestamp", "title", "comment"]), "csd_ai_deletions")

    tagged, cont = [], {}
    while True:
        js = api(action="query", list="embeddedin", eititle=AI_TAG, einamespace="0|118",
                 eilimit="max", **cont)
        tagged += [p["title"] for p in js.get("query", {}).get("embeddedin", [])]
        if "continue" not in js:
            break
        cont = js["continue"]
    save(pd.DataFrame({"title": tagged}), "ai_tagged_pages")


def readers_by_country():
    print("Fetching readers by country ...")
    rows = []
    for year in [2024, LAST_COMPLETE.year]:
        for m in range(1, LAST_COMPLETE.month + 1):
            url = f"{AQS}/pageviews/top-by-country/{PROJECT}/all-access/{year}/{m:02d}"
            items = get_json(url).get("items", [])
            for c in (items[0]["countries"] if items else []):
                rows.append({"year": year, "month": m, "country": c["country"],
                             "views_ceil": c["views_ceil"]})
            time.sleep(0.2)
    save(pd.DataFrame(rows), "readers_by_country")


def edits_by_editor_type():
    print("Fetching edits by editor type ...")
    cols = {}
    end = TODAY.replace(day=1).strftime("%Y%m%d")
    for et in ["user", "anonymous", "group-bot", "name-bot"]:
        url = f"{AQS}/edits/aggregate/{PROJECT}.org/{et}/all-page-types/monthly/20160101/{end}"
        items = get_json(url).get("items", [])
        res = items[0]["results"] if items else []
        cols[et] = {r["timestamp"][:7]: r["edits"] for r in res}
    df = pd.DataFrame(cols).sort_index()
    df.index.name = "month"
    save(df, "edits_by_editor_type", index=True)


def snapshot():
    print("Taking today's snapshot ...")
    stats = api(action="query", meta="siteinfo", siprop="statistics")["query"]["statistics"]
    raw = requests.get("https://bn.wikipedia.org/w/index.php",
                       params={"title": MENTOR_LIST, "action": "raw"},
                       headers=HEADERS, timeout=60)
    mentors = len(json.loads(raw.text).get("Mentors", {})) if raw.ok else None
    snap = {"date": TODAY.isoformat(), "articles": stats["articles"], "edits": stats["edits"],
            "registered_users": stats["users"], "active_users_30d": stats["activeusers"],
            "admins": stats["admins"], "growth_mentors": mentors}
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "snapshot.json"), "w", encoding="utf-8") as f:
        json.dump(snap, f, ensure_ascii=False, indent=2)


STEPS = {
    "snapshot": snapshot,
    "csd_ai_deletions": csd_ai_deletions,
    "edits_by_editor_type": edits_by_editor_type,
    "weekday_rhythm": weekday_rhythm,
    "hourly_rhythm": hourly_rhythm,
    "hourly_by_access": hourly_by_access,
    "readers_by_country": readers_by_country,
    "cx_translations": cx_translations,
    "top_articles": top_articles,
}


def main():
    global OUT
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    parser.add_argument("--out", default=OUT, help="output folder")
    parser.add_argument("--only", help="comma-separated steps to run (default: all)")
    args = parser.parse_args()
    OUT = args.out
    steps = args.only.split(",") if args.only else list(STEPS)
    print(f"Data window ends {LAST_COMPLETE:%Y-%m}; output: {OUT}\n")
    for name in steps:
        STEPS[name]()
    print("\nDone.")


if __name__ == "__main__":
    main()
