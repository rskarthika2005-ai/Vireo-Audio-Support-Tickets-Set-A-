import pandas as pd
from source import config
def load_files():
    tickets = pd.read_csv(config.TICKETS_FILE)
    agents = pd.read_csv(config.AGENTS_FILE)
    customers = pd.read_csv(config.CUSTOMERS_FILE)
    orders = pd.read_csv(config.ORDERS_FILE)
    products = pd.read_csv(config.PRODUCTS_FILE)
    return tickets, agents, customers, orders, products


def check_columns(tickets, agents, orders, products):
   
    needed = {
        "tickets": (tickets, ["ticket_id", "created_at", "first_response_at", "resolved_at",
                              "status", "channel", "customer_id", "order_id", "product_sku",
                              "agent_id", "csat_score", "source_system"]),
        "agents": (agents, ["agent_id", "name", "site", "team", "shift", "tier"]),
        "orders": (orders, ["order_id", "customer_id", "sku", "order_date", "lot_code"]),
        "products": (products, ["sku", "product_name", "family"]),
    }
    for name, (df, cols) in needed.items():
        missing = [c for c in cols if c not in df.columns]
        if missing:
            raise ValueError(name + ".csv is missing columns: " + str(missing))


def fix_dates(tickets, orders):
    for col in ["created_at", "first_response_at", "resolved_at"]:
        tickets[col] = pd.to_datetime(tickets[col], format=config.DATE_FORMAT, errors="coerce")
    orders["order_date"] = pd.to_datetime(orders["order_date"], format="%d-%m-%Y", errors="coerce")
    return tickets, orders


def remove_duplicate_tickets(tickets):
   
    tickets["is_legacy"] = (tickets["source_system"] == "legacy_fd").astype(int)
    tickets = tickets.sort_values(["ticket_id", "is_legacy"])
    tickets = tickets.drop_duplicates(subset="ticket_id", keep="first")
    return tickets.drop(columns="is_legacy").reset_index(drop=True)


def fix_legacy_resolved_time(tickets):
    
    legacy = (tickets["source_system"] == "legacy_fd") & tickets["resolved_at"].notnull()
    tickets.loc[legacy, "resolved_at"] = tickets.loc[legacy, "resolved_at"] + pd.Timedelta(hours=config.LEGACY_UTC_SHIFT_HOURS)
    return tickets, int(legacy.sum())


def fix_csat(tickets):
    
    zeros = int((tickets["csat_score"] == 0).sum())
    tickets.loc[tickets["csat_score"] == 0, "csat_score"] = float("nan")
    return tickets, zeros


def join_agents_and_products(tickets, agents, products):
   
    agents = agents.rename(columns={"name": "agent_name", "team": "agent_team"})
    agents = agents[["agent_id", "agent_name", "site", "agent_team", "shift", "tier"]]
    tickets = tickets.merge(agents, on="agent_id", how="left")

    products = products.rename(columns={"sku": "product_sku"})
    products = products[["product_sku", "product_name", "family", "unit_cost_inr"]]
    tickets = tickets.merge(products, on="product_sku", how="left")
    return tickets


def join_orders(tickets, orders):
    
    orders = orders.rename(columns={"sku": "product_sku"})
    order_cols = ["order_id", "order_value_inr", "lot_code"]

    by_id = tickets[["ticket_id", "order_id"]].dropna().merge(
        orders[order_cols], on="order_id", how="left")

    blank = tickets[tickets["order_id"].isnull()][["ticket_id", "customer_id", "product_sku"]]
    latest = orders.sort_values("order_date").drop_duplicates(["customer_id", "product_sku"], keep="last")
    by_fallback = blank.merge(latest[["customer_id", "product_sku"] + order_cols],
                              on=["customer_id", "product_sku"], how="left")

    found = pd.concat([by_id[["ticket_id", "order_value_inr", "lot_code"]],
                       by_fallback[["ticket_id", "order_value_inr", "lot_code"]]])
    tickets = tickets.merge(found, on="ticket_id", how="left")
    return tickets


def add_new_columns(tickets):
   
    gap = tickets["first_response_at"] - tickets["created_at"]
    tickets["response_minutes"] = gap.dt.total_seconds() / 60

   
    tickets["target_minutes"] = tickets["channel"].map(config.FIRST_RESPONSE_TARGET_MIN)
    tickets["breach"] = tickets["response_minutes"] > tickets["target_minutes"]

    
    handle = tickets["resolved_at"] - tickets["first_response_at"]
    tickets["handle_hours"] = handle.dt.total_seconds() / 3600
    tickets["days_to_resolve"] = (tickets["resolved_at"] - tickets["created_at"]).dt.total_seconds() / 86400

   
    tickets["week_start"] = tickets["created_at"].dt.normalize() - pd.to_timedelta(tickets["created_at"].dt.weekday, unit="D")
    tickets["closed_week_start"] = tickets["resolved_at"].dt.normalize() - pd.to_timedelta(tickets["resolved_at"].dt.weekday, unit="D")

    
    tickets["is_completed"] = tickets["status"].isin(["resolved", "closed"])
    return tickets


def mark_repeat_contacts(tickets):
    
    tickets = tickets.sort_values(["customer_id", "product_sku", "created_at"])
    group = tickets.groupby(["customer_id", "product_sku"])
    prev_resolved = group["resolved_at"].shift(1)
    days_since = (tickets["created_at"] - prev_resolved).dt.total_seconds() / 86400
    tickets["repeat_contact"] = (days_since >= 0) & (days_since <= config.REPEAT_WINDOW_DAYS)
    return tickets.sort_values("created_at").reset_index(drop=True)


def load_clean_data():
    tickets, agents, customers, orders, products = load_files()
    check_columns(tickets, agents, orders, products)

    log = {}
    log["rows_in_file"] = len(tickets)
    log["unique_ticket_ids"] = tickets["ticket_id"].nunique()

    tickets, orders = fix_dates(tickets, orders)
    tickets = remove_duplicate_tickets(tickets)
    log["rows_after_dedupe"] = len(tickets)

    tickets, shifted = fix_legacy_resolved_time(tickets)
    log["legacy_resolved_at_shifted"] = shifted

    tickets, zeros = fix_csat(tickets)
    log["csat_zeros_made_blank"] = zeros

    tickets = join_agents_and_products(tickets, agents, products)
    log["tickets_without_agent_match"] = int(tickets["agent_name"].isnull().sum())

    tickets = join_orders(tickets, orders)
    log["tickets_without_order_match"] = int(tickets["lot_code"].isnull().sum())

    tickets = add_new_columns(tickets)
    log["negative_handle_time_rows"] = int((tickets["handle_hours"] < 0).sum())
    log["negative_response_time_rows"] = int((tickets["response_minutes"] < 0).sum())

    tickets = mark_repeat_contacts(tickets)

    return {"tickets": tickets, "agents": agents, "customers": customers,
            "orders": orders, "products": products, "log": log}


if __name__ == "__main__":
    data = load_clean_data()
    print("--- cleaning log ---")
    for key, value in data["log"].items():
        print(key, ":", value)
    t = data["tickets"]
    print("breach rate:", round(t["breach"].mean() * 100, 1), "%")
    print("repeat contact rate:", round(t["repeat_contact"].mean() * 100, 1), "%")
    print("completed tickets after dedupe:", int(t["is_completed"].sum()))
