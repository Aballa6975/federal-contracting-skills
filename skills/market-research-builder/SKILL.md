---
name: market-research-builder
description: >
  Build FAR Part 10 market research reports by orchestrating the USASpending
  API skill and producing a formatted DOCX for the contract file. Trigger for
  any mention of market research, market research report, FAR Part 10, sources
  sought analysis, vendor landscape, prior award analysis, competition analysis,
  set-aside recommendation, small business availability, contract type analysis,
  or procurement research report. Also trigger when the user needs to research
  comparable awards, analyze the vendor pool for a requirement, justify a
  contract type or set-aside decision, or produce a market research document
  suitable for the contract file. Requires the USASpending API skill to be
  installed. This is an L2 orchestration skill: it contains no API code of its
  own; it tells Claude what to pull from USASpending and how to assemble the
  output into a defensible market research report.
---

# Market Research Builder Skill

## Overview

This skill orchestrates the USASpending API skill to produce FAR Part 10 market research reports as DOCX files suitable for the contract file. It contains no API code of its own. It tells Claude what to pull from USASpending, in what order, and how to synthesize the data into a structured market research report with findings and recommendations.

**Required skill (must be installed):**
1. **USASpending API**: federal award data by NAICS, PSC, agency, vendor, and keyword

**Required API keys:** None. USASpending is free, no-auth.

**What this skill produces:** A DOCX market research report covering: requirement summary, methodology, prior award analysis, pricing trends, vendor landscape, small business availability, contract type analysis, competition analysis, and data-driven recommendations for set-aside strategy, contract type, and competition approach.

**Regulatory basis:** FAR Part 10 requires agencies to conduct market research to determine if commercial products or services are available, assess small business capability, and determine the most appropriate contract type and competition strategy. FAR 10.002 lists specific purposes. This skill implements those requirements by analyzing historical federal award data from USASpending.gov (sourced from FPDS).

## Information to Collect from the User

Before building the report, Claude must collect the following inputs. Ask for everything in a single pass. Provide sensible defaults where noted.

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Requirement description | Brief description of what is being procured | IT help desk support services |
| NAICS code | Primary NAICS code for the requirement | 541512 |

### Optional Inputs (Use Defaults If Not Provided)

| Input | Default | Notes |
|-------|---------|-------|
| PSC code | None | Product/Service Code; narrows results significantly |
| Keywords | Derived from requirement description | Additional search terms for award text matching |
| Dollar range estimate | None | Lower/upper bound for comparable awards; omit filter if not provided |
| Agency scope | Government-wide | Limit to a specific awarding agency or subtier |
| Lookback period | 5 years from today | Start/end dates for time_period filter |
| Performance location | None | State or metro area; used for place_of_performance filter |
| Set-aside interest | None | If user has a target set-aside (e.g., 8(a), SDVOSB), note it for analysis |
| Top N vendors | 15 | Number of top vendors to display in the vendor landscape |

### Input Validation

Before proceeding, validate NAICS and PSC codes using USASpending autocomplete endpoints:
- `POST /api/v2/autocomplete/naics/` with the user's NAICS code
- `POST /api/v2/autocomplete/psc/` with the user's PSC code (if provided)

If either returns zero results, inform the user and suggest alternatives from the autocomplete response.

## Scope Strategy

Agency-scoped searches often return thin results while government-wide searches provide statistical robustness. Use a dual-scope approach:

**Government-wide scope** (for statistical analysis): Sections 3 (Market Overview), 5 (Small Business), 6 (Contract Type), 7 (Competition). These require large sample sizes to produce meaningful percentages and trends. Use NAICS and optionally PSC filters only; do not filter by agency.

**Agency scope** (for relevance): Sections 4 (Prior Awards), vendor landscape detail. If the user specifies an agency, use it here to show directly comparable awards.

Label every section's scope explicitly in the DOCX: "(Government-Wide)" or "(NAVSEA)" etc. This transparency is essential for the contract file.

If the agency-scoped search returns fewer than 20 awards, note this limitation and recommend supplementing with government-wide data for statistical conclusions.

## Orchestration Sequence

Execute these steps in order. Each step uses the USASpending API skill.

### Step 1: Build Filter Objects

Construct two filter objects: one government-wide, one agency-scoped (if applicable).

