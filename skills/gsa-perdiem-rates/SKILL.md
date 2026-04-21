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

This skill is self-contained. Recipes, response schemas, common rates table, travel IGCE formula, and error handling are all below.

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
Common rates table below goes stale each August. Query the API directly after August for exact figures.

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

## Response Schemas

### City/State/ZIP Endpoints (1-3)
```json
{"rates": [{"rate": [{"months": {"month": [
    {"value": 137, "number": 1, "short": "Jan", "long": "January"}]},
  "meals": 74, "county": "Baltimore city", "city": "Baltimore", "standardRate": "false"}],
  "state": "MD", "year": 2026}]}
```

### Bulk Lodging (Endpoint 4)
Values are **strings**: `{"Jan": "137", "Meals": "74", "City": "Baltimore", "State": "MD", "County": "Baltimore city", "DID": "356"}`

### M&IE Breakdown (Endpoint 5)
`[{"total": 68, "breakfast": 16, "lunch": 19, "dinner": 28, "incidental": 5, "FirstLastDay": 51}]`

### ZIP Mapping (Endpoint 6)
`[{"Zip": "21201", "DID": "0", "ST": "MD"}]` (DID "0" = standard rate)

---

## Query Recipes

### Recipe 1: Full Per Diem Lookup

```python
def lookup_perdiem(city, state, year=2026, api_key="DEMO_KEY"):
    """Full lookup with M&IE breakdown."""
    response = get_perdiem_city(city, state, year, api_key)
    rate = get_best_rate(response, query_city=city)
    if not rate:
        return {"error": f"No rates found for {city}, {state} in FY{year}"}
    mie_tiers = get_mie_breakdown(year, api_key)
    mie_detail = next((t for t in mie_tiers if t["total"] == rate["meals"]), None)
    return {
        "city": rate["city"], "county": rate["county"], "state": state.upper(),
        "fiscal_year": year, "is_standard_rate": rate["is_standard"],
        "lodging": rate["lodging_by_month"],
        "lodging_range": f"${rate['lodging_min']}-${rate['lodging_max']}/night"
            if rate["has_seasonal_variation"] else f"${rate['lodging_min']}/night",
        "mie_total": rate["meals"], "mie_breakdown": mie_detail,
    }
```

### Recipe 2: Estimate Travel Costs

```python
def estimate_travel_cost(city, state, year, num_nights, travel_month=None, api_key="DEMO_KEY"):
    """Total per diem for a trip. Uses max monthly rate if month unknown."""
    response = get_perdiem_city(city, state, year, api_key)
    rate = get_best_rate(response, query_city=city)
    if not rate:
        return {"error": f"No rates found for {city}, {state}"}
    nightly_rate = rate["lodging_by_month"].get(travel_month, rate["lodging_max"]) if travel_month else rate["lodging_max"]
    lodging_total = nightly_rate * num_nights
    travel_days = num_nights + 1
    if travel_days <= 1:
        mie_total = rate["meals"] * 0.75
    elif travel_days == 2:
        mie_total = rate["meals"] * 0.75 * 2
    else:
        mie_total = (rate["meals"] * (travel_days - 2)) + (rate["meals"] * 0.75 * 2)
    return {
        "city": rate["city"], "state": state.upper(),
        "nightly_lodging": nightly_rate, "num_nights": num_nights,
        "lodging_total": lodging_total, "daily_mie": rate["meals"],
        "travel_days": travel_days, "mie_total": round(mie_total, 2),
        "grand_total": round(lodging_total + mie_total, 2),
        "rate_month": travel_month or "MAX",
    }
```

### Recipe 3: Compare Multiple Locations

```python
import time

def compare_locations(locations, year=2026, api_key="DEMO_KEY"):
    """Compare per diem across locations. Input: list of (city, state) tuples."""
    results = []
    for city, state in locations:
        try:
            response = get_perdiem_city(city, state, year, api_key)
            rate = get_best_rate(response, query_city=city)
            if rate:
                results.append({
                    "location": f"{rate['city']}, {state.upper()}",
                    "lodging_range": f"${rate['lodging_min']}-${rate['lodging_max']}"
                        if rate["has_seasonal_variation"] else f"${rate['lodging_min']}",
                    "lodging_max": rate["lodging_max"],
                    "mie": rate["meals"],
                    "max_daily_total": rate["lodging_max"] + rate["meals"],
                })
        except Exception as e:
            results.append({"location": f"{city}, {state}", "error": str(e)})
        time.sleep(0.5)
    results.sort(key=lambda x: x.get("max_daily_total", 0), reverse=True)
    return results
```

### Recipe 4: Year-Over-Year Comparison

```python
def rate_trend(city, state, api_key="DEMO_KEY"):
    """Compare rates across available FYs (typically 3 years)."""
    results = []
    for year in [2024, 2025, 2026]:
        try:
            response = get_perdiem_city(city, state, year, api_key)
            rate = get_best_rate(response, query_city=city)
            if rate:
                results.append({"fiscal_year": year, "lodging_min": rate["lodging_min"],
                    "lodging_max": rate["lodging_max"], "mie": rate["meals"]})
        except Exception: pass
        time.sleep(0.5)
    return results
```

### Recipe 5: Multi-Trip Travel IGCE

