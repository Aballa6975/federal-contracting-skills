---
name: gsa-calc-ceilingrates
description: >
  Query the GSA CALC+ Labor Ceiling Rates API for awarded GSA MAS schedule hourly rates. Use this skill whenever the user asks about GSA labor rates, MAS ceiling prices, IGCE development, price reasonableness analysis, labor category comparisons, GSA schedule pricing, or market research for professional services acquisitions. Trigger for any mention of CALC, CALC+, ceiling rates, GSA rates, MAS rates, labor categories, GSA pricing, schedule pricing, IGCE support, price analysis, or rate benchmarking. Also trigger when the user needs to compare vendor pricing, look up rates by education/experience level, find rates for a specific SIN, or support price negotiations for task orders under GSA MAS contracts. This skill is essential for IGCEs, price reasonableness determinations, market research memos, and competitive range analysis.
---

# GSA CALC+ Labor Ceiling Rates API Skill

## Overview

The GSA CALC+ API (https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/) provides free, no-auth access to awarded NTE hourly ceiling rates from GSA MAS contracts. Data refreshes nightly.

Base URL: `https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/`
Web UI: https://buy.gsa.gov/pricing/qr/mas

**What this data is:** Fully burdened hourly ceiling rates (the max a contractor can charge). Worldwide, master contract-level pricing.

**What this data is NOT:** Order-level actuals, BLS wages, or prices-paid data.

**For composite workflows (IGCE benchmarking, price reasonableness, vendor rate cards, SIN analysis), aggregation schemas, SIN table, pagination, and troubleshooting:** `view` the REFERENCE.md file in this skill directory.

## Critical Rules

### 1. Messy Field Values (MOST COMMON PROBLEM)

Data comes from vendor PPTs. Values are NOT standardized.

**education_level:** ~15 distinct values. Filter with abbreviated form (BA, MA, HS, AA, PHD); API normalizes (BA captures "Bachelors" too). For clean analysis, use `education_level_counts` aggregation (6 buckets: AA, BA, HS, MA, PHD, TEC).

**security_clearance:** Mix of booleans and strings. Filter with `yes` or `no`; API normalizes.

**worksite:** ~20 values. Filter with `Customer`, `Contractor`, or `Both`; API does partial matching.

**business_size:** Clean. `S` = Small, `O` = Other.

### 2. Always Discover Before Exact Searching

Vendor names are inconsistent. **Use `suggest-contains` first** to find the exact value, then `search=` with that exact value.

### 3. Three Search Modes

| Mode | Parameter | Behavior |
|------|-----------|----------|
| Keyword | `keyword=term` | Wildcard across labor_category, vendor_name, idv_piid |
| Exact Match | `search=field:value` | Complete field match (must be exact) |
| Suggest-Contains | `suggest-contains=field:term` | Returns aggregation buckets only (2-char min) |

### 4. Aggregations Are Always Present

Every response includes `wage_stats` (count/min/max/avg/stddev), `histogram_percentiles` (P10-P90), `median_price`, `education_level_counts`, `business_size`, etc. Stats cover the FULL result set even when hits.total caps at 10,000. Use `wage_stats.count` for true record count.

**Use `histogram_percentiles.values.50.0` for median** (not `median_price`; different interpolation). Full schema in REFERENCE.md.

### 5. Record Fields

| Field | Type | Description |
|-------|------|-------------|
| `labor_category` | string | Awarded labor category title |
| `current_price` | float | Current NTE ceiling rate ($/hr) |
| `next_year_price` | float | Next option year rate |
| `vendor_name` | string | Contractor name |
| `idv_piid` | string | GSA MAS contract number |
| `education_level` | string | Min education requirement |
| `min_years_experience` | int | Min years experience |
| `business_size` | string | "S" or "O" |
| `security_clearance` | mixed | Boolean or string |
| `worksite` | string | Where work is performed |
| `sin` | string | Special Item Number |
| `contract_start` / `contract_end` | string | YYYY-MM-DD |

Hit-level `_id` (string) is used for the `exclude` parameter. Source-level `id` (int) is the record ID.

---

## Core Endpoints

All queries are GET requests against the base URL with query parameters.

### 1. Keyword Search (PRIMARY WORKHORSE)