```python
import json, urllib.request, time
from datetime import datetime, timedelta

def build_filters(naics, psc=None, keywords=None, agency=None, 
                  dollar_range=None, lookback_years=5, location_state=None):
    """Build the common filter object for USASpending queries."""
    
    today = datetime.now()
    start = today - timedelta(days=lookback_years * 365)
    
    filters = {
        "award_type_codes": ["A", "B", "C", "D"],
        "naics_codes": [naics],
        "time_period": [{
            "start_date": start.strftime("%Y-%m-%d"),
            "end_date": today.strftime("%Y-%m-%d")
        }]
    }
    
    if psc:
        filters["psc_codes"] = [psc]
    
    if keywords:
        filters["keywords"] = keywords if isinstance(keywords, list) else [keywords]
    
    if agency:
        filters["agencies"] = [{
            "type": "awarding",
            "tier": "subtier",
            "name": agency
        }]
    
    if dollar_range:
        filters["award_amounts"] = [{
            "lower_bound": dollar_range.get("lower", 0),
            "upper_bound": dollar_range.get("upper", 999999999)
        }]
    
    if location_state:
        filters["place_of_performance_locations"] = [{
            "country": "USA",
            "state": location_state
        }]
    
    return filters
```

**Build both:**
```python
govwide_filters = build_filters(naics=NAICS, psc=PSC, lookback_years=5)
agency_filters = build_filters(naics=NAICS, psc=PSC, agency=AGENCY, lookback_years=5)
```

**CRITICAL filter rules (from USASpending skill):**
- Never include `"exclude": []` in PSC or NAICS filters (causes HTTP 422)
- Use simple array format: `"naics_codes": ["541512"]`
- Award type codes must all be from the same group; contracts = `["A", "B", "C", "D"]`
- Omit the `keywords` key entirely if no keywords are provided (empty array causes HTTP 400)

### Step 2: Get Total Award Counts

**Use `spending_by_award_count` endpoint** for all count-based analysis. Do NOT rely on `page_metadata.total` (that field does not exist in the API response).

```python
def get_count(filters):
    """Get total contract count for a filter set."""
    payload = json.dumps({"filters": filters})
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award_count/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    return data["results"]["contracts"]
```

Get the baseline: `total_govwide = get_count(govwide_filters)`

If agency-scoped: `total_agency = get_count(agency_filters)`

### Step 3: Pull Prior Award Sample (Agency Scope)

**Use the spending_by_award search endpoint.** Pull comparable awards for the prior award table. Use the agency-scoped filter if an agency was specified; otherwise use govwide.

```python
def pull_prior_awards(filters, pages=3):
    """Pull comparable awards. Paginate up to 300 records."""
    all_awards = []
    fields = [
        "Award ID", "Description", "Award Amount", "Recipient Name",
        "Start Date", "End Date", "Awarding Agency", "Awarding Sub Agency",
        "Contract Award Type", "generated_internal_id"
    ]
    
    for page in range(1, pages + 1):
        payload = json.dumps({
            "subawards": False, "limit": 100, "page": page,
            "sort": "Award Amount", "order": "desc",
            "filters": filters, "fields": fields
        })
        url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
        req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        
        results = data.get("results", [])
        all_awards.extend(results)
        
        has_next = data.get("page_metadata", {}).get("hasNext", False)
        if not has_next:
            break
        time.sleep(0.3)
    
    return all_awards
```

**Data quality filtering:** Before analysis, filter the returned awards:
- Exclude awards with $0 or negative `Award Amount` from the display table and statistics (these are closeout-only records)
- Note that USASpending returns awards with any modification activity during the lookback period, even if the base award predates it. This is normal; include them but note the actual start dates.

**CRITICAL: Award distribution stats are sample-biased.** The prior award pull is sorted by `Award Amount` descending and capped at 20-300 records. This means min/max/median/mean computed from this sample reflect only the largest awards, not the full population. Do NOT present these as population statistics. In the report:
- Label the section "Award Value Distribution (Top Awards Sample)" or similar
- State explicitly: "Statistics below reflect the top N awards by value and are not representative of the full population of X awards"
- Omit the "Minimum" statistic entirely (the minimum of a top-N-by-value sample is meaningless)
- If population-level statistics are needed, note that USASpending does not provide a percentile/distribution endpoint; the only option is to paginate through all results, which is impractical for large result sets

**IMPORTANT:** The `Contract Award Type` field returns the award issuance type ("DELIVERY ORDER", "DEFINITIVE CONTRACT", etc.), NOT the contract pricing type (FFP, T&M). See Step 5 for pricing type analysis.

