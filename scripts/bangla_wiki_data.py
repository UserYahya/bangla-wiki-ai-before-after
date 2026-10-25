"""
Bangla Wikimedia data pull: before vs after AI
===============================================

Pulls monthly metrics for Bangla Wikipedia, its sister projects and a few
comparison wikis from the Wikimedia Analytics API, plus internet-user data
for Bangladesh and India from the World Bank. It then builds summary tables
ready for slides.

Usage:
    pip install requests pandas
    python scripts/bangla_wiki_data.py [output-folder]

Wikimedia asks API users to identify themselves: set WIKI_CONTACT to your
email address or user page URL before running.

Output folder (default: data/ next to scripts/):
    raw/        one CSV per metric, one column per wiki, one row per month
    derived/    bot share, mobile share, edits per new user
    summary/    period_summary.csv, same_months_by_year.csv, headline_gap.csv,
                internet_users.csv
"""
import datetime as dt
import os
import sys
import time

import pandas as pd
import requests

# ---------------------------------------------------------------- settings
CONTACT = os.environ.get("WIKI_CONTACT", "https://bn.wikipedia.org/")
HEADERS = {"User-Agent": f"BanglaWikimediaResearch/1.0 ({CONTACT})"}
BASE = "https://wikimedia.org/api/rest_v1/metrics"
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
    os.path.dirname(os.path.abspath(__file__)), os.pardir, "data")

# Bangla projects (a project that doesn't exist is simply skipped)
FOCUS = [
    "bn.wikipedia.org",
    "bn.wikisource.org",
    "bn.wiktionary.org",
    "bn.wikibooks.org",
    "bn.wikiquote.org",
    "bn.wikivoyage.org",
]
# Comparison wikis (other Indic languages + English as the global reference)
COMPARE = [
    "hi.wikipedia.org",
    "ta.wikipedia.org",
    "ml.wikipedia.org",
    "te.wikipedia.org",
    "mr.wikipedia.org",
    "ur.wikipedia.org",
    "en.wikipedia.org",
]
ALL_WIKIS = FOCUS + COMPARE

START = "20160101"
END_DATE = dt.date.today().replace(day=1)          # first day of current month
END = END_DATE.strftime("%Y%m%d")
LAST_COMPLETE = END_DATE - dt.timedelta(days=1)    # last full month in the data

# Periods for the before/after AI comparison (inclusive, YYYY-MM).
# Jan-Nov 2022 is deliberately left out as a transition year.
PERIODS = {
    "pre_ai_2017_2019": ("2017-01", "2019-12"),
    "covid_2020_2021": ("2020-01", "2021-12"),
    "early_ai_2022-12_2024-06": ("2022-12", "2024-06"),
    "ai_mainstream_2024-07_now": ("2024-07", "2099-12"),
}

# name -> (API path, value key, results nested inside items[0]?)
METRICS = {
    # Readers
    "pageviews_user": ("/pageviews/aggregate/{w}/all-access/user/monthly/{s}00/{e}00", "views", False),
    "pageviews_spider": ("/pageviews/aggregate/{w}/all-access/spider/monthly/{s}00/{e}00", "views", False),
    "pageviews_automated": ("/pageviews/aggregate/{w}/all-access/automated/monthly/{s}00/{e}00", "views", False),
    "pageviews_desktop": ("/pageviews/aggregate/{w}/desktop/user/monthly/{s}00/{e}00", "views", False),
    "pageviews_mobile_web": ("/pageviews/aggregate/{w}/mobile-web/user/monthly/{s}00/{e}00", "views", False),
    "pageviews_mobile_app": ("/pageviews/aggregate/{w}/mobile-app/user/monthly/{s}00/{e}00", "views", False),
    "unique_devices": ("/unique-devices/{w}/all-sites/monthly/{s}/{e}", "devices", False),
    # Contributors
    # The API buckets editors by activity; "active" (5+ edits) = 5..24 + 25..99 + 100..
    "editors_5_24": ("/editors/aggregate/{w}/user/content/5..24-edits/monthly/{s}/{e}", "editors", True),
    "editors_25_99": ("/editors/aggregate/{w}/user/content/25..99-edits/monthly/{s}/{e}", "editors", True),
    "very_active_editors_100plus": ("/editors/aggregate/{w}/user/content/100..-edits/monthly/{s}/{e}", "editors", True),
    "new_registered_users": ("/registered-users/new/{w}/monthly/{s}/{e}", "new_registered_users", True),
    "edits_user_content": ("/edits/aggregate/{w}/user/content/monthly/{s}/{e}", "edits", True),
    # Content
    "new_articles_all": ("/edited-pages/new/{w}/all-editor-types/content/monthly/{s}/{e}", "new_pages", True),
    "new_articles_by_humans": ("/edited-pages/new/{w}/user/content/monthly/{s}/{e}", "new_pages", True),
}

