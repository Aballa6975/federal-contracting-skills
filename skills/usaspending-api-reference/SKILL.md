---
name: usaspending-api-reference
description: Reference file for the USASpending API skill. Do not trigger directly. Contains filter value tables, composite workflows, bulk download, loan search, reference endpoints, PSC codes, and troubleshooting. Loaded on demand by the main usaspending-api skill.
---

# USASpending API Reference

Supplemental reference for the USASpending API skill. Load on demand when you need filter codes, composite workflows, or troubleshooting.

## Table of Contents
1. Filter Value Reference Tables
2. Composite Workflows
3. Bulk Download
4. Loan Search
5. Award Funding (File C)
6. Reference Endpoints
7. PSC Code Reference (Common IT/Services Codes)
8. Vendor Deduplication Notes
9. Troubleshooting

---

## 1. Filter Value Reference Tables

### contract_pricing_type_codes

| Code | Description |
|------|-------------|
| A | Fixed Price Redetermination |
| B | Fixed Price Level of Effort |
| J | Firm Fixed Price |
| K | Fixed Price with Economic Price Adjustment |
| L | Fixed Price Incentive |
| M | Fixed Price Award Fee |
| R | Cost Plus Award Fee |
| S | Cost No Fee |
| T | Cost Sharing |
| U | Cost Plus Fixed Fee |
| V | Cost Plus Incentive Fee |
| Y | Time and Materials |
| Z | Labor Hours |

### extent_competed_type_codes

| Code | Description |
|------|-------------|
| A | Full and Open Competition |
| B | Not Available for Competition |
| C | Not Competed |
| D | Full and Open after Exclusion of Sources |
| E | Follow On to Competed Action |
| F | Competed under SAP |
| G | Not Competed under SAP |
| CDO | Competitive Delivery Order |
| NDO | Non-Competitive Delivery Order |

Useful groupings: competed = `["A","D","F","CDO"]`, not competed = `["B","C","E","G","NDO"]`.

### set_aside_type_codes

| Code | Description |
|------|-------------|
| SBA | Small Business Set-Aside (Total) |
| SBP | Small Business Set-Aside (Partial) |
| 8A | 8(a) Competitive |
| 8AN | 8(a) Sole Source |
| HZC | HUBZone Set-Aside |
| HZS | HUBZone Sole Source |
| SDVOSBS | SDVOSB Set-Aside |
| SDVOSBC | SDVOSB Sole Source |
| WOSB | WOSB Set-Aside |
| WOSBSS | WOSB Sole Source |
| EDWOSB | EDWOSB Set-Aside |
| EDWOSBSS | EDWOSB Sole Source |
| VSA | Veteran Set-Aside |

Useful groupings: all SB = `["SBA","SBP","8A","8AN","HZC","HZS","SDVOSBS","SDVOSBC","WOSB","WOSBSS","EDWOSB","EDWOSBSS","VSA"]`, 8(a) = `["8A","8AN"]`, SDVOSB = `["SDVOSBS","SDVOSBC"]`, WOSB/EDWOSB = `["WOSB","WOSBSS","EDWOSB","EDWOSBSS"]`.

---

## 2. Composite Workflows

### Enrich Contract Court / PRISM Descriptions

Problem: PRISM overwrites the description field with the latest modification text.

```python
def get_base_description(piid):
    """Get the original base award description for a PIID."""
    award_types = detect_award_type(piid)
    result = search_awards(piid, award_types,
                           fields=["Award ID", "Description", "Award Amount",
                                   "Recipient Name", "generated_internal_id"])
    awards = result.get('results', [])
    if not awards and 'IDV' not in str(award_types):
        award_types = ["IDV_A","IDV_B","IDV_B_A","IDV_B_B","IDV_B_C","IDV_C","IDV_D","IDV_E"]
        result = search_awards(piid, award_types,
                               fields=["Award ID", "Description", "Award Amount",
                                        "Recipient Name", "generated_internal_id"])
        awards = result.get('results', [])
    return awards[0] if awards else None
```

### Batch PIID Lookup

```python
import time

def batch_lookup_descriptions(piids):
    """Look up base descriptions for a list of PIIDs."""
    results = {}
    for piid in piids:
        try:
            award = get_base_description(piid)
            if award:
                results[piid] = {'description': award.get('Description'),
                    'amount': award.get('Award Amount'),
                    'recipient': award.get('Recipient Name'),
                    'internal_id': award.get('generated_internal_id')}
            else:
                results[piid] = None
        except Exception as e:
            results[piid] = {'error': str(e)}
        time.sleep(0.3)
    return results
```

### Get Full Award Lifecycle

```python
def get_award_lifecycle(piid):
    """Get complete award info: base description + all modifications."""
    award = get_base_description(piid)
    if not award:
        return None
    internal_id = award.get('generated_internal_id')
    detail = get_award_detail(internal_id)
    transactions = get_transactions(internal_id, limit=100)
    return {'award': detail, 'transactions': transactions.get('results', [])}
```

### Dimensional Analysis with Award Counts

```python
# Count FFP awards
ffp_filters = {**base_filters, "contract_pricing_type_codes": ["J"]}
ffp_count = get_award_counts(ffp_filters)["results"]["contracts"]

# Count competed awards
comp_filters = {**base_filters, "extent_competed_type_codes": ["A","D","F","CDO"]}
comp_count = get_award_counts(comp_filters)["results"]["contracts"]

# Count small business set-aside awards
sb_filters = {**base_filters, "set_aside_type_codes": ["SBA","SBP","8A","8AN"]}
sb_count = get_award_counts(sb_filters)["results"]["contracts"]
```