### Step 4: Analyze Vendor Landscape (Agency Scope)

**Use `spending_by_category/recipient` endpoint** for top vendors.

```python
def get_top_vendors(filters, limit=15):
    payload = json.dumps({"filters": filters, "limit": limit, "page": 1})
    url = "https://api.usaspending.gov/api/v2/search/spending_by_category/recipient/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

**Handling negative amounts:** Vendor obligation amounts are net values and can be negative (deobligations exceed new obligations during the period). The response does NOT include a `category_total` field. For market share calculations:
- Compute `positive_total` = sum of amounts for vendors with amount > 0
- Calculate each vendor's share as `vendor_amount / positive_total`
- List vendors with negative amounts separately as "Net Deobligations" at the bottom of the table

**Market concentration:** What percentage of positive obligations do the top 5 vendors represent? If a single vendor holds >40%, flag it as a concentrated market. Note that these percentages reflect share among the top N vendors returned by the API, not share of total market obligations across all vendors in the NAICS code. State this scope explicitly: "The top 5 vendors account for X% of positive obligations among the top 15 vendors sampled."

**Vendor entity deduplication:** The `recipient` category returns results by unique entity (UEI), not by parent company. Large companies often appear multiple times under different UEIs (e.g., "LEIDOS, INC." and "LEIDOS INC." as separate entries due to subsidiaries, divisions, or re-registrations). In the report:
- Note that vendor counts reflect unique UEI registrations and may overstate the number of distinct companies
- If the same company name appears more than once with trivial name variations, note it in the table or combine the entries with a footnote
- Do not attempt automated parent-company rollup (SAM.gov entity hierarchy is not available via USASpending); a manual note is sufficient

**Detecting likely duplicates:** After retrieving vendor results, normalize names and flag likely matches:

```python
import re

def normalize_vendor(name):
    """Strip suffixes and punctuation for fuzzy matching."""
    n = name.upper().strip()
    # Remove common suffixes
    for suffix in [", INC.", " INC.", " INC", ", LLC", " LLC", ", LLP", " LLP",
                   ", CORP.", " CORP.", " CORP", ", L.L.C.", " L.L.C."]:
        n = n.replace(suffix, "")
    # Remove punctuation and extra whitespace
    n = re.sub(r'[^A-Z0-9 ]', '', n)
    n = re.sub(r'\s+', ' ', n).strip()
    return n

# Group vendors by normalized name
from collections import defaultdict
groups = defaultdict(list)
for v in vendors:
    groups[normalize_vendor(v["name"])].append(v)

# Flag groups with >1 entry as likely duplicates
for norm, entries in groups.items():
    if len(entries) > 1:
        # Add footnote to table: "* Likely same parent entity"
        pass
```

This catches obvious cases like "BOOZ ALLEN HAMILTON INC" appearing twice or "PERATON ENTERPRISE SOLUTIONS LLC" / "PERATON INC." When duplicates are found, add a footnote to the vendor table and note the combined obligation total in the narrative. Name normalization catches suffix/punctuation variations but cannot detect acquisitions, rebrands, or parent-subsidiary relationships (e.g., Cerner rebranded to Oracle Health Government Services). These require manual review.

### Step 5: Contract Type Analysis (Government-Wide)

**Use `contract_pricing_type_codes` filter + `spending_by_award_count`** for each pricing type. Do NOT try to extract pricing type from the `Contract Award Type` search field (that field contains the award issuance type, not the pricing mechanism).

```python
pricing_types = [
    ("J", "Firm Fixed Price"), ("Y", "Time and Materials"), ("Z", "Labor Hours"),
    ("U", "Cost Plus Fixed Fee"), ("R", "Cost Plus Award Fee"),
    ("V", "Cost Plus Incentive Fee"), ("S", "Cost No Fee"),
    ("L", "FP Incentive"), ("B", "FP Level of Effort"),
    ("K", "FP w/ EPA"), ("M", "FP Award Fee"),
    ("A", "FP Redetermination"), ("T", "Cost Sharing")
]

type_counts = {}
for code, name in pricing_types:
    f = {**govwide_filters, "contract_pricing_type_codes": [code]}
    count = get_count(f)
    if count > 0:
        type_counts[code] = {"name": name, "count": count}
    time.sleep(0.2)
