import os
import re
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source import config

CHANNELS = ["chat", "email", "voice", "social"]
MIN_PRIOR_WEEKS = 4      
MIN_SPIKE_TICKETS = 5    


SIGN_OFF = re.compile(r"(regards|thanks|thank you|sincerely|cheers)[,.!\s]+[A-Za-z]+\s*$", re.I)
ORDER_ID = re.compile(r"\bvr\d{5,}\b", re.I)
PHONE = re.compile(r"\b\d{10}\b")


def short_example(text):
    text = " ".join(str(text).split())
    text = SIGN_OFF.sub("", text)
    text = PHONE.sub("[phone]", ORDER_ID.sub("[order]", text)).strip()
    return text if len(text) <= 150 else text[:147] + "..."


def find_spikes(df, weeks):
    """spike = this week's count is above (mean + 2 x std) of all earlier weeks, and at least 5 tickets"""
    counts = df.groupby(["week_start", "product_sku"]).size().unstack(fill_value=0)
    counts = counts.reindex(weeks, fill_value=0)
    spikes = {}
    for i, week in enumerate(weeks):
        if i < MIN_PRIOR_WEEKS:
            spikes[week] = ""
            continue
        before = counts.iloc[:i]
        limit = before.mean() + 2 * before.std()
        flagged = counts.iloc[i][(counts.iloc[i] > limit) & (counts.iloc[i] >= MIN_SPIKE_TICKETS)]
        spikes[week] = "; ".join(f"{sku} ({n})" for sku, n in flagged.sort_values(ascending=False).items())
    return spikes


def build_digest(analyzed):
    df = analyzed[~analyzed["parse_failed"].astype(bool)].copy()
    df["week_start"] = pd.to_datetime(df["week_start"])
    df["created_at"] = pd.to_datetime(df["created_at"])

    weeks = list(pd.date_range(df["week_start"].min(), df["week_start"].max(), freq="7D"))
    first_day = df["created_at"].min().normalize()
    last_day = df["created_at"].max().normalize()

    cat_counts = df.groupby(["week_start", "category"]).size().unstack(fill_value=0).reindex(weeks, fill_value=0)
    spikes = find_spikes(df, weeks)

    rows = []
    for week in weeks:
        wk = df[df["week_start"] == week]
        if wk.empty:
            continue
        
        partial = week < first_day or week + pd.Timedelta(days=6) > last_day
        week_info = {
            "week_start": week.date(),
            "partial_week": partial,
            "week_tickets": len(wk),
            "negative_pct": round((wk["sentiment"] == "negative").mean() * 100, 1),
            "spike_skus": spikes[week],
        }
        for channel in CHANNELS:
            part = wk[wk["channel"] == channel]
            week_info[f"contacted_before_pct_{channel}"] = (
                round(part["already_contacted_before"].astype(bool).mean() * 100, 1) if len(part) else None)

        top = cat_counts.loc[week].drop(labels=["unclear"], errors="ignore")
        top = top.sort_values(ascending=False).head(5)
        top = top[top > 0]      
        prev_week = week - pd.Timedelta(days=7)
        for rank, (category, n) in enumerate(top.items(), start=1):
            prev = int(cat_counts.loc[prev_week, category]) if prev_week in cat_counts.index and category in cat_counts.columns else None
            example = wk[wk["category"] == category]["customer_message"].iloc[0]
            rows.append({**week_info, "rank": rank, "category": category, "tickets": int(n),
                         "prev_week_tickets": prev,
                         "change": (int(n) - prev) if prev is not None else None,
                         "share_of_week_pct": round(n / len(wk) * 100, 1),
                         "example_message": short_example(example)})
    return pd.DataFrame(rows)


def print_latest_week(digest):
    full = digest[~digest["partial_week"]]
    if full.empty:
        print("no full week in the data yet")
        return
    week = full["week_start"].max()
    wk = full[full["week_start"] == week]
    first = wk.iloc[0]
    print(f"\n=== digest for the week starting {week} ({first['week_tickets']} tickets) ===")
    print(f"negative sentiment: {first['negative_pct']}%")
    for _, r in wk.iterrows():
        change = "n/a" if pd.isna(r["change"]) else f"{int(r['change']):+d} vs last week"
        print(f"{r['rank']}. {r['category']}: {r['tickets']} tickets ({r['share_of_week_pct']}%), {change}")
        print(f"     e.g. \"{r['example_message']}\"")
    print("customers who say they contacted us before:",
          ", ".join(f"{c} {first[f'contacted_before_pct_{c}']}%" for c in CHANNELS
                    if pd.notna(first[f'contacted_before_pct_{c}'])))
    print("product spikes:", first["spike_skus"] or "none")


def run(analyzed):
    digest = build_digest(analyzed)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    digest.to_csv(config.WEEKLY_DIGEST_FILE, index=False, encoding="utf-8-sig")
    print(f"weekly digest: {digest['week_start'].nunique()} weeks -> {config.WEEKLY_DIGEST_FILE}")
    print_latest_week(digest)
    return digest


if __name__ == "__main__":
    run(pd.read_csv(config.ANALYZED_TICKETS_FILE))