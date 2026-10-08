import os
import sys
import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source import config
from modules.preprocess import load_clean_data


def build_leaderboard(tickets):
    done = tickets[tickets["is_completed"] & tickets["resolved_at"].notnull()].copy()
    done = done[done["agent_name"].notnull()]

    group_cols = ["agent_id", "agent_name", "agent_team", "tier", "shift", "closed_week_start"]
    table = done.groupby(group_cols).agg(
        tickets_closed=("ticket_id", "count"),
        csat_responses=("csat_score", "count"),
        avg_csat=("csat_score", "mean"),
        breach_rate=("breach", "mean"),
        repeat_rate=("repeat_contact", "mean"),
        median_days_to_resolve=("days_to_resolve", "median"),
    ).reset_index()
    table = table.rename(columns={"closed_week_start": "week_start"})

    table["avg_csat"] = table["avg_csat"].round(2)
    table["breach_rate"] = (table["breach_rate"] * 100).round(1)
    table["repeat_rate"] = (table["repeat_rate"] * 100).round(1)
    table["median_days_to_resolve"] = table["median_days_to_resolve"].round(2)

    tier1 = table["tier"] != config.TIER_2
    table["rank"] = table[tier1].groupby(["week_start", "agent_team"])["tickets_closed"].rank(method="min", ascending=False)
    table["rank"] = table["rank"].astype("Int64")

    table["note"] = ""
    table.loc[~tier1, "note"] = "not ranked, tier 2 is measured on days to resolve"

    
    
    first_day = tickets["created_at"].min().normalize()
    last_day = tickets["created_at"].max().normalize()
    table["partial_week"] = (table["week_start"] < first_day) | (table["week_start"] + pd.Timedelta(days=6) > last_day)

    table = table.sort_values(["week_start", "tier", "agent_team", "rank", "agent_id"])
    columns = ["agent_id", "agent_name", "agent_team", "tier", "shift", "week_start", "partial_week",
               "tickets_closed", "rank", "avg_csat", "csat_responses", "breach_rate", "repeat_rate",
               "median_days_to_resolve", "note"]
    return table[columns].reset_index(drop=True)


def print_latest_week(table):
    full = table[~table["partial_week"]]
    week = full["week_start"].max()
    this_week = full[(full["week_start"] == week) & (full["tier"] != config.TIER_2)]

    print("\nlatest full week:", week.date(), "(top 3 in each team)")
    for team, part in this_week.groupby("agent_team"):
        print(team)
        for _, r in part.sort_values("rank").head(3).iterrows():
            print("  ", r["rank"], r["agent_name"], "-", r["tickets_closed"], "closed, breach",
                  r["breach_rate"], "%, repeat", r["repeat_rate"], "%, csat", r["avg_csat"])

    print("\ntier 2 (not ranked):")
    tier2 = table[table["tier"] == config.TIER_2]
    for name, part in tier2.groupby("agent_name"):
        print("  ", name, "-", int(part["tickets_closed"].sum()), "closed, median",
              round(part["median_days_to_resolve"].median(), 1), "days to resolve")


def run(tickets):
    table = build_leaderboard(tickets)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    table.to_csv(config.LEADERBOARD_FILE, index=False, encoding="utf-8-sig")
    print("leaderboard:", len(table), "agent-weeks,", table["agent_id"].nunique(), "agents ->", config.LEADERBOARD_FILE)
    print_latest_week(table)
    return table


if __name__ == "__main__":
    run(load_clean_data()["tickets"])