```

Compute:
- **Count and percentage by contract type**
- **Dominant type**: which pricing type represents the plurality?
- Present in descending order by count

### Step 6: Competition Analysis (Government-Wide)

**Use `extent_competed_type_codes` filter + `spending_by_award_count`.**

```python
competed_filters = {**govwide_filters, "extent_competed_type_codes": ["A","D","F","CDO"]}
competed_count = get_count(competed_filters)

sole_source_filters = {**govwide_filters, "extent_competed_type_codes": ["B","C","E","G","NDO"]}
sole_source_count = get_count(sole_source_filters)

unclassified = total_govwide - competed_count - sole_source_count
```

Note: competed + sole source may not equal total. Some awards have null competition data. Report the unclassified count: "Of X awards, Y had missing competition data and were excluded."

### Step 7: Small Business Analysis (Government-Wide)

**Use `set_aside_type_codes` filter + `spending_by_award_count`** for each category.

```python
# All SB combined
all_sb_codes = ["SBA","SBP","8A","8AN","HZC","HZS","SDVOSBS","SDVOSBC",
                "WOSB","WOSBSS","EDWOSB","EDWOSBSS","VSA"]
sb_total = get_count({**govwide_filters, "set_aside_type_codes": all_sb_codes})

# Breakdown by major category
sb_categories = {
    "Small Business (SBA/SBP)": ["SBA", "SBP"],
    "8(a)": ["8A", "8AN"],
    "HUBZone": ["HZC", "HZS"],
    "SDVOSB": ["SDVOSBS", "SDVOSBC"],
    "WOSB/EDWOSB": ["WOSB", "WOSBSS", "EDWOSB", "EDWOSBSS"],
    "VSA (Veteran)": ["VSA"]
}
```

Compute:
- **Overall SB set-aside participation rate** (sb_total / total_govwide)
- **Breakdown by socioeconomic category**
- Note: this measures set-aside awards only. Small businesses also win full-and-open competitions, so the actual SB participation rate is higher than the set-aside rate. Mention this nuance in the report.

**Identifying top SB vendors for Rule of Two:** The main vendor landscape (Step 4) pulls top vendors by total obligations, which are typically large businesses for broad NAICS codes. To support Rule of Two assessments, run a separate `spending_by_category/recipient` call with `set_aside_type_codes` to identify the top small business vendors specifically:

```python
sb_vendor_filters = {**govwide_filters, "set_aside_type_codes": all_sb_codes}
sb_vendors = api_post("/api/v2/search/spending_by_category/recipient/",
                      {"filters": sb_vendor_filters, "limit": 10, "page": 1})
```

If this returns 2+ vendors with meaningful obligations, note their names in the Small Business section narrative to strengthen the Rule of Two justification. This is optional but recommended when the set-aside rate is between 20-40% and the decision is borderline.

### Step 8: Spending Trend (Government-Wide)

**Use `spending_over_time` endpoint** with `group: "fiscal_year"` and govwide filters.

```python
def get_spending_trend(filters):
    payload = json.dumps({"group": "fiscal_year", "filters": filters})
    url = "https://api.usaspending.gov/api/v2/search/spending_over_time/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

**CRITICAL: `fiscal_year` is a string.** The API returns `time_period.fiscal_year` as a string (e.g., `"2025"`). You MUST cast to integer before comparing against computed FY values. In Python: `int(r["time_period"]["fiscal_year"])`. In JavaScript: `parseInt(r.time_period.fiscal_year)`. Without this cast, partial-FY detection, YoY exclusion, and market characterization all silently fail (e.g., `"2026" === 2026` is `false` in JS).

**Handling negative fiscal years:** Deobligations can exceed new obligations in a given FY, especially for narrow scopes or PSC filters. This typically reflects closeout activity, not a shrinking market. The narrative should explain: "Negative values in FY20XX represent net deobligations (contract closeout adjustments exceeding new award activity within the filtered scope), which is normal for NAICS codes with large multi-year contracts."

**Partial fiscal year labeling:** Two fiscal years may be partial in the trend table:
- The **current FY** (if the query date is before September 30): label as "Partial year" in the Notes column
- The **first FY in the lookback**: if the lookback start date falls after October 1 of that fiscal year, the first FY is also partial. For example, a lookback starting March 15, 2021 means FY2021 (Oct 2020 - Sep 2021) is missing Oct-Mar data. Label it "Partial year (lookback starts [date])" in the Notes column.
- Exclude partial fiscal years from YoY growth calculations and market characterization narratives. Compare only full fiscal years when describing growth trends.

