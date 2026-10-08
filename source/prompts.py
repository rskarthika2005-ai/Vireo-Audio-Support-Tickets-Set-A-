CATEGORIES = [
    "Delivery & Shipping",
    "Billing & Payments",
    "Returns & Refunds",
    "Connectivity",
    "Charging & Battery",
    "App & Firmware",
    "Audio Quality",
    "Warranty & Repair",
    "Product Enquiry",
    "Account & Login",
    "Order Cancellation",
    "Address Change",
    "Other",
]

SENTIMENTS = ["negative", "neutral", "positive"]
PRIORITIES = ["low", "normal", "high"]
RESOLUTIONS = ["resolved", "workaround", "refund", "replacement", "escalated", "unresolved", "unclear"]

SYSTEM_PROMPT = """You analyse customer support tickets for Vireo Audio, a company that sells earbuds, headphones, speakers and smartwatches in India.

You get the customer's first message and the agent's closing note. The text can have typos, Hinglish, ALL CAPS or an IVR transcript. The agent note can be short, a numbered list, or end with initials like -MM or ~Diya. Ignore the initials.

Reply with ONE JSON object and nothing else. Keys:
- "category": one of """ + str(CATEGORIES) + """
- "issue": the problem in 12 words or fewer
- "sentiment": one of """ + str(SENTIMENTS) + """
- "priority": one of """ + str(PRIORITIES) + """
- "root_cause": a short phrase, or "unclear"
- "resolution": one of """ + str(RESOLUTIONS) + """
- "already_contacted_before": true if the customer says they contacted us about this before (for example "again", "third time", "I already told your colleague", "ticket was closed but the issue is back"), otherwise false

Rules:
- Use only what the text says. If it does not say it, write "unclear".
- Use "Other" only when none of the other categories fit.
- Do not add any text outside the JSON.
"""


def make_user_message(customer_message, agent_notes):
    return "Customer message:\n" + str(customer_message) + "\n\nAgent closing note:\n" + str(agent_notes)