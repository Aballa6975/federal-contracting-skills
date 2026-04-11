---
name: gsa-perdiem-rates-reference
description: >
  Reference file for the GSA Per Diem Rates API skill. Do not trigger
  directly. Contains query recipes, common FY2026 rates table, travel
  IGCE formula, response schemas, and error handling. Loaded on demand
  by the main gsa-perdiem-rates skill.
---

# GSA Per Diem API Reference

## Table of Contents
1. Response Schemas
2. Query Recipes
3. Common Rates Table (FY2026)
4. IGCE Travel Formula
5. Error Handling
6. API vs Website Comparison

---

## 1. Response Schemas

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

## 2. Query Recipes

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

## 3. Common Per Diem Rates (reference snapshot)

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

## 4. IGCE Travel Formula

```
Trip Cost = Airfare + Ground Transport + (Nightly Lodging x Nights) + M&IE Full Days + (M&IE x 0.75 x 2 partial days)
Annual Travel = Trip Cost x Trips/Year
Total Travel = Annual Travel x Years in PoP
```

Per diem covers lodging + M&IE only. Also estimate: airfare (GSA City Pairs at cpsearch.fas.gsa.gov), ground transport (GSA mileage $0.70/mile CY2025), conference fees. Document source (GSA Per Diem API, FY, location) in IGCE narrative.

---

## 5. Error Handling

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

## 6. API vs Website Comparison

| Dimension | API | Website (gsa.gov/travel) |
|-----------|-----|------------------------|
| Format | JSON | HTML |
| Auth | API key | None |
| Batch queries | Yes | No |
| Best for | IGCE automation, Claude skills | One-off lookups |

Cross-validate at https://www.gsa.gov/travel/plan-book/per-diem-rates.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*