**Market characterization filter (explicit logic):** After building the trend array, filter to only full FYs before computing growth:

```python
# Cast fiscal_year from string to int (API returns strings)
trend = [{"fy": int(r["time_period"]["fiscal_year"]), "amount": r["aggregated_amount"]} for r in results]

# Determine which FYs are partial
current_fy = datetime.now().year + 1 if datetime.now().month >= 10 else datetime.now().year
lookback_start_fy = lookback_start.year + 1 if lookback_start.month >= 10 else lookback_start.year
first_fy_partial = lookback_start > datetime(lookback_start_fy - 1, 10, 1)

# Filter to full FYs only
full_fys = [t for t in trend if t["fy"] != current_fy and not (t["fy"] == lookback_start_fy and first_fy_partial)]

# Characterize using first and last full FYs
if len(full_fys) >= 2:
    growth = (full_fys[-1]["amount"] - full_fys[0]["amount"]) / abs(full_fys[0]["amount"])
    # >15% = growing, <-15% = contracting, else stable
```

Both the **YoY column** and the **narrative paragraph** must use this filtered set. A common bug is filtering for the narrative but forgetting to suppress YoY on partial-FY rows in the table.

**Limitation:** This endpoint returns dollar amounts only, not award counts per year. The skill does not provide award count trends over time. Note this limitation if the user asks about it.

### Step 9: Formulate Recommendations

Based on Steps 2 through 8, generate recommendations for three decision areas:

**1. Set-Aside Recommendation**

Apply the Rule of Two logic:
- If SB set-aside rate exceeds 40% AND at least 2 capable small businesses appear in the SB vendor lookup (Step 7) or overall vendor landscape: recommend a small business set-aside.
- If a specific socioeconomic category (8(a), HUBZone, SDVOSB, WOSB) shows strong participation (>15% of total) AND the user expressed interest: recommend that specific set-aside.
- If SB set-aside rate is below 20%: recommend full and open competition with SB subcontracting plan requirement. Note the top SB vendors from Step 7 if available; they may still support a set-aside if the sources sought confirms capability.
- Between 20% and 40%: present both options with supporting data. Recommend a sources sought notice to identify capable small businesses before deciding. Name the top SB vendors from Step 7 to demonstrate that capable firms exist.
- Always note: set-aside rate understates true SB participation because SBs also compete in unrestricted competitions.

**2. Contract Type Recommendation**

- If FFP >60% of comparable awards: recommend FFP.
- If T&M/Labor Hours (Y+Z combined) dominate: recommend T&M or Labor Hours.
- If mixed: recommend the plurality type but note the diversity.
- Note that historical patterns inform but do not dictate: if the requirement involves uncertain scope, T&M may be appropriate regardless of market norms.

**3. Competition Strategy**

- If competition rate >75%: recommend full and open (or set-aside competition per above).
- If sole source rate >40%: note the pattern but recommend competition unless a specific J&A basis applies.
- If vendor concentration is high (top vendor >40% share): note potential limited source concern.

**All recommendations must cite specific data.** Example: "Based on 41,433 comparable awards in NAICS 541512 from FY2021 through FY2026, 83.2% used firm fixed price contracting, supporting an FFP approach for this requirement."

### Step 10: Produce the DOCX Report

**Use the DOCX skill (docx-js via npm).** Follow the DOCX skill's rules for page size, fonts, tables, and lists.

Generate a formal DOCX with these sections:

**Document Layout:**
- US Letter (12240 x 15840 DXA), 1-inch margins
- Arial font, 12pt body, headings per DOCX skill style guidance
- Table of Contents (using HeadingLevel styles)
- Page numbers in footer

**Section Structure:**

**Cover / Title Block**
- Title: "Market Research Report"
- Subtitle: requirement description
- NAICS code, PSC code (if provided)
- Date prepared
- Prepared by: [leave blank for user to fill]
- Layout: Add vertical spacing before the title block (approximately 4000-5000 DXA / ~3 inches of `spacing.before` on the first paragraph) to position the title group in the upper-middle third of the page. This prevents the title from sitting at the very top with empty space below. Follow the "Prepared by" line with a page break so Section 1 starts on a fresh page.

**1. Purpose and Scope**
- Brief statement of the requirement
- FAR Part 10 authority citation
- Scope of research: note both government-wide and agency-specific scopes used, with the lookback period

