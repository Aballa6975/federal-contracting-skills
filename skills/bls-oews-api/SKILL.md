---
name: bls-oews-api
description: >
  Query the BLS Occupational Employment and Wage Statistics (OEWS) API for market wage data by occupation, geography, and industry. Trigger for any mention of BLS, Bureau of Labor Statistics, OEWS, OES, occupational wages, market wages, salary data, wage percentiles, median wage, mean wage, labor market rates, SOC codes, or geographic wage differentials. Also trigger when the user needs to compare wages across metro areas, benchmark contractor labor rates against market data, support IGCE development with market wage research, or validate price proposals against BLS data. Complements the GSA CALC+ skill (ceiling rates from awarded contracts) by providing independent market wage data from employer surveys. Together they form a complete pricing toolkit - BLS OEWS for what the market pays, CALC+ for what GSA contractors charge.
---

# BLS OEWS API Skill v1.3

## Changelog
- v1.3: Refactored for efficiency; moved query recipes, SOC table, IGCE workflow, BLS vs CALC+ comparison, error handling to REFERENCE.md
- v1.2: Added detect_oews_year() auto-detect helper
- v1.1: Major bugfix: area code builder, special value handling, year default, wage cap docs
- v1.0: Initial release

## Quick Start: One Occupation, One Location

```python
import urllib.request, json

OEWS_CURRENT_YEAR = "2024"  # May 2024 estimates, released April 2025
BLS_API_KEY = None  # Set to v2 key for 500 queries/day, or None for v1 (25/day)

def quick_wage_lookup(occ_code, prefix="OEUN", area="0000000"):
    """Get annual mean, median, 10th, and 90th percentile."""
    datatypes = {"04": "Annual Mean", "13": "Annual Median", "11": "Annual 10th%", "15": "Annual 90th%"}
    series_ids = [f"{prefix}{area}000000{occ_code}{dt}" for dt in datatypes]
    for sid in series_ids:
        assert len(sid) == 25, f"Bad series ID length {len(sid)}: {sid}"
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/" if BLS_API_KEY else "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    payload = {"seriesid": series_ids, "startyear": OEWS_CURRENT_YEAR, "endyear": OEWS_CURRENT_YEAR}
    if BLS_API_KEY:
        payload["registrationkey"] = BLS_API_KEY
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    results = {}
    for s in data["Results"]["series"]:
        dt = s["seriesID"][-2:]
        if s["data"]:
            entry = s["data"][0]
            val = entry["value"]
            footnotes = [f.get("text", "") for f in entry.get("footnotes", []) if f.get("text")]
            if val in ("-", "#", "*"):
                results[datatypes[dt]] = f">{footnotes[0]}" if footnotes else f"Suppressed ({val})"
            else:
                results[datatypes[dt]] = f"${int(float(val)):,}"
    return results

# Example: Software Developers in Seattle
# print(quick_wage_lookup("151252", prefix="OEUM", area="0042660"))
```

---

## Overview

BLS Public Data API provides occupational wage data from the OEWS program (~1.1M establishments, ~830 occupations). National, state, and metro area levels with optional industry breakdowns.

Base URL (v2): `https://api.bls.gov/publicAPI/v2/timeseries/data/`
Base URL (v1): `https://api.bls.gov/publicAPI/v1/timeseries/data/`

| Feature | v1 (No Key) | v2 (Registered) |
|---------|-------------|-----------------|
| Daily queries | 25 | 500 |
| Series/query | 25 | 50 |
| Years/query | 10 | 20 |

**What this data is:** Employer-reported base wages. Does NOT include fringe, overhead, G&A, or profit. To build an IGCE, apply a burden/wrap rate (typically 1.5x-2.5x).

**CRITICAL:** Always use `OEWS_CURRENT_YEAR = "2024"`. Do NOT use `datetime.date.today().year`. OEWS data lags ~2 years. Querying 2025 or 2026 returns nothing. Next release: May 15, 2026 (May 2025 estimates).

**For query recipes, SOC lookup table, BLS vs CALC+ comparison, IGCE workflow, and error handling:** `view` the REFERENCE.md file in this skill directory.

---

## Series ID Format (CRITICAL)

Every query requires a **25-character** series ID:

```
Position:  [1-4]   [5-11]    [12-17]    [18-23]    [24-25]
Field:     PREFIX  AREA_CODE INDUSTRY   OCC_CODE   DATATYPE
Length:    4       7         6          6          2
Example:   OEUN    0000000   000000     151252     13
```

### PREFIX (4 chars)
| Prefix | Scope | Area Code |
|--------|-------|-----------|
| `OEUN` | National | `0000000` |
| `OEUS` | State | FIPS + `00000` (e.g., `5100000` = VA) |
| `OEUM` | Metro | `00` + MSA (e.g., `0042660` = Seattle) |

### Common Area Codes
**States:** `0600000`=CA, `1100000`=DC, `2400000`=MD, `4800000`=TX, `5100000`=VA
**Metros:** `0047900`=DC, `0042660`=Seattle, `0012580`=Baltimore, `0037980`=Philadelphia, `0035620`=NYC, `0031080`=LA, `0041860`=SF, `0038060`=Phoenix

### INDUSTRY (6 chars)
`000000` = all industries (default). Industry-specific estimates are **national only** (`OEUN`). Common: `541000`=Prof services, `541500`=Computer systems, `999100`=Federal govt. 2-digit NAICS codes do NOT work.