```python
import urllib.request, urllib.parse, json

def keyword_search(keyword, page=1, page_size=100, filters=None, ordering="current_price", sort="asc"):
    """Wildcard search across labor_category, vendor_name, idv_piid."""
    params = f"keyword={urllib.parse.quote_plus(keyword)}&page={page}&page_size={page_size}&ordering={ordering}&sort={sort}"
    if filters:
        for f in filters:
            params += f"&filter={f}"
    url = f"https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 2. Exact Match Search

```python
def exact_search(field, value, page=1, page_size=100, filters=None, ordering="current_price", sort="asc"):
    """Exact match on labor_category, vendor_name, or idv_piid. Discover value with suggest-contains first."""
    encoded_value = urllib.parse.quote_plus(value)
    params = f"search={field}:{encoded_value}&page={page}&page_size={page_size}&ordering={ordering}&sort={sort}"
    if filters:
        for f in filters:
            params += f"&filter={f}"
    url = f"https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 3. Suggest-Contains (Autocomplete/Discovery)

```python
def suggest_contains(field, term):
    """Discover exact field values. Returns aggregation buckets only. 2-char minimum."""
    encoded_term = urllib.parse.quote_plus(term)
    url = f"https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/?suggest-contains={field}:{encoded_term}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    buckets = data.get('aggregations', {}).get(field, {}).get('buckets', [])
    return {'suggestions': [{"value": b["key"], "count": b["doc_count"]} for b in buckets],
            'total_matching_records': data.get('hits', {}).get('total', {}).get('value', 0)}
```

### 4. Filtered Browse (No Search Term)

```python
def filtered_browse(filters, page=1, page_size=100, ordering="current_price", sort="asc"):
    """Browse with filters only. Good for market segment statistics."""
    params = f"page={page}&page_size={page_size}&ordering={ordering}&sort={sort}"
    for f in filters:
        params += f"&filter={f}"
    url = f"https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/?{params}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

---

## Filter Reference

Format: `filter=field:value`. Multiple filters = AND. Pipe within field = OR.

| Filter | Format | Example |
|--------|--------|---------|
| `education_level` | Code or pipe-delimited | `education_level:BA` or `education_level:BA\|MA` |
| `experience_range` | min,max | `experience_range:5,15` |
| `min_years_experience` | exact | `min_years_experience:10` |
| `price_range` | min,max | `price_range:50,200` |
| `business_size` | S or O | `business_size:S` |
| `security_clearance` | yes or no | `security_clearance:yes` |
| `sin` | SIN code | `sin:54151S` |
| `worksite` | value | `worksite:Customer` |

Combining: `filter=education_level:BA|MA&filter=experience_range:5,15&filter=business_size:S`

---

## Ordering Reference

| Field | Description |
|-------|-------------|
| `current_price` | Hourly ceiling rate (default) |
| `labor_category` | Alphabetical |
| `vendor_name` | Alphabetical |
| `education_level` | By education |
| `min_years_experience` | By experience |

Sort: `sort=asc` or `sort=desc`.

---

## Excluding Outliers

Use `exclude` with hit-level `_id` values (pipe-delimited): `&exclude=6275099|6275111`

Excluded records are removed from both hits and aggregation stats.

---

## CSV Export

Append `&export=y` to any query URL. CSV includes metadata header rows before actual data; skip to the line starting with "Contract #,".

---

## Rate Limiting

1. No auth required; 1,000 requests/hour
2. Add 0.3s delays in batch operations
3. Use aggregations for IGCE stats instead of computing client-side
4. Use `suggest-contains` before exact match searches
5. If `hits.total.relation` = "gte", use `wage_stats.count` for true count
6. Check `timed_out`; if true, results may be incomplete

---

## Disclaimers (Include in Output)

1. **Ceiling rates, not actuals.** Order-level prices should be lower per FAR 8.405-2(d).
2. **Worldwide rates.** No geographic cost adjustment.
3. **Master contract-level.** Not task order rates.
4. **Fair and reasonable determination still required** per FAR 15.4.
5. **Sample size matters.** Note the count in any analysis.

---

## Additional Resources

For complete aggregation schemas, composite workflows (IGCE benchmarking, price reasonableness check, vendor rate card extraction, multi-category IGCE builder, SIN analysis), common SINs table, pagination helper, and troubleshooting: `view` the **REFERENCE.md** file in this skill directory.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*