**2. Methodology**
- Data source: USASpending.gov (FPDS-sourced federal award data)
- Search parameters: NAICS, PSC, keywords, date range, agency, dollar range
- Dual-scope approach explanation: government-wide for statistical sections, agency-scoped for comparable awards
- Query date
- Limitations: FPDS data only; does not include commercial market data, GSA Advantage pricing, or vendor capability statements. Set-aside analysis reflects only set-aside awards, not total SB participation. Spending trend shows obligations, not award counts.

**3. Market Overview (Government-Wide)**
- Total comparable awards found (from spending_by_award_count)
- Annual spending trend (table: fiscal year, obligations, year-over-year change)
- Explain any negative fiscal years as closeout deobligations
- Market characterization: growing, stable, or contracting

**4. Prior Award Analysis ([Agency] or Government-Wide)**
- Label the scope clearly
- Table of top 15-20 comparable awards: PIID, Vendor, Amount, Start Date, End Date, Awarding Agency (6 columns). Description is omitted from the table for column width reasons; if space permits or the user requests it, include a truncated Description column or add descriptions in a separate appendix table.
- **Use landscape orientation for the prior award table section.** Six columns with billion-dollar amounts, full PIIDs, and agency names do not fit in portrait US Letter without wrapping. Create a separate landscape section (using a docx-js section break with `orientation: PageOrientation.LANDSCAPE`) for Section 4, then switch back to portrait for Section 5. If landscape is not feasible, drop Start Date (keep End Date only) to reduce to 5 columns, or abbreviate amounts to millions (e.g., "$2,087M").
- **Column character limits for landscape (12,960 DXA content width):** PIID: 20 chars (~2,000 DXA), Vendor: 35 chars (~3,200 DXA), Amount: ~1,800 DXA, Start Date: ~1,500 DXA, End Date: ~1,500 DXA, Awarding Agency: 35 chars (~2,960 DXA). Truncate vendor names and agency names that exceed limits. Do not truncate PIIDs.
- **Footer re-definition across section breaks:** docx-js section breaks reset headers and footers. Re-define the footer paragraph (with page numbers) in every section: the portrait opening section, the landscape Section 4 section, and the portrait Section 5+ section. Without this, page numbers disappear after the first section break.
- Exclude $0 awards from the table
- Award value distribution summary (max, median, mean only; omit min) based on positive-value awards, with explicit label: "Top Awards Sample" and a note that these are not population statistics
- If agency-scoped results are thin (<20 awards), note this and include the total government-wide count for context

**5. Vendor Landscape ([Agency] or Government-Wide)**
- Table of top N vendors: rank, vendor name, total obligations, market share %
- Four columns only; do not include a Notes column. Mark dedup footnotes inline with an asterisk on the vendor name (e.g., "BOOZ ALLEN HAMILTON INC *") and explain below the table.
- Handle negative vendor amounts: list separately or note as deobligations
- Market concentration analysis (top 5 share)
- Number of unique vendors

**6. Small Business Availability (Government-Wide)**
- Overall SB set-aside participation rate (by count)
- Breakdown table by socioeconomic category: three columns (Category, Awards, % of Total). Do not include a Notes column.
- Use "All SB Set-Asides Combined" as a summary row, then list subcategories. Use "Small Business (SBA/SBP)" for the generic SB set-aside codes to distinguish from the combined total.
- Rule of Two assessment
- If SB vendor identification was performed (Step 7), name the top 2-3 SB vendors to support the assessment
- Note that set-aside rate is a lower bound on actual SB participation

**7. Contract Type Analysis (Government-Wide)**
- Distribution table: contract type, award count, % of total. Three columns only; do not include a Notes column.
- Dominant type identification
- Summary of FFP vs. T&M/LH vs. cost-type proportions

**8. Competition Analysis (Government-Wide)**
- Competed vs. not competed: counts and percentages. Three columns only (Category, Awards, % of Total); do not include a Notes column.
- Unclassified count noted if nonzero

**9. Findings and Recommendations**
- Set-aside recommendation with supporting data
- Contract type recommendation with supporting data
- Competition strategy recommendation
- Additional observations (e.g., thin agency dataset, IDV vehicle considerations, seasonal patterns)

**10. Data Sources and Certification**
- Full list of API endpoints called and parameters used
- Date of data retrieval
- Certification block with signature/date lines

