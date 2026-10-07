import argparse
import os
import sys
import time

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from source import config
from modules import analyze_ticket, leaderboard, preprocess, validation, weekly_digest


def step(number, title):
    print(f"\n{'=' * 60}\nSTEP {number}: {title}\n{'=' * 60}")

def check_api_settings():
    problems = []
    if not config.API_KEY:
        problems.append("GEMINI_API_KEY is missing in .env")
    if not config.MODEL_NAME:
        problems.append("MODEL_NAME is missing in .env")
    if problems:
        print("cannot call the model:\n  - " + "\n  - ".join(problems))
        print("fix the .env file, or run with --no-llm to use saved answers only.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Vireo support tickets pipeline")
    parser.add_argument("--limit", type=int, help="only analyse N tickets (try 20, then 50)")
    parser.add_argument("--yes", action="store_true", help="do not ask before a full run")
    parser.add_argument("--no-llm", action="store_true", help="use only answers already in the cache")
    args = parser.parse_args()
    started = time.time()

    if not args.no_llm:
        check_api_settings()

    step(1, "preprocess (clean the data)")
    data = preprocess.load_clean_data()
    for key, value in data["log"].items():
        print(f"  {key}: {value}")
    tickets = data["tickets"]

    step(2, "analyze tickets with the model")
    chosen, results = analyze_ticket.run_analysis(
        tickets, limit=args.limit, assume_yes=args.yes, cache_only=args.no_llm)
    out = analyze_ticket.build_output(chosen, results)
    analyze_ticket.print_summary(out)

    analyzed = None
    if out.empty:
        print("\nno analysed tickets, so the digest and the AI validation are skipped.")
    else:
        analyzed = pd.read_csv(config.ANALYZED_TICKETS_FILE)

    step(3, "validate (data checks, and the AI check if labels exist)")
    validation.run(analyzed, data)

    step(4, "weekly digest")
    if analyzed is not None:
        weekly_digest.run(analyzed)
    else:
        print("skipped, nothing analysed yet")

    step(5, "agent leaderboard")
    leaderboard.run(tickets)

    print(f"\n{'=' * 60}\nDONE in {time.time() - started:.0f} seconds. Output files:")
    for path in [config.ANALYZED_TICKETS_FILE, config.WEEKLY_DIGEST_FILE,
                 config.LEADERBOARD_FILE, config.VALIDATION_FILE]:
        if os.path.exists(path):
            print(f"  {os.path.basename(path)}: {len(pd.read_csv(path))} rows")
        else:
            print(f"  {os.path.basename(path)}: not created")


if __name__ == "__main__":
    main()
