---
name: gsa-perdiem-rates
description: >
  Query the GSA Per Diem Rates API for federal travel lodging and M&IE
  (meals and incidental expenses) rates by city, state, ZIP code, or
  fiscal year. Trigger for any mention of per diem, lodging rates, M&IE,
  travel costs, travel CLINs, travel IGCE, contractor travel estimates,
  first/last day of travel, meal rates, incidental expenses, or GSA
  travel rates. Also trigger when the user needs to estimate travel costs
  for a proposal, build an IGCE with a travel component, evaluate
  contractor travel costs in a price proposal, compare per diem rates
  across locations, or look up seasonal lodging rate variations.
  Complements the BLS OEWS skill (labor wages), CALC+ skill (ceiling
  rates), and USASpending skill (award data) to cover the three biggest
  cost elements in professional services IGCEs.
---

# GSA Per Diem Rates API Skill

## Overview

The GSA Per Diem API provides CONUS federal per diem rates (lodging + M&IE). Rates are set annually per fiscal year (Oct 1 - Sep 30).

Base URL: `https://api.gsa.gov/travel/perdiem/v2/rates/`

**API Key:** Works with `DEMO_KEY` (~10 req/hr, shared IP pool). Register free at https://api.data.gov/signup/ for 1,000 req/hr. Pass as `?api_key=KEY` or header `x-api-key: KEY`.

**What this data is:** Maximum federal reimbursement ceilings for CONUS lodging and meals. Not actual hotel prices, not OCONUS rates (State Dept), not contractor-specific policies.

**For recipes (travel cost estimation, multi-location comparison, travel IGCE builder, ZIP lookup), common rates table, error handling, and response schemas:** `view` the REFERENCE.md file in this skill directory.

## Rate Structure

**Standard CONUS baseline (query the API for exact current values):** approximately $110/night lodging, $68/day M&IE. The baseline changes each October 1 when GSA publishes new fiscal-year rates.

**M&IE Tiers:**

| Total | Breakfast | Lunch | Dinner | Incidental | First/Last Day (75%) |
|-------|-----------|-------|--------|------------|---------------------|
| $68 | $16 | $19 | $28 | $5 | $51.00 |
| $74 | $18 | $20 | $31 | $5 | $55.50 |
| $80 | $20 | $22 | $33 | $5 | $60.00 |
| $86 | $22 | $23 | $36 | $5 | $64.50 |
| $92 | $23 | $26 | $38 | $5 | $69.00 |

First/last day at 75% per 41 CFR 301-11.101. FY rates announced mid-August, effective Oct 1. ~3 years of data available.

## API Endpoints

| # | Endpoint | Use |
|---|----------|-----|
| 1 | `/rates/city/{city}/state/{ST}/year/{year}` | Rates for a city |
| 2 | `/rates/state/{ST}/year/{year}` | All NSA rates for a state |
| 3 | `/rates/zip/{zip}/year/{year}` | Rates by ZIP code |
| 4 | `/rates/conus/lodging/{year}` | Bulk: all CONUS lodging |
| 5 | `/rates/conus/mie/{year}` | M&IE breakdown table |
| 6 | `/rates/conus/zipcodes/{year}` | ZIP-to-Destination ID mapping |

Path parameters are case-insensitive.

## Critical Rules

### 1. City Endpoint Uses Partial Prefix Matching
If query partially matches NSA names, returns ALL matching entries plus standard rate. If nothing matches, returns ALL state NSAs as fallback. Always check the `city` field in the response.

### 2. Composite NSA Names Use " / " Separators
"Boston / Cambridge", "Arlington / Fort Worth / Grapevine". Use substring matching: `if "Fort Worth" in rate["city"]`.

### 3. `standardRate` Field Is Unreliable
Always check `city == "Standard Rate"` instead.

### 4. Special Characters in City Names
Replace apostrophes/hyphens with spaces. **Keep periods for "St." prefix** cities (St. Louis, St. Petersburg). Removing the period causes partial match on "St" returning ALL state NSAs.

### 5. DC Returns "District of Columbia"
Query "Washington/DC" returns `city = "District of Columbia"`. The `get_best_rate` helper handles this.

### 6. ZIP May Return Multiple Entries
NSA rate + standard rate both returned. Prefer the non-standard entry.

### 7. Fiscal Year, Not Calendar Year
The federal fiscal year runs October through September. A date in the first calendar quarter (January-March) is still in the fiscal year that began the prior October. Compute the current FY at query time; do not hardcode.

### 8. Seasonal Lodging Variations
Many NSAs vary by month (DC: $183-$276). M&IE does NOT vary seasonally. Retrieve all 12 months for multi-month estimates.

