import os
import pandas as pd
import streamlit as st

OUTPUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")

st.set_page_config(page_title="Vireo Audio - support tickets", layout="wide")
st.title("Vireo Audio - support tickets")


def read(name):
    """Read a csv from the output folder. Returns None if it is not there yet."""
    path = os.path.join(OUTPUT, name)
    if not os.path.exists(path):
        st.info(name + " not found. Run the pipeline first.")
        return None
    return pd.read_csv(path, encoding="utf-8-sig")


tab1, tab2, tab3, tab4 = st.tabs(["Weekly digest", "Leaderboard", "Money finding", "AI accuracy"])

with tab1:
    digest = read("weekly_digest.csv")
    if digest is not None:
        digest = digest[digest["partial_week"] == False]      # hide incomplete weeks
        week = st.selectbox("Week starting", sorted(digest["week_start"].unique(), reverse=True))
        this_week = digest[digest["week_start"] == week].sort_values("rank")

        col1, col2 = st.columns(2)
        col1.metric("Tickets this week", int(this_week["week_tickets"].iloc[0]))
        col2.metric("Negative sentiment", str(this_week["negative_pct"].iloc[0]) + "%")

        spikes = this_week["spike_skus"].iloc[0]
        if isinstance(spikes, str) and spikes:
            st.warning("Product spike: " + spikes)

        st.subheader("Top issues")
        st.dataframe(this_week[["rank", "category", "tickets", "share_of_week_pct", "change", "example_message"]],
                     hide_index=True)

        st.subheader("Tickets per week")
        st.line_chart(digest.drop_duplicates("week_start").set_index("week_start")["week_tickets"])
        st.caption("Based on the tickets analysed by the AI so far (a sample), not all 11,875 tickets.")

with tab2:
    board = read("agent_leaderboard.csv")
    if board is not None:
        board = board[board["partial_week"] == False]
        week = st.selectbox("Week", sorted(board["week_start"].unique(), reverse=True), key="lb")
        this_week = board[board["week_start"] == week]

        st.subheader("Tier 1 - ranked by tickets closed")
        tier1 = this_week[this_week["tier"] != 2].sort_values("tickets_closed", ascending=False)
        st.dataframe(tier1[["agent_name", "agent_team", "tickets_closed", "avg_csat", "breach_rate", "repeat_rate"]],
                     hide_index=True)
        st.caption("Read tickets closed together with breach and repeat rate.")

        st.subheader("Tier 2 - not ranked (measured on days to resolve)")
        tier2 = this_week[this_week["tier"] == 2]
        st.dataframe(tier2[["agent_name", "tickets_closed", "median_days_to_resolve", "avg_csat"]],
                     hide_index=True)


with tab3:
    money = read("money_finding.csv")
    if money is not None:
        st.dataframe(money, hide_index=True)

        label_col = "metric" if "metric" in money.columns else money.columns[0]
        cost_col = None
        if "cost_inr" in money.columns:
            cost_col = "cost_inr"
        else:
            for c in money.columns:
                if "cost" in c.lower():
                    cost_col = c
                    break

        if cost_col is None:
            st.warning("No cost column found. This file has these columns: " + ", ".join(money.columns))
        else:
            money[cost_col] = pd.to_numeric(money[cost_col], errors="coerce")
            st.bar_chart(money.set_index(label_col)[cost_col])
            st.caption("Costs use the support policy figures. The categories can overlap, so do not add them up.")

            repeat_rows = money[money[label_col].astype(str).str.contains("repeat", case=False)]
            if len(repeat_rows) > 0 and pd.notnull(repeat_rows[cost_col].iloc[0]):
                repeat_cost = repeat_rows[cost_col].iloc[0]
                cut = st.slider("What if repeat contacts fall by (%)", 0, 50, 20, step=5)
                st.metric("Contact cost saved", "Rs " + format(int(repeat_cost * cut / 100), ","))


with tab4:
    report = read("validation_report.csv")
    if report is not None:
        ai = report[report["section"] == "ai"]
        # only fields that were really checked (checked > 0 and a rate exists)
        wrong = ai[ai["item"].str.endswith(" wrong")
                   & ~ai["item"].str.startswith("at least")
                   & (ai["checked"] > 0)
                   & ai["rate_pct"].notnull()]
        if wrong.empty:
            st.info("No labels yet. Fill the ok_ columns (y/n) in output/validation_labels.csv "
                    "and run python modules/validation.py again.")
        else:
            st.subheader("Accuracy per field (hand-checked tickets)")
            cols = st.columns(len(wrong))
            for col, (_, row) in zip(cols, wrong.iterrows()):
                col.metric(row["item"].replace(" wrong", ""), str(round(100 - row["rate_pct"])) + "%")
            st.caption("Based on " + str(int(wrong["checked"].max())) +
                       " hand-checked tickets. Small sample, so the real accuracy can be a few points higher or lower.")

        st.subheader("Data checks")
        st.dataframe(report[report["section"] == "data"][["item", "checked", "issues", "rate_pct"]],
                     hide_index=True)