# Metrics that go into the summary tables
SUMMARY_METRICS = [
    "pageviews_user", "unique_devices", "bot_share_pct", "mobile_share_pct",
    "active_editors_5plus", "very_active_editors_100plus", "new_registered_users",
    "edits_user_content", "edits_per_new_user", "new_articles_by_humans",
]


# ---------------------------------------------------------------- helpers
def short(w):
    """bn.wikipedia.org -> bnwiki, bn.wikisource.org -> bnwikisource"""
    lang, proj = w.split(".")[:2]
    return lang + ("wiki" if proj == "wikipedia" else proj)


def month_key(ts):
    """'2016010100' or '2016-01-01T00:00:00.000Z' -> '2016-01'"""
    d = ts.replace("-", "")[:6]
    return f"{d[:4]}-{d[4:6]}"


def fetch(path, key, nested):
    url = BASE + path
    for attempt in range(5):
        try:
            r = requests.get(url, headers=HEADERS, timeout=90)
        except requests.RequestException as e:
            print(f"    network error ({e}), retrying...")
            time.sleep(3)
            continue
        if r.status_code == 200:
            items = r.json().get("items", [])
            rows = (items[0].get("results", []) if items else []) if nested else items
            return {month_key(row["timestamp"]): row[key] for row in rows}
        if r.status_code == 404:          # no data / project doesn't exist
            return {}
        if r.status_code == 429 or r.status_code >= 500:   # rate limited / server busy
            time.sleep(10 * (attempt + 1))
            continue
        print(f"    HTTP {r.status_code}: {url}")
        return {}
    print(f"    gave up: {url}")
    return {}


def world_bank(country, indicator):
    url = f"https://api.worldbank.org/v2/country/{country}/indicator/{indicator}"
    try:
        r = requests.get(url, params={"format": "json", "date": "2015:2026", "per_page": 100},
                         headers=HEADERS, timeout=60)
        js = r.json()
    except Exception as e:
        print(f"    World Bank error: {e}")
        return {}
    if len(js) < 2 or not js[1]:
        return {}
    return {int(x["date"]): x["value"] for x in js[1] if x["value"] is not None}


def save(df, sub, name):
    os.makedirs(os.path.join(OUT, sub), exist_ok=True)
    df.to_csv(os.path.join(OUT, sub, f"{name}.csv"))


# ---------------------------------------------------------------- steps
def collect():
    data = {}
    for name, (tmpl, key, nested) in METRICS.items():
        print(f"Fetching {name} ...")
        cols = {}
        for w in ALL_WIKIS:
            vals = fetch(tmpl.format(w=w, s=START, e=END), key, nested)
            if vals:
                cols[short(w)] = vals
            time.sleep(0.3)               # be polite to the API
        df = pd.DataFrame(cols).sort_index()
        df.index.name = "month"
        save(df, "raw", name)
        data[name] = df
    return data


def derive(d):
    out = {}
    bots = d["pageviews_spider"].add(d["pageviews_automated"], fill_value=0)
    total = d["pageviews_user"].add(bots, fill_value=0)
    # NOTE: the "automated" category only exists from April 2020, so bot share
    # before that date is understated. Compare bot share from 2020-05 onwards.
    out["bot_share_pct"] = bots / total * 100
    mobile = d["pageviews_mobile_web"].add(d["pageviews_mobile_app"], fill_value=0)
    out["mobile_share_pct"] = mobile / d["pageviews_user"] * 100
    # Christophe Henner's concentration metric, using human content edits
    out["edits_per_new_user"] = d["edits_user_content"] / d["new_registered_users"]
    out["active_editors_5plus"] = (d["editors_5_24"]
                                   .add(d["editors_25_99"], fill_value=0)
                                   .add(d["very_active_editors_100plus"], fill_value=0))
    for name, df in out.items():
        df = df.replace([float("inf"), -float("inf")], pd.NA).round(2)
        df.index.name = "month"
        out[name] = df
        save(df, "derived", name)
    return out