**Appendix A: Raw Query Parameters**
- JSON of the two base filter objects: government-wide and agency-scoped (if applicable)
- Condensed table of all API calls made: Endpoint URL, Filter Variant (e.g., "base", "FFP pricing type", "competed", "SB set-aside"), Record Count returned. Do not dump full JSON for every filter variant; the base filters plus the variant description are sufficient for reproducibility.
- Endpoint URLs used
- Total record counts

**Formatting Standards:**
- Tables: light gray header fill (#D5E8F0), 1pt borders (#CCCCCC), cell padding (80/80/120/120 DXA)
- Percentages to 1 decimal place
- Dollar amounts with comma separators, no decimals for amounts >$1,000
- Page break before each major section

After generating the DOCX, validate:
```bash
python /mnt/skills/public/docx/scripts/office/validate.py output.docx
```

**TOC update requirement:** The docx-js `TableOfContents` element generates a TOC field code that requires the reader application to "Update Fields" on first open. In Microsoft Word, the user is prompted automatically ("This document contains fields that may refer to other files. Do you want to update...?"). In LibreOffice, the user must right-click the TOC and select "Update Index." In Google Docs, the TOC may remain empty. Note this to the user when delivering the report: "Right-click the Table of Contents and select Update to populate page numbers."

## Handling Edge Cases

### Zero Results from USASpending

If the initial count returns zero:
1. Broaden: remove keywords, use 2-digit NAICS prefix, extend lookback to 7 years.
2. Remove PSC filter (if applied).
3. If still zero: generate the DOCX with "No comparable federal awards found." Recommend supplementing with commercial market research, SAM.gov entity searches, and sources sought notices.

### Too Many Results (>10,000 Awards)

If `spending_by_award_count` returns >10,000 contracts:
- Ask the user if they want to narrow by PSC, dollar range, or agency before proceeding.
- If proceeding, the count-based analysis (Steps 5-7) works fine at any scale. Cap the prior award table pull (Step 3) at 300 records (3 pages).

### NAICS / PSC Mismatch

If autocomplete validation returns a different description than expected, present the mismatch to the user before proceeding.

### IDV Analysis

Default filter uses contract codes `["A","B","C","D"]`. If the user mentions GWACs, BPAs, or GSA Schedule:
- Run a separate count with IDV codes `["IDV_A","IDV_B","IDV_B_A","IDV_B_B","IDV_B_C","IDV_C","IDV_D","IDV_E"]`
- Include IDV results in a separate subsection of the Prior Award Analysis
- Note in methodology that both contract and IDV awards were analyzed

### Missing Competition Data

Some awards have null competition extent. Report the gap: "Of X total awards, Y were competed, Z were not competed, and W had missing competition data."

### Stale Data

USASpending FPDS data is typically 1 business day behind. Note the retrieval date in methodology with a standard caveat.

## Quick Start Examples

**Simple:** "Do market research for IT help desk services, NAICS 541512"

Claude will: validate 541512, build government-wide 5-year filters, run count-based analysis for contract type/competition/SB, pull agency-scoped prior awards, generate DOCX with full FAR Part 10 analysis.

**Scoped:** "Market research for cybersecurity services, NAICS 541512, PSC D399, NAVSEA only, last 3 years, $500K-$5M"

Claude will: validate codes, build dual-scope filters, run all pulls. Note if the agency-scoped results are thin and supplement with gov-wide context.

**With set-aside interest:** "Market research for NAICS 541519, interested in small business set-aside"

Claude will: run standard analysis with extra emphasis on SB data, Rule of Two assessment, and socioeconomic breakdown. Recommendations directly address the set-aside question.

## What This Skill Does NOT Cover

Note in the methodology section:

- **Commercial market data**: GSA Advantage, commercial pricing, Gartner/Forrester. USASpending covers federal awards only.
- **Vendor capability statements**: SAM.gov entity registrations, past performance references.
- **GSA Schedule pricing**: MAS rate analysis requires the CALC+ skill.
- **Sources sought / RFI responses**: active market engagement complements this desk research.
- **State/local government data**: federal awards only.
- **Subcontract data**: limited in USASpending; prime award analysis only.
- **Price analysis**: this skill produces market research, not pricing analysis. For pricing, use the IGCE Builder skill.
- **Award count trends over time**: the spending_over_time endpoint returns dollars only, not counts per year.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*