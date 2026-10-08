import argparse
import hashlib
import json
import os
import re
import sys
import threading
from concurrent.futures import ThreadPoolExecutor

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source import config, prompts
from modules.preprocess import load_clean_data

AI_FIELDS = ["category", "issue", "sentiment", "priority", "root_cause",
             "resolution", "already_contacted_before"]


PROMPT_ID = hashlib.md5(prompts.SYSTEM_PROMPT.encode("utf-8")).hexdigest()[:8]


SIGNATURE = re.compile(r"\s+(?:-[A-Z]{2,3}|~[A-Z][a-z]+)\s*$")

cache_lock = threading.Lock()


def clean_note(note):
    if pd.isna(note):
        return ""
    return SIGNATURE.sub("", str(note)).strip()


def cache_key(ticket_id):
    return f"{ticket_id}|{config.MODEL_NAME}|{PROMPT_ID}"


def load_cache():
    cache = {}
    if os.path.exists(config.LLM_CACHE_FILE):
        with open(config.LLM_CACHE_FILE, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    cache[record["key"]] = record
    return cache


def save_to_cache(record):
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    with cache_lock:
        with open(config.LLM_CACHE_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


def parse_json(text):
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON found in the answer")
    return json.loads(text[start:end + 1])


def check_answer(answer):
    """Returns the cleaned fields or raises ValueError with the reason."""
    if not isinstance(answer, dict):
        raise ValueError("answer is not a JSON object")
    missing = [k for k in AI_FIELDS if k not in answer]
    if missing:
        raise ValueError("missing keys " + str(missing))

    allowed = {"category": prompts.CATEGORIES, "sentiment": prompts.SENTIMENTS,
               "priority": prompts.PRIORITIES, "resolution": prompts.RESOLUTIONS}
    cleaned = {}
    for field, values in allowed.items():
        value = str(answer[field]).strip()
        # category has capital letters in the list, the others are lowercase
        value = value if field == "category" else value.lower()
        if value not in values:
            raise ValueError(f"{field} '{value}' is not allowed")
        cleaned[field] = value

    flag = answer["already_contacted_before"]
    if isinstance(flag, str):
        flag = {"true": True, "false": False}.get(flag.strip().lower())
    if not isinstance(flag, bool):
        raise ValueError("already_contacted_before must be true or false")
    cleaned["already_contacted_before"] = flag

    cleaned["issue"] = " ".join(str(answer["issue"]).split()[:12])
    cleaned["root_cause"] = " ".join(str(answer["root_cause"]).split()[:12]) or "unclear"
    return cleaned


def analyze_one(ticket_id, customer_message, agent_note, ask):
    """ask(system, user) -> (text, tokens_in, tokens_out). Tries twice, then marks parse_failed."""
    user_message = prompts.make_user_message(customer_message, clean_note(agent_note))
    tokens_in = tokens_out = 0
    error = ""
    for attempt in (1, 2):
        message = user_message
        if attempt == 2:
            message += f"\n\nYour last answer was rejected: {error}. Reply with the JSON only."
        text, t_in, t_out = ask(prompts.SYSTEM_PROMPT, message)   # api errors are not caught here on purpose
        tokens_in += t_in
        tokens_out += t_out
        try:
            fields = check_answer(parse_json(text))
            return {"key": cache_key(ticket_id), "ticket_id": ticket_id, **fields,
                    "parse_failed": False, "tokens_in": tokens_in, "tokens_out": tokens_out}
        except (ValueError, json.JSONDecodeError) as e:
            error = str(e)

    failed = {"category": "unclear", "issue": "unclear", "sentiment": "unclear",
              "priority": "unclear", "root_cause": "unclear", "resolution": "unclear",
              "already_contacted_before": False}
    return {"key": cache_key(ticket_id), "ticket_id": ticket_id, **failed,
            "parse_failed": True, "tokens_in": tokens_in, "tokens_out": tokens_out}


def estimate(todo):
    chars = (todo["customer_message"].fillna("").str.len() + todo["agent_notes"].fillna("").str.len()).sum()
    tokens_in = int(len(prompts.SYSTEM_PROMPT) / 4 * len(todo) + chars / 4)
    tokens_out = 80 * len(todo)
    cost = (tokens_in * config.INPUT_PRICE_PER_MTOK + tokens_out * config.OUTPUT_PRICE_PER_MTOK) / 1_000_000
    return tokens_in, tokens_out, cost


def run_analysis(tickets, limit=None, assume_yes=False, cache_only=False, ask=None):
    selected = tickets.sample(frac=1, random_state=config.SAMPLE_SEED)
    if limit:
        selected = selected.head(limit)

    cache = load_cache()
    in_cache = selected["ticket_id"].map(lambda t: cache_key(t) in cache)
    if cache_only:
        selected = selected[in_cache]
        in_cache = in_cache[in_cache]
    todo = selected[~in_cache]
    print(f"tickets selected: {len(selected)} | already in cache: {int(in_cache.sum())} | to send: {len(todo)}")

    if len(todo) and not cache_only:
        tokens_in, tokens_out, cost = estimate(todo)
        money = f"about ${cost:.2f}" if cost else "prices not set in .env"
        print(f"estimate: ~{tokens_in:,} tokens in, ~{tokens_out:,} tokens out ({money})")
        if not limit and not assume_yes:
            if input("send all of these? type yes: ").strip().lower() != "yes":
                print("cancelled, nothing was sent")
                sys.exit(0)

        if ask is None:
            from source.llm_client import get_client, call_llm
            client = get_client()
            ask = lambda system, user: call_llm(client, system, user)

        def work(row):
            try:
                record = analyze_one(row.ticket_id, row.customer_message, row.agent_notes, ask)
            except Exception as e:
                print("  api error on", row.ticket_id, "-", str(e)[:80])
                return None
            save_to_cache(record)
            return record

        done = 0
        with ThreadPoolExecutor(max_workers=config.LLM_WORKERS) as pool:
            for record in pool.map(work, todo.itertuples(index=False)):
                if record:
                    cache[record["key"]] = record
                done += 1
                if done % 25 == 0:
                    print(f"  {done}/{len(todo)}")

    selected = selected[selected["ticket_id"].map(lambda t: cache_key(t) in cache)]
    return selected, cache


def build_output(selected, cache):
    if len(selected) == 0:
        return pd.DataFrame()
    ai = pd.DataFrame([cache[cache_key(t)] for t in selected["ticket_id"]])
    ai = ai[["ticket_id"] + AI_FIELDS + ["parse_failed", "tokens_in", "tokens_out"]]
    ai = ai.rename(columns={"priority": "priority_ai"})

    keep = ["ticket_id", "created_at", "week_start", "channel", "product_sku", "lot_code",
            "agent_id", "status", "transfers", "breach", "repeat_contact", "priority",
            "category", "customer_message", "agent_notes"]
    base = selected[keep].rename(columns={"priority": "priority_recorded", "category": "category_bot"})
    out = base.merge(ai, on="ticket_id", how="left")
    os.makedirs(config.OUTPUT_FOLDER, exist_ok=True)
    out.to_csv(config.ANALYZED_TICKETS_FILE, index=False, encoding="utf-8-sig")
    return out


def print_summary(out):
    if out.empty:
        print("nothing analysed yet")
        return
    print(f"\nrows saved: {len(out)}  ->  {config.ANALYZED_TICKETS_FILE}")
    print("parse failures:", int(out["parse_failed"].sum()))
    print(f"tokens used: in {int(out['tokens_in'].sum()):,}, out {int(out['tokens_out'].sum()):,}")
    print("\nAI categories:\n" + out["category"].value_counts().to_string())
    moved = out[(out["category_bot"] == "Other") & (out["category"] != "Other")]
    print(f"\nbot said Other, AI found a category: {len(moved)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, help="only analyse N tickets (try 20, then 50)")
    parser.add_argument("--yes", action="store_true", help="do not ask before a full run")
    parser.add_argument("--cache-only", action="store_true", help="use only tickets already saved, no API calls")
    parser.add_argument("--since", help="only tickets created on or after this date, e.g. 2026-04-20")
    args = parser.parse_args()

    clean = load_clean_data()["tickets"]
    if args.since:
        clean = clean[clean["created_at"] >= pd.to_datetime(args.since)]
        print("tickets from", args.since, "onwards:", len(clean))
    chosen, results = run_analysis(clean, limit=args.limit, assume_yes=args.yes, cache_only=args.cache_only)
    print_summary(build_output(chosen, results))