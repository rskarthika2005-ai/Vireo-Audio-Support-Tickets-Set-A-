<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&height=220&text=VIREO%20AUDIO&fontSize=48&fontAlignY=38&desc=SUPPORT%20TICKET%20ANALYSIS%20%7C%20AI%20%7C%20CUSTOMER%20EXPERIENCE&descAlignY=60&animation=fadeIn&fontColor=ffffff&color=0:0078D4,50:2563EB,100:7C3AED"/>

<br>

### **AI-Assisted Support Analytics • Customer Experience • Business Intelligence**

<p>
Transforming customer support tickets into
<b>actionable insights using AI, analytics and interactive dashboards.</b>
</p>

<br>

<img src="https://img.shields.io/badge/Support%20Analytics-0078D4?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Artificial%20Intelligence-2563EB?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Generative%20AI-7C3AED?style=for-the-badge"/>
<img src="https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white"/>

<br><br>

<a href="https://fbh8ydtfxb7wecajwhehau.streamlit.app/">
<img src="https://img.shields.io/badge/Live%20Dashboard-Open-2563EB?style=for-the-badge"/>
</a>

&nbsp;

<a href="https://github.com/rskarthika2005-ai/Vireo-Audio-Support-Tickets-Set-A-">
<img src="https://img.shields.io/badge/GitHub-Repository-181717?style=for-the-badge&logo=github&logoColor=white"/>
</a>

</div>

---

<div align="center">

## ✦ **ABOUT THE PROJECT**

</div>

**Vireo Audio – Support Ticket Analysis** is an AI-assisted analytics project that transforms approximately **18 months of customer support tickets** into actionable customer experience and business insights.

The project produces three main management views:

- **Weekly Digest** — what customers are complaining about.
- **Agent Leaderboard** — agent performance alongside repeat rate, breach rate and CSAT.
- **Money Finding** — potential financial impact from support problems.

The project combines **Python, Pandas, Generative AI and Streamlit** to create an end-to-end support analytics workflow.

---

<div align="center">

## ✦ **PROJECT OBJECTIVE**

</div>

### Reduce Repeat Customer Contacts

The main business goal is to reduce repeat contacts from:

<div align="center">

# **27.3% → 23.1%**

</div>

The **23.1%** benchmark is achieved by the best large Voice Frontline team.

The estimated opportunity is approximately:

<div align="center">

# **Rs 22,000 / Quarter**

</div>

This connects customer support improvement with measurable business value.

---

<div align="center">

## ✦ **PROJECT OVERVIEW**

</div>

<table align="center">

<tr>

<td align="center" width="25%">

### **12,528**

Raw Rows

</td>

<td align="center" width="25%">

### **11,875**

Unique Tickets

</td>

<td align="center" width="25%">

### **653**

Duplicates

</td>

<td align="center" width="25%">

### **44**

Agents

</td>

</tr>

<tr>

<td align="center">

### **18**

Months

</td>

<td align="center">

### **100**

AI Analysed

</td>

<td align="center">

### **54**

Weekly Periods

</td>

<td align="center">

### **0**

Parse Failures

</td>

</tr>

</table>

---

<div align="center">

## ✦ **KEY FINDINGS**

</div>

### Customer Support

The analysis identifies the most common customer support issues using AI-assisted ticket classification.

### Agent Performance

The leaderboard provides weekly performance visibility across support agents.

### Financial Opportunity

Support issues are connected to estimated financial impact through repeat contacts, late-response credits and team transfers.

### AI Quality

AI-generated ticket labels are checked through automated data validation, parsing checks and manual review.

---

<div align="center">

## ✦ **DATA PREPROCESSING**

</div>

Before analysis, the raw support data is cleaned and validated.

| Processing Step | Result |
|---|---:|
| Raw ticket rows | 12,528 |
| Unique tickets | 11,875 |
| Duplicate rows | 653 |
| Duplicate rate | 5.2% |
| Legacy resolved dates corrected | 2,937 |
| Zero CSAT values treated as missing | 1,750 |

### Data Quality Checks

After preprocessing:

- No missing ticket IDs
- No missing customer IDs
- No missing customer messages
- No unmatched agents
- No unmatched orders
- No negative response times
- No negative handling times

The raw input files are not edited directly. Cleaning is performed on a working copy.

---

<div align="center">

## ✦ **AI ANALYSIS**

</div>

The AI analysis processes selected support tickets and returns structured information including:

- Ticket category
- Customer tone
- Support issue classification

The AI instructions are maintained separately in `source/prompts.py`, while communication with the AI model is isolated in `source/llm_client.py`.

### Support Ticket Categories

| Category | Share |
|---|---:|
| Returns & Refunds | 20% |
| Delivery & Shipping | 12% |
| Billing & Payments | 12% |
| Audio Quality | 9% |
| Charging & Battery | 9% |
| Connectivity | 9% |
| Product Enquiry | 8% |
| Order Cancellation | 7% |
| App & Firmware | 4% |
| Address Change | 4% |
| Account & Login | 3% |
| Warranty & Repair | 3% |

---

<div align="center">

## ✦ **AI TOOLS & COST**

</div>

<div align="center">

## ✦ **AI TOOL USAGE & COST**

<br>

### **Google GenAI**

</div>

<div align="center">

The project uses **Google GenAI** during the ticket-analysis stage
to generate structured support-ticket classifications.

</div>

<br>

| Item | Details |
|:---|:---|
| **AI Tool** | **Google GenAI** |
| **AI Purpose** | Generate one category and one customer tone per ticket |
| **Python Package** | `google-genai` |
| **AI Integration** | `source/llm_client.py` |
| **AI Instructions** | `source/prompts.py` |
| **AI Analysis Script** | `modules/analyze_ticket.py` |
| **AI Results** | `output/analyzed_tickets.csv` |
| **AI Cache** | `output/llm_cache.jsonl` |

<br>

<div align="center">

### **AI COST**

# **Rs 0 Direct API Cost**

The recorded project run used **free-tier Google GenAI access**
and reused cached AI results. Therefore, no new paid API calls
were required during the recorded run.

</div>

<br>

### **Recorded AI Usage**

| Metric | Result |
|:---|---:|
| Tickets selected | **100** |
| Tickets already cached | **100** |
| New AI calls | **0** |
| Input tokens | **42,483** |
| Output tokens | **7,694** |
| Parse failures | **0** |

<div align="center">

<br>

> **Note:** Google GenAI free-tier availability and usage limits
> may vary depending on the account and current provider policies.

</div>
### Cost-Controlled Design

Only the ticket-analysis stage communicates with the AI model.

The system uses a cache:

```text
Ticket
   ↓
Check llm_cache.jsonl
   ↓
Already analysed?
   ├── Yes → Reuse saved result
   │
   └── No → Send to AI → Save result
