import os
import sys
import pandas as pd

PROJECT_ROOT = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

sys.path.insert(0, PROJECT_ROOT)

from source import config




def calculate_money_finding(tickets):

    df = tickets.copy()

    total_tickets = len(df)

    if total_tickets == 0:
        raise ValueError("No tickets found.")


 

    df["repeat_contact"] = (
        df["repeat_contact"]
        .fillna(False)
        .astype(bool)
    )

    repeat_count = int(
        df["repeat_contact"].sum()
    )

    repeat_rate = (
        repeat_count / total_tickets
    ) * 100



    df["contact_cost_inr"] = (
        df["channel"]
        .astype(str)
        .str.lower()
        .map(config.COST_PER_CONTACT_INR)
        .fillna(0)
    )

    repeat_cost = df.loc[
        df["repeat_contact"],
        "contact_cost_inr"
    ].sum()


  

    df["breach"] = (
        df["breach"]
        .fillna(False)
        .astype(bool)
    )

    breach_count = int(
        df["breach"].sum()
    )

    breach_rate = (
        breach_count / total_tickets
    ) * 100

    breach_cost = (
        breach_count *
        config.BREACH_CREDIT_INR
    )



    df["transfers"] = pd.to_numeric(
        df["transfers"],
        errors="coerce"
    ).fillna(0)

    transfer_count = int(
        df["transfers"].sum()
    )

    transfer_rate = (
        transfer_count / total_tickets
    ) * 100

    transfer_cost = (
        transfer_count *
        config.TRANSFER_COST_INR
    )



    refund_amount = pd.to_numeric(
        df["refund_amount_inr"],
        errors="coerce"
    ).fillna(0)

  
    replacement_issued = (
        df["replacement_issued"]
        .astype(str)
        .str.upper()
        .eq("Y")
    )

    refund_and_replacement = (
        (refund_amount > 0)
        & replacement_issued
    )

    error_count = int(
        refund_and_replacement.sum()
    )

    error_rate = (
        error_count / total_tickets
    ) * 100

    refund_error_amount = float(
        refund_amount[
            refund_and_replacement
        ].sum()
    )



    results = pd.DataFrame([
        {
            "metric": "Repeat contacts",
            "count": repeat_count,
            "rate_percent": round(
                repeat_rate, 2
            ),
            "cost_inr": round(
                repeat_cost, 2
            )
        },
        {
            "metric": "SLA breach credits",
            "count": breach_count,
            "rate_percent": round(
                breach_rate, 2
            ),
            "cost_inr": round(
                breach_cost, 2
            )
        },
        {
            "metric": "Transfers",
            "count": transfer_count,
            "rate_percent": round(
                transfer_rate, 2
            ),
            "cost_inr": round(
                transfer_cost, 2
            )
        },
        {
            "metric": "Refund + replacement errors",
            "count": error_count,
            "rate_percent": round(
                error_rate, 2
            ),
            "cost_inr": round(
                refund_error_amount, 2
            )
        }
    ])


   

    df["quarter"] = (
        df["created_at"]
        .dt.to_period("Q")
        .astype(str)
    )

    quarterly = (
        df.groupby("quarter")
        .agg(
            tickets=("ticket_id", "count"),
            repeat_contacts=(
                "repeat_contact",
                "sum"
            )
        )
        .reset_index()
    )

    quarterly["repeat_rate_percent"] = (
        quarterly["repeat_contacts"]
        / quarterly["tickets"]
        * 100
    ).round(2)

    quarterly["repeat_contact_cost_inr"] = (
        df[df["repeat_contact"]]
        .groupby("quarter")["contact_cost_inr"]
        .sum()
        .reindex(quarterly["quarter"])
        .fillna(0)
        .round(2)
        .values
    )

    quarterly_file = os.path.join(
        config.OUTPUT_FOLDER,
        "money_finding_quarterly.csv"
    )

    quarterly.to_csv(
        quarterly_file,
        index=False
    )


    

    os.makedirs(
        config.OUTPUT_FOLDER,
        exist_ok=True
    )

    results.to_csv(
        config.MONEY_FILE,
        index=False
    )


  

    print()
    print("======================================")
    print("        MONEY FINDING")
    print("======================================")

    print(
        f"Total tickets: {total_tickets:,}"
    )

    print()
    print("1. Repeat contacts")
    print(
        f"Count: {repeat_count:,}"
    )
    print(
        f"Rate: {repeat_rate:.2f}%"
    )
    print(
        f"Associated contact cost: "
        f"Rs {repeat_cost:,.0f}"
    )

    print()
    print("2. SLA breaches")
    print(
        f"Count: {breach_count:,}"
    )
    print(
        f"Rate: {breach_rate:.2f}%"
    )
    print(
        f"Store credit cost: "
        f"Rs {breach_cost:,.0f}"
    )

    print()
    print("3. Transfers")
    print(
        f"Count: {transfer_count:,}"
    )
    print(
        f"Rate: {transfer_rate:.2f}%"
    )
    print(
        f"Transfer cost: "
        f"Rs {transfer_cost:,.0f}"
    )

    print()
    print("4. Refund + replacement")
    print(
        f"Count: {error_count:,}"
    )
    print(
        f"Rate: {error_rate:.2f}%"
    )
    print(
        f"Refund amount in these cases: "
        f"Rs {refund_error_amount:,.0f}"
    )

    print()
    print(
        "Saved:",
        config.MONEY_FILE
    )

    print(
        "Quarterly file:",
        quarterly_file
    )

    print("======================================")


    return results, quarterly




if __name__ == "__main__":

    from modules.preprocess import load_clean_data

    data = load_clean_data()

    calculate_money_finding(
        data["tickets"]
    )