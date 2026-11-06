# Pivot — Job Data Approaches

This document describes the five approaches evaluated for sourcing live job listings in Pivot, with real examples. It serves as both technical documentation and a portfolio artifact demonstrating architectural decision-making.

---

## The Problem

Pivot needs real, current job listings to be useful. Claude's training knowledge is stale — job postings from training data may be months or years old, companies may have changed hiring, and salary ranges shift constantly. A career advocate that shows outdated listings is worse than no listings at all.

Five approaches were evaluated:

---

## Approach 1 — Claude Training Knowledge (Fallback Only)

**Status:** Active as fallback when live APIs are unavailable

**How it works:** Claude generates job titles, company names, and salary ranges from its training data when no live source is available.

**Example output for a nurse in NJ targeting healthcare administration:**
> "Healthcare administration roles in the New Jersey area include positions such as Clinical Operations Manager at RWJBarnabas Health, Director of Patient Services at Hackensack Meridian Health, and Healthcare Administrator at CarePoint Health. Salary ranges typically fall between $85,000 and $130,000 for experienced candidates."

**Problems:**
- Data may be 1-2 years old
- Companies listed may have changed hiring or restructured
- Salary ranges may not reflect current market
- Job postings may no longer exist
- Cannot provide apply links

**When used:** Only when JSearch and USAJobs both fail or return no results. The Fact-Check Agent labels all Claude-generated job data as ESTIMATED.

---

## Approach 2 — JSearch via RapidAPI (Active — Fallback Only)

**Status:** Active as fallback when Apify returns fewer than 10 combined results