### 9. Bulk Endpoint Returns Strings, City Endpoints Return Ints
Bulk: `"Jan": "110"` (string). City/ZIP: `"value": 110` (int). Convert with `int()` for bulk.

### 10. Standard Rate Has Null County
Guard with: `county = rate.get("county") or "N/A"`

### 11. Month Field Is "short" Not "short_month"
Use `m["short"]` for abbreviated month name.

### 12. Annual Rate Refresh
Common rates table in REFERENCE.md goes stale each August. Query the API directly after August for exact figures.

---

## Core Functions

```python
import urllib.request, json, urllib.parse

def get_perdiem_city(city, state, year, api_key="DEMO_KEY"):
    """Get per diem for a city/state/fiscal year."""
    city_encoded = urllib.parse.quote(city.replace("'", " ").replace("-", " "))
    url = (f"https://api.gsa.gov/travel/perdiem/v2/rates/"
           f"city/{city_encoded}/state/{state}/year/{year}?api_key={api_key}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get_perdiem_zip(zip_code, year, api_key="DEMO_KEY"):
    """Get per diem by ZIP. May return multiple entries; prefer non-standard."""
    url = (f"https://api.gsa.gov/travel/perdiem/v2/rates/"
           f"zip/{zip_code}/year/{year}?api_key={api_key}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get_perdiem_state(state, year, api_key="DEMO_KEY"):
    """Get all NSA rates for a state."""
    url = (f"https://api.gsa.gov/travel/perdiem/v2/rates/"
           f"state/{state}/year/{year}?api_key={api_key}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get_mie_breakdown(year, api_key="DEMO_KEY"):
    """Get M&IE tier breakdown (meal components)."""
    url = (f"https://api.gsa.gov/travel/perdiem/v2/rates/"
           f"conus/mie/{year}?api_key={api_key}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())

def get_bulk_lodging(year, api_key="DEMO_KEY"):
    """Get all CONUS lodging rates (~346 records). Bulk values are strings."""
    url = (f"https://api.gsa.gov/travel/perdiem/v2/rates/"
           f"conus/lodging/{year}?api_key={api_key}")
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### Parse and Select Best Rate

```python
def parse_rate_entry(rate_entry):
    """Parse one rate entry into a clean dict."""
    months = {m["short"]: m["value"] for m in rate_entry["months"]["month"]}
    is_standard = (rate_entry.get("city", "") == "Standard Rate")
    return {
        "city": rate_entry.get("city"),
        "county": rate_entry.get("county") or "N/A",
        "meals": rate_entry.get("meals"),
        "zip": rate_entry.get("zip"),
        "is_standard": is_standard,
        "lodging_by_month": months,
        "lodging_min": min(months.values()),
        "lodging_max": max(months.values()),
        "has_seasonal_variation": min(months.values()) != max(months.values()),
    }

def get_best_rate(response, query_city=None):
    """Extract best matching rate from response.
    Priority: exact city match > composite name match > first NSA > standard rate.
    """
    rates = response.get("rates", [])
    if not rates or not rates[0].get("rate"):
        return None
    parsed = [parse_rate_entry(e) for e in rates[0]["rate"]]
    if query_city:
        q = query_city.lower()
        exact = [p for p in parsed if p["city"] and p["city"].lower() == q]
        if exact: return exact[0]
        composite = [p for p in parsed if p["city"] and q in p["city"].lower() and p["city"] != "Standard Rate"]
        if composite: return composite[0]
    nsa = [p for p in parsed if not p["is_standard"]]
    return nsa[0] if nsa else parsed[0]
```

---

## Rate Limiting

1. `DEMO_KEY`: ~10 req/hr (shared). Personal key: 1,000 req/hr
2. Add 0.5s delays in batch operations
3. Bulk endpoint (4) is one call for all CONUS rates

---

## Disclaimers (Include in Output)

1. **Maximum reimbursement, not actual cost.**
2. **CONUS only.** OCONUS at https://aoprals.state.gov/
3. **Fiscal year rates.** Verify FY and confirm current.
4. **Lodging taxes not included.** Federal travelers generally exempt (varies by state).
5. **M&IE deductions** when meals provided per 41 CFR 301-11.18.
6. **Per diem is one component.** Also need airfare, ground transport, other expenses.

---

## Additional Resources

For recipes (single lookup with M&IE breakdown, travel cost estimation, multi-location comparison, year-over-year trends, travel IGCE builder, ZIP lookup), common FY2026 rates table, IGCE travel formula, response schemas, and error handling: `view` the **REFERENCE.md** file in this skill directory.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*