### Top Small Business Vendors

```python
sb_vendor_filters = {**base_filters, "set_aside_type_codes": ["SBA","SBP","8A","8AN","HZC","HZS","SDVOSBS","SDVOSBC","WOSB","WOSBSS","EDWOSB","EDWOSBSS","VSA"]}
sb_vendors = spending_by_category("recipient", sb_vendor_filters, limit=15)
```

---

## 3. Bulk Download

**Endpoint:** `POST /api/v2/bulk_download/awards/`

Async: returns download URL. Uses DIFFERENT filter structure than search endpoints.

```python
def request_bulk_download(filters):
    payload = json.dumps({"filters": filters, "columns": [], "file_format": "csv"})
    url = "https://api.usaspending.gov/api/v2/bulk_download/awards/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())
```

Key differences from search filters:
- `"prime_award_types"` instead of `"award_type_codes"`
- `"date_range": {"start_date": "...", "end_date": "..."}` (object) instead of `"time_period"` (array)
- Requires `"date_type"` field (e.g., `"action_date"`)

---

## 4. Loan Search

Loans use different field names. "Award Amount" returns HTTP 400; use "Loan Value".

```python
def search_loans(keywords, limit=10):
    payload = json.dumps({
        "subawards": False, "limit": min(limit, 100), "page": 1,
        "sort": "Loan Value", "order": "desc",
        "filters": {
            "keywords": keywords if isinstance(keywords, list) else [keywords],
            "award_type_codes": ["07", "08"]
        },
        "fields": ["Award ID", "Recipient Name", "Recipient UEI", "Description",
                    "Loan Value", "Subsidy Cost", "Awarding Agency", "Awarding Sub Agency",
                    "generated_internal_id", "Last Modified Date"]
    })
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

---

## 5. Award Funding (File C Data)

**Endpoint:** `POST /api/v2/awards/funding/`

Federal account, object class, and program activity data linked to an award.

```python
def get_award_funding(generated_award_id):
    payload = json.dumps({"award_id": generated_award_id, "limit": 50, "page": 1})
    url = "https://api.usaspending.gov/api/v2/awards/funding/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Sort fields: reporting_fiscal_date, account_title, transaction_obligated_amount, object_class.

---

## 6. Reference Endpoints (GET)

| Endpoint | Use |
|----------|-----|
| `/api/v2/references/toptier_agencies/` | All top-tier agencies |
| `/api/v2/references/naics/<CODE>/` | NAICS code details (2-6 digit) |
| `/api/v2/references/filter_tree/psc/` | PSC hierarchy (drillable: `/psc/Service/R/`) |
| `/api/v2/references/submission_periods/` | Available reporting periods |
| `/api/v2/references/def_codes/` | Disaster/emergency fund codes |
| `/api/v2/references/data_dictionary/` | Full data dictionary |
| `/api/v2/references/glossary/` | Glossary terms |
| `/api/v2/recipient/state/<FIPS>/` | State spending profile |
| `/api/v2/agency/<CODE>/` | Agency overview (?fiscal_year=YYYY) |
| `/api/v2/agency/<CODE>/awards/` | Agency award summary |

---

## 7. PSC Code Reference (Common IT/Services Codes)

| Code | Description |
|------|-------------|
| AN11 | R&D: Health Care Services, Basic Research |
| AN91 | R&D: Other Research and Development, Basic Research |
| AJ11 | R&D: General Science/Technology, Basic Research |
| AJ12 | R&D: General Science/Technology, Applied Research |
| AZ11 | R&D: Other R&D, Basic Research |
| R499 | Other Professional Services |
| D399 | IT and Telecom: Other IT and Telecommunications |
| DA01 | IT and Telecom: Application Development Support |
| S112 | Utilities: Electric |

---

## 8. Vendor Deduplication Notes

The `recipient` category returns results by unique entity (UEI). Large companies often appear multiple times due to subsidiaries, divisions, or re-registrations. When using for vendor landscape analysis:
- Vendor counts may overstate unique companies
- Market share may be split across multiple entries
- No built-in dedup; apply case-insensitive name matching if precision matters
- Name normalization catches suffix variations but not acquisitions/rebrands (e.g., Cerner to Oracle Health Government Services; Northrop Grumman acquired Peraton)
- Vendor names return in ALL CAPS; title-case for reports but preserve LLC/INC/LLP in uppercase

---

## 9. Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| 422 "award_type_codes must only contain types from one group" | Mixed contract + IDV codes | Separate into two requests |
| 422 "Invalid value in filters\|psc_codes" | Empty `"exclude": []` | Remove exclude key or use simple array |
| 422 "Field 'limit' value above max" | limit > 100 (search) or > 5000 (transactions) | Reduce limit; paginate |
| 400 "Sort value not found in requested fields" | Sort field not in fields array | Add sort field to fields |
| 400 "Sort value not found in Loan Award mappings" | "Award Amount" with loan codes | Use "Loan Value" for loans |
| 400 "Invalid value in filters\|keywords" | Empty keywords array | Omit keywords filter entirely |
| Empty results for known PIID | Wrong award type group | Try contracts then IDVs |
| Null values for valid fields | Typo in field name (API accepts anything) | Verify field spelling |
| Truncated description | FPDS 4000-char limit | Normal; use what's available |
| Stale data | FPDS nightly updates | Typically 1 business day behind |
