---
name: usaspending-api
description: Query the USASpending.gov REST API for federal contract and award data. Use this skill whenever the user asks about federal spending data, contract descriptions, award details, transaction histories, vendor/recipient lookups, obligation amounts, agency spending breakdowns, PSC/NAICS code lookups, or any procurement research that involves USASpending, FPDS, or FAADC data. Also trigger when the user needs to enrich internal contract data (PRISM, FPDS, ALP, Contract Court) with base award descriptions, transaction histories, or award metadata. Trigger for any mention of USASpending, FPDS, federal awards, PIIDs, FAINs, award IDs, or federal spending analysis. This skill is essential for daily contract portfolio management, description enrichment, and procurement intelligence work.
---

# USASpending.gov API Skill

## Overview

The USASpending.gov API (https://api.usaspending.gov) provides free, no-auth access to all federal spending data sourced from FPDS, FAADC, and agency DATA Act submissions. No API key required.

Base URL: `https://api.usaspending.gov`

**For filter value tables, composite workflows, reference endpoints, PSC codes, and troubleshooting:** `view` the REFERENCE.md file in this skill directory.

## Critical Rules

### 1. Award Type Code Groups (MOST COMMON ERROR)
Award type codes MUST NOT be mixed across groups. The API returns HTTP 422 if you mix them.

- **Contracts:** `["A", "B", "C", "D"]` (A=BPA Call, B=PO, C=DO, D=Definitive)
- **IDVs:** `["IDV_A", "IDV_B", "IDV_B_A", "IDV_B_B", "IDV_B_C", "IDV_C", "IDV_D", "IDV_E"]`
- **Grants:** `["02", "03", "04", "05"]`
- **Loans:** `["07", "08"]` (use "Loan Value" not "Award Amount")
- **Direct Payments:** `["06", "10"]`
- **Other:** `["09", "11", "-1"]`

### 2. PIID Type Detection
PIID formats vary by agency. Example: NAVSEA PIIDs start with N00024 (e.g., N0002425CXXXX). Other DoD prefixes: W91CRB (Army Contracting Command), FA8650 (AFRL). If the agency format is unknown, try contracts first, then IDVs if 0 results.

```python
def detect_award_type(piid):
    if piid.startswith("N00024") and len(piid) >= 9:
        return ["IDV_B_B"] if piid[8] == 'D' else ["A", "B", "C", "D"]
    return ["A", "B", "C", "D"]
```

### 3. Sort Field Must Be in Fields Array
The `sort` value MUST appear in `fields` or the API returns HTTP 400.

### 4. Endpoint Limit Caps
- Search endpoints: max `limit` = 100
- Transactions endpoint: max `limit` = 5000
- Paginate with `page` parameter

### 5. No Total Count in page_metadata
`spending_by_award` has no `total` field. Use `spending_by_award_count` for totals.

### 6. PSC/NAICS Filter Format
Do NOT include empty `"exclude": []`. Use simple arrays: `"psc_codes": ["R499"]`.

### 7. Contract Award Type vs Pricing Type
`Contract Award Type` in search = how issued (BPA Call, PO, DO, Definitive). For pricing type (FFP, T&M, etc.), use award detail endpoint or `contract_pricing_type_codes` filter.

### 8. Generated Award IDs
Format: `CONT_AWD_[PIID]_[AGENCY]_[PARENT_PIID]_[PARENT_AGENCY]` or `CONT_IDV_[PIID]_[AGENCY]`.

---

## Core Endpoints

### 1. Award Search (PRIMARY WORKHORSE)

**Endpoint:** `POST /api/v2/search/spending_by_award/`

```python
import urllib.request, json

def search_awards(keywords, award_type_codes, fields=None, limit=10, page=1, sort="Award Amount"):
    if fields is None:
        fields = ["Award ID", "Description", "Award Amount", "Recipient Name",
                  "Start Date", "End Date", "generated_internal_id",
                  "Awarding Agency", "Awarding Sub Agency", "PSC", "NAICS"]
    if sort not in fields:
        fields.append(sort)
    payload = json.dumps({
        "subawards": False, "limit": min(limit, 100), "page": page,
        "sort": sort, "order": "desc",
        "filters": {
            "keywords": keywords if isinstance(keywords, list) else [keywords],
            "award_type_codes": award_type_codes
        }, "fields": fields
    })
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

**Contract fields:** Award ID, Recipient Name, Recipient UEI, Description, Awarding Agency, Awarding Sub Agency, Funding Agency, Funding Sub Agency, generated_internal_id, Start Date, End Date, Award Amount, Total Outlays, Contract Award Type, NAICS, PSC, def_codes, Last Modified Date, Base Obligation Date

**IDV fields:** Same base plus Last Date to Order (no End Date).

**Loan fields:** Use "Loan Value" and "Subsidy Cost" instead of "Award Amount". Sort by "Loan Value".

**Note on `award_ids` filter:** Use plain strings: `"award_ids": ["N0002424C0085"]`. Performs prefix match.

### 2. Award Detail

**Endpoint:** `GET /api/v2/awards/<GENERATED_AWARD_ID>/`

```python
def get_award_detail(generated_id):
    url = f"https://api.usaspending.gov/api/v2/awards/{generated_id}/"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Returns: piid, description, total_obligation, date_signed, recipient, parent_award, latest_transaction_contract_data (competition, set-aside, pricing type), period_of_performance, place_of_performance, naics_hierarchy, psc_hierarchy, base_and_all_options, total_subaward_amount.

### 3. Transaction History

**Endpoint:** `POST /api/v2/transactions/`

```python
def get_transactions(generated_award_id, limit=100, sort="action_date", order="asc"):
    payload = json.dumps({
        "award_id": generated_award_id, "page": 1,
        "sort": sort, "order": order, "limit": min(limit, 5000)
    })
    url = "https://api.usaspending.gov/api/v2/transactions/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Returns per transaction: id, type, action_date, action_type, modification_number, description, federal_action_obligation. Mod 0 = original base award description.

### 4. Agency-Filtered Search

```python
filters = {
    "award_type_codes": ["A", "B", "C", "D"],
    "agencies": [{"type": "awarding", "tier": "subtier",
                  "name": "Naval Sea Systems Command",
                  "toptier_name": "Department of Defense"}],
    "time_period": [{"start_date": "2024-10-01", "end_date": "2025-09-30"}]
}
```

DoD constants: toptier code 097 (Defense). Navy subtier 1700. Example NAVSEA PIID format N00024[YY][type][NNNN].

### 5. IDV Child Awards

**Endpoint:** `POST /api/v2/idvs/awards/`

```python
def get_idv_children(generated_idv_id, award_type="child_awards"):
    payload = json.dumps({
        "award_id": generated_idv_id, "type": award_type,
        "limit": 50, "page": 1,
        "sort": "period_of_performance_start_date", "order": "desc"
    })
    url = "https://api.usaspending.gov/api/v2/idvs/awards/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

**Field name differences:** IDV children use `piid` (not "Award ID"), `obligated_amount` (not "Award Amount"), `generated_unique_award_id` (not "generated_internal_id").

### 6. Spending by Category

**Endpoint:** `POST /api/v2/search/spending_by_category/<CATEGORY>/`

Category MUST be in URL path. Categories: awarding_agency, awarding_subagency, funding_agency, funding_subagency, recipient, cfda, naics, psc, country, county, district, state_territory, federal_account, defc.

```python
def spending_by_category(category, filters, limit=10):
    payload = json.dumps({"filters": filters, "limit": limit, "page": 1})
    url = f"https://api.usaspending.gov/api/v2/search/spending_by_category/{category}/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Recipient results: `amount` (net obligations, can be negative), `name` (ALL CAPS), `recipient_id`, `uei`. Vendor dedup warning: large companies appear multiple times under different UEIs (subsidiaries, rebrands, acquisitions). See REFERENCE.md for details.

### 7. Spending Over Time

**Endpoint:** `POST /api/v2/search/spending_over_time/`

```python
def spending_over_time(filters, group="fiscal_year"):
    payload = json.dumps({"group": group, "filters": filters})
    url = "https://api.usaspending.gov/api/v2/search/spending_over_time/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

**CRITICAL:** `fiscal_year` is returned as a **string**. Cast to int before numeric comparison.

### 8. Award Count

**Endpoint:** `POST /api/v2/search/spending_by_award_count/`

```python
def get_award_counts(filters):
    payload = json.dumps({"filters": filters})
    url = "https://api.usaspending.gov/api/v2/search/spending_by_award_count/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Returns counts by group: `contracts`, `idvs`, `grants`, `loans`, `direct_payments`, `other`. Use with dimensional filters (contract_pricing_type_codes, extent_competed_type_codes, set_aside_type_codes) for aggregate analysis.

### 9. Autocomplete Endpoints

```python
def autocomplete_psc(search_text):
    payload = json.dumps({"search_text": search_text, "limit": 10})
    url = "https://api.usaspending.gov/api/v2/autocomplete/psc/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())

def autocomplete_naics(search_text):
    payload = json.dumps({"search_text": search_text, "limit": 10})
    url = "https://api.usaspending.gov/api/v2/autocomplete/naics/"
    req = urllib.request.Request(url, data=payload.encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode())
```

PSC autocomplete works best with code prefixes ("R499") or single keywords ("professional").

---

## Common Filter Object

```python
filters = {
    "award_type_codes": ["A","B","C","D"],  # MUST be from same group
    "keywords": ["search term"],
    "time_period": [{"start_date": "2024-10-01", "end_date": "2025-09-30"}],
    "agencies": [{"type": "awarding", "tier": "subtier", "name": "..."}],
    "recipient_search_text": ["vendor name"],
    "award_ids": ["PIID1"],  # Plain strings, prefix match
    "psc_codes": ["R499"],  # Simple array, no empty exclude
    "naics_codes": ["541512"],
    "place_of_performance_locations": [{"country": "USA", "state": "MD"}],
    "award_amounts": [{"lower_bound": 1000000, "upper_bound": 10000000}],
    "set_aside_type_codes": ["SBA"],
    "extent_competed_type_codes": ["A"],
    "contract_pricing_type_codes": ["J"],
    "def_codes": ["L","M","N","O","P"]
}
```

---

## Rate Limiting

1. No auth needed; API is public and read-only
2. Add 0.3s delays between batch requests
3. Search max limit = 100; transactions max limit = 5000
4. API silently accepts invalid field names (returns null); verify spelling
5. Empty `keywords: []` returns HTTP 400; omit entirely if not needed

---

## Additional Resources

For filter value tables (contract_pricing_type_codes, extent_competed_type_codes, set_aside_type_codes), composite workflows (enrich descriptions, batch lookup, award lifecycle), bulk download, loan search, reference endpoints, PSC codes, and troubleshooting: `view` the **REFERENCE.md** file in this skill directory.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*