import os
from dotenv import load_dotenv

load_dotenv()

BASE_FOLDER = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FOLDER = os.path.join(BASE_FOLDER, "data")
OUTPUT_FOLDER = os.path.join(BASE_FOLDER, "output")

TICKETS_FILE = os.path.join(DATA_FOLDER, "tickets.csv")
AGENTS_FILE = os.path.join(DATA_FOLDER, "agents.csv")
CUSTOMERS_FILE = os.path.join(DATA_FOLDER, "customers.csv")
ORDERS_FILE = os.path.join(DATA_FOLDER, "orders.csv")
PRODUCTS_FILE = os.path.join(DATA_FOLDER, "products.csv")

ANALYZED_TICKETS_FILE = os.path.join(OUTPUT_FOLDER, "analyzed_tickets.csv")
WEEKLY_DIGEST_FILE = os.path.join(OUTPUT_FOLDER, "weekly_digest.csv")
LEADERBOARD_FILE = os.path.join(OUTPUT_FOLDER, "agent_leaderboard.csv")
VALIDATION_FILE = os.path.join(OUTPUT_FOLDER, "validation_report.csv")


LLM_CACHE_FILE = os.path.join(OUTPUT_FOLDER, "llm_cache.jsonl")
MONEY_FILE = os.path.join(OUTPUT_FOLDER, "money_finding.csv")
VALIDATION_LABELS_FILE = os.path.join(OUTPUT_FOLDER, "validation_labels.csv")
VALIDATION_MISMATCH_FILE = os.path.join(OUTPUT_FOLDER, "validation_mismatches.csv")

API_KEY = os.getenv("GEMINI_API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME")
INPUT_PRICE_PER_MTOK = float(os.getenv("INPUT_PRICE_PER_MTOK", "0"))
OUTPUT_PRICE_PER_MTOK = float(os.getenv("OUTPUT_PRICE_PER_MTOK", "0"))


DATE_FORMAT = "%d-%m-%Y %H:%M"
FIRST_RESPONSE_TARGET_MIN = {"chat": 15, "voice": 120, "social": 240, "email": 480}
BREACH_CREDIT_INR = 350
COST_PER_CONTACT_INR = {"chat": 210, "email": 260, "voice": 520, "social": 240}
TRANSFER_COST_INR = 305
REPEAT_WINDOW_DAYS = 30
TIER_2 = 2

HELPDESK_GO_LIVE = "2025-09-14"


LEGACY_UTC_SHIFT_HOURS = 5.5
LEGACY_UTC_TO_IST_HOURS = LEGACY_UTC_SHIFT_HOURS  


LLM_WORKERS = 2      
SAMPLE_SEED = 42         
VALIDATION_SAMPLE_SIZE = 60