```python
def build_travel_igce(trips, year=2026, api_key="DEMO_KEY"):
    """Build travel estimate for multiple trips.
    trips: list of dicts with city, state, nights, num_trips, month (optional)."""
    igce_lines, grand_total = [], 0
    for trip in trips:
        cost = estimate_travel_cost(trip["city"], trip["state"], year,
            trip["nights"], trip.get("month"), api_key)
        if "error" in cost:
            igce_lines.append({"trip": trip, "error": cost["error"]}); continue
        trip_total = cost["grand_total"] * trip["num_trips"]
        grand_total += trip_total
        igce_lines.append({
            "destination": cost["city"], "state": cost["state"],
            "nights_per_trip": trip["nights"], "num_trips": trip["num_trips"],
            "lodging_per_trip": cost["lodging_total"], "mie_per_trip": cost["mie_total"],
            "per_trip_total": cost["grand_total"], "line_total": trip_total,
        })
        time.sleep(0.5)
    return {"fiscal_year": year, "line_items": igce_lines, "grand_total": round(grand_total, 2),
        "data_source": "GSA Per Diem Rates API",
        "disclaimer": "Per diem rates are maximum reimbursement per 41 CFR 301-11. Airfare and ground transport not included."}
```

### Recipe 6: ZIP Code Lookup

```python
def lookup_by_zip(zip_code, year=2026, api_key="DEMO_KEY"):
    """Per diem by ZIP. Prefers NSA rate over standard."""
    response = get_perdiem_zip(zip_code, year, api_key)
    rate = get_best_rate(response)
    if not rate:
        return {"error": f"No rates for ZIP {zip_code} in FY{year}"}
    return {"zip": zip_code, "city": rate["city"], "county": rate["county"],
        "is_standard": rate["is_standard"],
        "lodging_range": f"${rate['lodging_min']}-${rate['lodging_max']}"
            if rate["has_seasonal_variation"] else f"${rate['lodging_min']}/night",
        "mie": rate["meals"]}
```

---

## Common Per Diem Rates (reference snapshot)

These are reference values for quick comparison. **Rates change each fiscal year** (GSA publishes new rates effective October 1). Query the live API for exact current figures before citing in a contract file or IGCE.

| Location | NSA City Name | Lodging Range | M&IE | Max Daily |
|----------|--------------|--------------|------|-----------|
| Washington, DC | District of Columbia | $183-$276 | $92 | $368 |
| New York City | New York City | $179-$342 | $92 | $434 |
| Boston | Boston / Cambridge | $209-$349 | $92 | $441 |
| San Francisco | San Francisco | $259-$272 | $92 | $364 |
| Seattle | Seattle | $188-$248 | $92 | $340 |
| Chicago | Chicago | $142-$234 | $92 | $326 |
| Denver | Denver / Aurora | $165-$215 | $92 | $307 |
| Los Angeles | Los Angeles | $191 (flat) | $86 | $277 |
| Atlanta | Atlanta | $182-$197 | $86 | $283 |
| Dallas | Dallas | $170-$191 | $80 | $271 |
| Fort Worth | Arlington / Fort Worth / Grapevine | $181 (flat) | $80 | $261 |
| Austin | Austin | $173-$187 | $80 | $267 |
| Baltimore | Baltimore City | $150 (flat) | $86 | $236 |
| Baltimore | Baltimore | $137-$161 | $74 | $235 |
| Houston | Houston | $128 (flat) | $80 | $208 |
| Standard Rate | Standard Rate | $110 (flat) | $68 | $178 |

**DC metro covers:** DC, Alexandria, Falls Church, Fairfax (city + county), Arlington County VA, Montgomery + Prince George's counties MD. **Baltimore is separate** ($150/$86, not DC rates).

---

## IGCE Travel Formula

```
Trip Cost = Airfare + Ground Transport + (Nightly Lodging x Nights) + M&IE Full Days + (M&IE x 0.75 x 2 partial days)
Annual Travel = Trip Cost x Trips/Year
Total Travel = Annual Travel x Years in PoP
```

Per diem covers lodging + M&IE only. Also estimate: airfare (GSA City Pairs at cpsearch.fas.gsa.gov), ground transport (GSA mileage $0.70/mile CY2025), conference fees. Document source (GSA Per Diem API, FY, location) in IGCE narrative.

---

## Error Handling

| Scenario | API Behavior | Action |
|----------|-------------|--------|
| No API key | HTTP 403 | Add `?api_key=DEMO_KEY` or register |
| City partially matches | 200, returns all matching NSAs + standard | Filter for target city |
| City matches nothing | 200, returns ALL state NSAs + standard | Use "Standard Rate" entry |
| Invalid state | 200, empty rates array | Verify 2-letter code |
| Future/old FY | 200, empty rates array | Use current or most recent FY |
| ZIP coverage gap | 200, empty rates array | Fall back to city/state endpoint |
| Rate limit | HTTP 429 | Wait or register for free key |
| Special chars in city | Unexpected results | Replace apostrophes/hyphens with spaces; keep "St." periods |

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

## API vs Website Comparison

| Dimension | API | Website (gsa.gov/travel) |
|-----------|-----|------------------------|
| Format | JSON | HTML |
| Auth | API key | None |
| Batch queries | Yes | No |
| Best for | IGCE automation, Claude skills | One-off lookups |

Cross-validate at https://www.gsa.gov/travel/plan-book/per-diem-rates.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*
