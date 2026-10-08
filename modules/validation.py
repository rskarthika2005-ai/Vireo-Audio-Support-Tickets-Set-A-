import math
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source import config
from modules.preprocess import load_clean_data

FIELDS = ["category", "sentiment", "priority", "root_cause", "resolution", "already_contacted_before"]


def error_range(wrong, checked):
    if checked == 0:
        return None, None
    z = 1.96
    p = wrong / checked
    middle = (p + z * z / (2 * checked)) / (1 + z * z / checked)
    spread = z * math.sqrt(p * (1 - p) / checked + z * z / (4 * checked ** 2)) / (1 + z * z / checked)
    low = max(0, middle - spread)
    high = min(1, middle + spread)
    return round(low * 100, 1), round(high * 100, 1)


def make_row(section, item, checked, issues, note=""):
    rate = round(issues / checked * 100, 1) if checked else None
    low, high = (None, None)
    if section == "ai":
        low, high = error_range(issues, checked)
    return {"section": section, "item": item, "checked": int(checked), "issues": int(issues),
            "rate_pct": rate, "range_low_pct": low, "range_high_pct": high, "note": note}


def data_checks(data):
    t = data["tickets"]
    log = data["log"]
    total = len(t)
    done = t["is_completed"]

    rows = []
    rows.append(make_row("data", "duplicate ticket_id rows in raw file", log["rows_in_file"],
                         log["rows_in_file"] - log["unique_ticket_ids"], "legacy re-import, kept the helpdesk row"))
    rows.append(make_row("data", "missing ticket_id", total, t["ticket_id"].isnull().sum()))
    rows.append(make_row("data", "created_at missing or not readable", total, t["created_at"].isnull().sum()))
    rows.append(make_row("data", "customer_id missing", total, t["customer_id"].isnull().sum()))
    rows.append(make_row("data", "customer_message missing", total, t["customer_message"].isnull().sum()))
    rows.append(make_row("data", "finished ticket without agent_notes", done.sum(), (done & t["agent_notes"].isnull()).sum()))
    rows.append(make_row("data", "finished ticket without resolved_at", done.sum(), (done & t["resolved_at"].isnull()).sum()))
    rows.append(make_row("data", "finished ticket without agent_id", done.sum(), (done & t["agent_id"].isnull()).sum()))
    rows.append(make_row("data", "agent_id not in agents.csv", total, (t["agent_id"].notnull() & t["agent_name"].isnull()).sum()))
    rows.append(make_row("data", "first response before creation", total, (t["response_minutes"] < 0).sum()))
    rows.append(make_row("data", "resolved before first response", total, (t["handle_hours"] < 0).sum(), "should be 0 after the utc fix"))
    rows.append(make_row("data", "resolved before creation", total, (t["days_to_resolve"] < 0).sum()))
    rows.append(make_row("data", "status not resolved/closed/open/pending", total,
                         (~t["status"].isin(["resolved", "closed", "open", "pending"])).sum()))
    rows.append(make_row("data", "csat outside 1 to 5", total, ((t["csat_score"] < 1) | (t["csat_score"] > 5)).sum()))
    return rows


def make_label_sheet(analyzed):
    usable = analyzed[~analyzed["parse_failed"].astype(bool)]
    size = min(config.VALIDATION_SAMPLE_SIZE, len(usable))
    sample = usable.sample(size, random_state=config.SAMPLE_SEED)

    sheet = pd.DataFrame()
    sheet["ticket_id"] = sample["ticket_id"]
    sheet["customer_message"] = sample["customer_message"]
    sheet["agent_notes"] = sample["agent_notes"]
    sheet["category_bot"] = sample["category_bot"]
    sheet["priority_recorded"] = sample["priority_recorded"]
    sheet["ai_category"] = sample["category"]
    sheet["ai_issue"] = sample["issue"]
    sheet["ai_sentiment"] = sample["sentiment"]
    sheet["ai_priority"] = sample["priority_ai"]
    sheet["ai_root_cause"] = sample["root_cause"]
    sheet["ai_resolution"] = sample["resolution"]
    sheet["ai_already_contacted_before"] = sample["already_contacted_before"]
    for field in FIELDS:
        sheet["ok_" + field] = ""
    sheet["note"] = ""

    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    sheet.to_csv(config.VALIDATION_LABELS_FILE, index=False, encoding="utf-8-sig")
    return size


def to_mark(value):
    value = str(value).strip().lower()
    if value in ("y", "yes", "1", "true"):
        return True
    if value in ("n", "no", "0", "false"):
        return False
    return None    


def ai_checks(analyzed):
    labels = pd.read_csv(config.VALIDATION_LABELS_FILE, encoding="utf-8-sig", dtype=str).fillna("")
    rows = []
    rows.append(make_row("ai", "parse failures (all analysed tickets)", len(analyzed),
                         analyzed["parse_failed"].astype(bool).sum(), "answer rejected twice"))
    marks = pd.DataFrame()
    for field in FIELDS:
        marks[field] = labels["ok_" + field].map(to_mark)

    for field in FIELDS:
        answered = marks[field].dropna()
        wrong = (answered == False).sum()
        rows.append(make_row("ai", field + " wrong", len(answered), wrong))

    complete = marks.dropna()
    wrong_any = len(complete) - complete.all(axis=1).sum()
    rows.append(make_row("ai", "at least one field wrong (tickets with all 6 marked)", len(complete), wrong_any))

    
    has_wrong = (marks == False).any(axis=1)
    labels[has_wrong].to_csv(config.VALIDATION_MISMATCH_FILE, index=False, encoding="utf-8-sig")
    return rows, len(labels), int(has_wrong.sum())


def run(analyzed=None, data=None):
    if data is None:
        data = load_clean_data()
    rows = data_checks(data)

    if analyzed is None and os.path.exists(config.ANALYZED_TICKETS_FILE):
        analyzed = pd.read_csv(config.ANALYZED_TICKETS_FILE)

    if analyzed is None or analyzed.empty:
        print("no analyzed tickets yet, only the data checks were run")
    elif not os.path.exists(config.VALIDATION_LABELS_FILE):
        size = make_label_sheet(analyzed)
        print("\nlabel sheet created with", size, "tickets ->", config.VALIDATION_LABELS_FILE)
        print("open it, type y or n in every ok_ column, save as csv and run this again")
    else:
        ai_rows, n_labels, n_wrong = ai_checks(analyzed)
        rows = rows + ai_rows
        print("\nlabels read:", n_labels, "tickets,", n_wrong, "with a wrong field ->", config.VALIDATION_MISMATCH_FILE)

    report = pd.DataFrame(rows)
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    report.to_csv(config.VALIDATION_FILE, index=False, encoding="utf-8-sig")

    print("\n--- validation report ---")
    for _, r in report.iterrows():
        line = "[" + r["section"] + "] " + r["item"] + ": " + str(int(r["issues"])) + " of " + str(int(r["checked"]))
        if pd.notna(r["rate_pct"]):
            line += " (" + str(r["rate_pct"]) + "%)"
        if pd.notna(r["range_low_pct"]):
            line += ", 95% range " + str(r["range_low_pct"]) + " to " + str(r["range_high_pct"]) + "%"
        print(line)
    print("saved ->", config.VALIDATION_FILE)
    return report


if __name__ == "__main__":
    run()