def period_summary(metrics):
    rows = []
    names = list(PERIODS)
    for m in SUMMARY_METRICS:
        df = metrics.get(m)
        if df is None:
            continue
        for col in df.columns:
            s = pd.to_numeric(df[col], errors="coerce").dropna()
            row = {"metric": m, "wiki": col}
            for p, (a, b) in PERIODS.items():
                v = s[(s.index >= a) & (s.index <= b)]
                row[p] = round(v.mean(), 2) if len(v) else None
            first, last = row[names[0]], row[names[-1]]
            row["change_pre_ai_to_now_pct"] = (
                round((last - first) / first * 100, 1) if first and last is not None else None
            )
            row["change_early_ai_to_now_pct"] = (
                round((last - row[names[2]]) / row[names[2]] * 100, 1)
                if row[names[2]] and last is not None else None
            )
            rows.append(row)
    df = pd.DataFrame(rows)
    save(df.set_index(["metric", "wiki"]), "summary", "period_summary")
    return df


def same_months(metrics):
    """Average of the same calendar months (Jan..last complete month) per year."""
    m_max = LAST_COMPLETE.month
    frames = []
    for m in SUMMARY_METRICS:
        df = metrics.get(m)
        if df is None:
            continue
        idx = pd.to_datetime(df.index, format="%Y-%m")
        sub = df[idx.month <= m_max].copy()
        sub["year"] = pd.to_datetime(sub.index, format="%Y-%m").year
        yearly = sub.apply(pd.to_numeric, errors="coerce").groupby("year").mean().round(2).T
        yearly.insert(0, "metric", m)
        frames.append(yearly)
    df = pd.concat(frames)
    df.index.name = "wiki"
    save(df, "summary", f"same_months_by_year_jan-{LAST_COMPLETE.strftime('%b').lower()}")
    return df


def internet_and_gap(metrics):
    print("Fetching World Bank internet data ...")
    rows = {}
    for c in ["BGD", "IND"]:
        pct = world_bank(c, "IT.NET.USER.ZS")
        pop = world_bank(c, "SP.POP.TOTL")
        for y in sorted(set(pct) & set(pop)):
            rows.setdefault(y, {})[f"{c}_internet_pct"] = round(pct[y], 1)
            rows.setdefault(y, {})[f"{c}_internet_users"] = round(pct[y] / 100 * pop[y])
    net = pd.DataFrame.from_dict(rows, orient="index").sort_index()
    net.index.name = "year"
    save(net, "summary", "internet_users")

    # Headline gap: Bangladesh internet users vs Bangla Wikipedia human pageviews,
    # both indexed to 2016 = 100 (pageviews use same-month yearly averages).
    pv = metrics["pageviews_user"].get("bnwiki")
    if pv is None or net.empty or "BGD_internet_users" not in net:
        print("    Not enough data for the headline gap table.")
        return
    idx = pd.to_datetime(pv.index, format="%Y-%m")
    pv = pv[idx.month <= LAST_COMPLETE.month]
    pv_year = pv.groupby(pd.to_datetime(pv.index, format="%Y-%m").year).mean()
    gap = pd.DataFrame({
        "bnwiki_human_pageviews_avg": pv_year.round(0),
        "BGD_internet_users": net["BGD_internet_users"],
    })
    if 2016 in gap.index:
        gap["pageviews_index"] = (gap.iloc[:, 0] / gap.loc[2016].iloc[0] * 100).round(1)
        gap["internet_index"] = (gap.iloc[:, 1] / gap.loc[2016].iloc[1] * 100).round(1)
        gap["gap_points"] = (gap["internet_index"] - gap["pageviews_index"]).round(1)
    gap.index.name = "year"
    save(gap, "summary", "headline_gap")


def main():
    print(f"Data window: {START} to {LAST_COMPLETE:%Y-%m} (last complete month)\n")
    raw = collect()
    derived = derive(raw)
    metrics = {**raw, **derived}
    period_summary(metrics)
    same_months(metrics)
    internet_and_gap(metrics)
    print(f"\nDone. Files are in {os.path.normpath(OUT)}")


if __name__ == "__main__":
    main()