### OCCUPATION (6 chars): SOC without dash
Common IT/professional: `151252`=Software Dev, `151211`=Systems Analyst, `151212`=InfoSec, `151244`=Net Admin, `151232`=Help Desk, `131111`=Mgmt Analyst, `131082`=Project Mgmt, `113021`=IT Manager. Full table in REFERENCE.md.

### DATATYPE (2 chars)
| Code | Measure | Format |
|------|---------|--------|
| `01` | Employment | Integer |
| `03` | Hourly mean | Float |
| `04` | Annual mean | Integer |
| `08` | Hourly median | Float |
| `11`-`15` | Annual 10th/25th/50th/75th/90th | Integer |

For IGCE: use `04` (mean), `13` (median), `11` (10th floor), `15` (90th ceiling).

---

## Core Functions

### Build Series ID

```python
def build_oes_series_id(prefix="OEUN", area="0000000", industry="000000", occ="000000", datatype="04"):
    sid = f"{prefix}{area}{industry}{occ}{datatype}"
    assert len(sid) == 25, f"Series ID must be 25 chars, got {len(sid)}: {sid}"
    return sid
```

### Normalize Area Code

```python
def normalize_area_code(area_input):
    """Convert 2-digit FIPS, 5-digit MSA, or 7-char full code to 7-char format."""
    area = str(area_input).strip()
    if len(area) == 7: return area
    elif len(area) == 5: return f"00{area}"
    elif len(area) == 2: return f"{area}00000"
    else: raise ValueError(f"Unrecognized area code: '{area}' (len={len(area)})")
```

### Query BLS API

```python
OEWS_CURRENT_YEAR = "2024"

def query_bls(series_ids, start_year=None, end_year=None, registration_key=None):
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/" if registration_key else "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    year = start_year or OEWS_CURRENT_YEAR
    payload = {"seriesid": series_ids, "startyear": year, "endyear": end_year or year}
    if registration_key:
        payload["registrationkey"] = registration_key
    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                 headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())
```

### Parse Results

```python
BLS_SPECIAL_VALUES = {"-", "#", "*", "N/A"}

def parse_oes_results(api_response):
    """Parse response into {series_id: {year, value, is_numeric, footnotes}}."""
    results = {}
    for series in api_response.get("Results", {}).get("series", []):
        sid = series["seriesID"]
        if series["data"]:
            latest = series["data"][0]
            footnote_texts = [f.get("text", "") for f in latest.get("footnotes", []) if f.get("text")]
            val = latest["value"]
            results[sid] = {"year": latest["year"], "period": latest["periodName"],
                "value": val, "is_numeric": val not in BLS_SPECIAL_VALUES, "footnotes": footnote_texts}
    return results
```

### Format Values

```python
DATATYPE_LABELS = {"01": "Employment", "03": "Hourly Mean Wage", "04": "Annual Mean Wage",
    "08": "Hourly Median", "11": "Annual 10th Percentile", "12": "Annual 25th Percentile",
    "13": "Annual Median", "14": "Annual 75th Percentile", "15": "Annual 90th Percentile"}

def format_oes_value(value_str, datatype_code, footnotes=None):
    if value_str in BLS_SPECIAL_VALUES:
        return f"[Capped] {footnotes[0]}" if footnotes else f"[Suppressed: {value_str}]"
    try:
        if datatype_code == "01": return f"{int(float(value_str)):,}"
        elif datatype_code in ("03", "06", "07", "08", "09", "10"): return f"${float(value_str):,.2f}/hr"
        else: return f"${int(float(value_str)):,}"
    except (ValueError, TypeError):
        return f"[Unparseable: {value_str}]"
```

### Detect Latest OEWS Year

```python
def detect_oews_year(api_key=None):
    """Probe API for newer data year. Call once at start of IGCE build."""
    probe_series = "OEUN000000000000000000004"
    candidate = str(int(OEWS_CURRENT_YEAR) + 1)
    url = "https://api.bls.gov/publicAPI/v2/timeseries/data/" if api_key else "https://api.bls.gov/publicAPI/v1/timeseries/data/"
    payload = {"seriesid": [probe_series], "startyear": candidate, "endyear": candidate}
    if api_key: payload["registrationkey"] = api_key
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'),
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
        for s in data.get("Results", {}).get("series", []):
            if s.get("data") and s["data"][0].get("value") not in ("-", "#", "*", ""):
                return candidate
    except Exception: pass
    return OEWS_CURRENT_YEAR
```

---

## Critical Rules

1. **Series ID must be exactly 25 characters.** Print component lengths to debug.
2. **Always query OEWS_CURRENT_YEAR ("2024"), not calendar year.** Most common failure.
3. **Industry estimates are national only.** Cannot combine OEUM/OEUS with non-zero industry codes.
4. **Not all occupation x area combos exist.** Handle empty data and "Series does not exist" gracefully.
5. **Special values ("-", "*", "#") must be checked before float().** `float("-")` throws ValueError.
6. **Wage cap:** "-" with footnote code 5 means wage >= $239,200/yr or $115/hr. Use as lower bound.
7. **Batch series into one call** (up to 50 for v2, 25 for v1) to conserve daily quota.
8. **2-digit NAICS codes don't work.** Use 3-digit (e.g., `541000` not `540000`).
9. **MSA definitions changed in May 2024 data** (2020 census, OMB Bulletin 23-01). NECTAs discontinued.

---

## Additional Resources

For query recipes (wage profile, metro comparison, multi-occupation, industry-specific, IGCE rate derivation), BLS vs CALC+ comparison table, full SOC code lookup table, complete IGCE workflow example, and error handling: `view` the **REFERENCE.md** file in this skill directory.