**API:** Available via RapidAPI (https://rapidapi.com)
**Free tier:** 200 requests/month
**Data source:** Google for Jobs — aggregates Indeed, LinkedIn, Glassdoor, ZipRecruiter in real time

**How it works:** The Research Agent calls `jsearch_client.py` with the user's target role and location. JSearch queries Google for Jobs and returns current listings with title, company, location, salary (when available), and apply link.

**Example query for a nurse in NJ targeting healthcare administration:**
```python
search_jobs(
    query="healthcare administration nurse NJ",
    location="New Jersey"
)
```

**Example output:**
```
LIVE JOB LISTINGS (from Indeed/LinkedIn via JSearch):
1. Healthcare Administrator at Atlantic Health System (Morristown, NJ) | $95,000–$118,000 YEAR
   Apply: https://www.indeed.com/viewjob?jk=abc123...
2. Clinical Operations Manager at RWJBarnabas Health (New Brunswick, NJ)
   Apply: https://www.linkedin.com/jobs/view/...
3. Director of Care Coordination at Hackensack Meridian Health (Hackensack, NJ) | $110,000–$135,000 YEAR
   Apply: https://careers.hackensackmeridianhealth.org/...
```

**Advantages:**
- Real-time listings updated daily
- Aggregates multiple job boards in one API call
- Returns apply links directly
- Includes salary data when available
- Free tier sufficient for portfolio demo (200 requests/month)

**Limitations:**
- 200 requests/month on free tier (upgrade $10/month for 1,000)
- Occasional slow response times (11+ seconds observed)
- Some listings may not include salary data
- Not all apply links are direct — some route through aggregator pages

**Implementation:** `src/jsearch_client.py`

---

## Approach 3 — Indeed Publisher API (Evaluated — Replaced by Apify)

**Status:** Evaluated and replaced by Approach 5 (Apify Indeed Scraper)

**Note:** The reasoning below was recorded when this approach was evaluated. Third-party sources report that Indeed has since retired the public Publisher API. That has not been confirmed against Indeed's own documentation.

**Why it was evaluated:** Indeed is the largest job board in the US. A direct Indeed API would provide the most comprehensive listing data without the aggregator layer.

**Why it was not implemented:**

The Indeed Publisher API (https://www.indeed.com/publisher) is free to register for and works in browser-based contexts. However, Indeed's OAuth authentication flow requires a browser redirect — it cannot complete in a server-side Python context without a full OAuth callback implementation.

Specifically:
- Indeed MCP works in Claude.ai because it authenticates via the browser session that Claude.ai runs in
- From a Python FastAPI backend on Render, there is no browser session — the OAuth redirect has nowhere to go
- Implementing full OAuth with callback URL, token storage, and refresh logic was evaluated but deferred as out of scope for Pivot 1.0

**Example of what Indeed Publisher API would return for a nurse in NJ:**
```
Indeed Publisher API Response (hypothetical):
{
  "jobtitle": "Healthcare Administrator",
  "company": "Atlantic Health System",
  "city": "Morristown",
  "state": "NJ",
  "country": "US",
  "formattedLocation": "Morristown, NJ",
  "source": "Indeed",
  "date": "2026-03-20",
  "snippet": "Seeking experienced healthcare administrator...",
  "url": "https://www.indeed.com/viewjob?jk=...",
  "onmousedown": "...",
  "latitude": 40.7968,
  "longitude": -74.4819,
  "jobkey": "abc123",
  "sponsored": false
}
```

**Why it was replaced:**
The OAuth complexity was solved a different way — Apify's `misceres/indeed-scraper` actor scrapes Indeed directly without requiring OAuth, delivering equivalent data with zero auth infrastructure.

---

## Approach 4 — USAJobs API (Active — Government Roles)

**Status:** Active, secondary source for government roles

**API:** https://developer.usajobs.gov/
**Free tier:** Unlimited (free API key, no rate limits documented)
**Data source:** Official U.S. federal government job listings

**How it works:** The Research Agent calls `usajobs_client.py` in parallel with JSearch. USAJobs returns federal government positions relevant to the user's target role and location.

**Example query for a nurse in NJ targeting healthcare administration:**
```python
search_jobs(
    query="healthcare administration",
    location="New Jersey"
)
```

**Example output:**
```
GOVERNMENT JOB LISTINGS (from USAJobs):
1. Health Systems Administrator at Department of Veterans Affairs (East Orange, NJ) | $89,054–$115,766 YEAR
   Apply: https://www.usajobs.gov/job/...
2. Medical Administrative Officer at U.S. Army (Fort Dix, NJ) | $72,553–$94,317 YEAR
   Apply: https://www.usajobs.gov/job/...
```

**Advantages:**
- Free and unlimited
- Official government postings — no aggregation uncertainty
- Strong for healthcare, administration, IT, and engineering roles
- Excellent salary data (government pay scales are public and precise)

**Limitations:**
- Government roles only — no private sector
- Some roles require citizenship or clearance
- Fewer listings than private sector sources
- Response time can be slow

**Implementation:** `src/usajobs_client.py`

---

## Approach 5 — Apify Direct Scrapers (Active — Primary Source)

**Status:** Active as of April 2026 — primary job data source

**Actors used:**
- `misceres/indeed-scraper` — direct Indeed scraper, 20K+ users, 4.0 rating, pay-per-usage
- `cryptosignals/linkedin-jobs-scraper` — direct LinkedIn scraper, public guest API (no login), pay-per-usage

**Cost:** ~$0.50/1K results (Indeed), ~$10/1K results (LinkedIn). Testing consumed ~$0.09 on Apify's $5/month free credit.

**Why Apify over Indeed Publisher API:**
Approach 3 (Indeed Publisher API) required browser-based OAuth that cannot complete from a Python backend on Render. Apify's actor handles all scraping infrastructure — no OAuth, no callback URL, no token storage. Drop-in replacement.

**Example output for an ICU nurse in Dallas targeting Clinical Informaticist:**
```
[Indeed] Clinical Informatics Spec 2 at Baylor Scott & White Health (Dallas, TX)
Apply: https://www.indeed.com/viewjob?jk=...

[LinkedIn] Clinical Informaticist Analyst at White Rock Medical Center (Dallas, TX)
Apply: https://www.linkedin.com/jobs/view/...
```

**Implementation:** `src/apify_indeed_client.py`, `src/apify_linkedin_client.py`

---

## Current Architecture Decision

Pivot 1.0 uses **Apify Indeed + Apify LinkedIn (Approach 5)** as the primary sources, with **JSearch (Approach 2)** as a fallback when Apify returns fewer than 10 combined results, **USAJobs (Approach 4)** always running for government roles, and **Claude training knowledge (Approach 1)** as a silent fallback when all live sources fail.

The Research Agent runs Indeed and LinkedIn sequentially, deduplicates by company+title key, formats results with [Indeed] and [LinkedIn] source labels, stores them directly in `state["live_jobs"]` to preserve URLs through the pipeline, and passes them to the Synthesizer which renders them as structured items with Apply Now buttons.

---

## Key Design Decisions

This comparison of approaches, and the waterfall it led to, reflects several deliberate design decisions:

- **Graceful degradation** — five-layer waterfall means the pipeline never fails due to a job API outage; it falls back silently through each layer
- **Source attribution** — each listing is labeled [Indeed] or [LinkedIn] in the Synthesizer output; users know exactly where each job came from
- **Direct vs aggregator** — Apify scrapes Indeed and LinkedIn directly, eliminating the aggregator layer (JSearch) as primary source for better relevance and fresher data
- **OAuth without OAuth** — Indeed Publisher API requires browser-based OAuth impossible from a Python backend; Apify's actor handles all scraping infrastructure with zero auth complexity
- **URL preservation** — live job URLs bypass the Research Agent's prose summarization by storing directly in state, preventing link loss through LLM rewriting
- **Separation of concerns** — job API clients are standalone modules (`apify_indeed_client.py`, `apify_linkedin_client.py`, `jsearch_client.py`, `usajobs_client.py`) testable independently of the LangGraph pipeline
- **Cost optimization** — Apify pay-per-usage on $5/month free credit handles portfolio demo load; JSearch free tier preserved as fallback
