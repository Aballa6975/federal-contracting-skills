---
name: bls-oews-api-reference
description: Reference file for the BLS OEWS API skill. Do not trigger directly. Contains query recipes, SOC code lookup table, BLS vs CALC+ comparison, IGCE workflow example, and error handling. Loaded on demand by the main bls-oews-api skill.
---

# BLS OEWS API Reference

Supplemental reference for the BLS OEWS skill. Load on demand for recipes, SOC codes, and troubleshooting.

## Table of Contents
1. Query Recipes
2. BLS vs CALC+ Comparison
3. SOC Code Lookup Table
4. IGCE Rate Derivation
5. Complete IGCE Workflow Example
6. Error Handling

---

## 1. Query Recipes

### Full Wage Profile for One Occupation

```python
def get_wage_profile(occ_code, prefix="OEUN", area="0000000", industry="000000"):
    """Get employment + all wage percentiles for an occupation."""
    datatypes = ["01", "03", "04", "08", "11", "12", "13", "14", "15"]
    series_ids = [build_oes_series_id(prefix, area, industry, occ_code, dt) for dt in datatypes]
    response = query_bls(series_ids)
    results = parse_oes_results(response)
    profile = {}
    all_footnotes = []
    for sid, data in results.items():
        dt = sid[-2:]
        profile[DATATYPE_LABELS.get(dt, dt)] = format_oes_value(data["value"], dt, data.get("footnotes"))
        profile["_year"] = data["year"]
        if data.get("footnotes"): all_footnotes.extend(data["footnotes"])
    if all_footnotes: profile["_footnotes"] = list(set(all_footnotes))
    return profile

# National: get_wage_profile("151252")
# Seattle: get_wage_profile("151252", prefix="OEUM", area="0042660")
# Virginia: get_wage_profile("151252", prefix="OEUS", area="5100000")
# Federal govt national: get_wage_profile("151252", industry="999100")
```

### Compare Wages Across Metros

```python
def compare_metros(occ_code, metro_codes, datatype="04"):
    """Compare a wage measure across multiple metro areas."""
    series_ids = [build_oes_series_id("OEUM", normalize_area_code(area), "000000", occ_code, datatype)
                  for area in metro_codes]
    return parse_oes_results(query_bls(series_ids))

# metros = {"0047900": "DC", "0042660": "Seattle", "0012580": "Baltimore"}
```

### Compare Multiple Occupations in One Location

```python
def compare_occupations(occ_codes, prefix="OEUN", area="0000000", datatype="04"):
    """Compare annual mean wage across occupations in one location."""
    series_ids = [build_oes_series_id(prefix, area, "000000", occ, datatype) for occ in occ_codes]
    return parse_oes_results(query_bls(series_ids))
```

### Industry-Specific Wages (National Only)

```python
# Federal govt vs all-industry vs computer systems design for Systems Analysts
series_ids = [
    build_oes_series_id("OEUN", "0000000", "000000", "151211", "04"),  # All industries
    build_oes_series_id("OEUN", "0000000", "999100", "151211", "04"),  # Federal govt
    build_oes_series_id("OEUN", "0000000", "541500", "151211", "04"),  # Computer systems
]
```

---

## 2. BLS vs CALC+ Comparison

| Dimension | BLS OEWS | GSA CALC+ Ceiling Rates |
|-----------|----------|------------------------|
| Data source | Employer wage surveys (~1.1M establishments) | Awarded GSA MAS contract rates |
| What it measures | Base wages paid to employees | Fully burdened ceiling hourly rates |
| Includes overhead/profit | No (base wage only) | Yes (fully loaded) |
| Geographic detail | National, state, 530+ metros | Worldwide (no geo breakdown) |
| Industry detail | National industry breakdowns | By SIN/category |
| Occupation taxonomy | SOC codes (~830 occupations) | Vendor-defined labor categories |
| Percentile data | Yes (10/25/50/75/90) | Yes (via aggregation) |
| Update frequency | Annual (~April) | Nightly |
| Best for | Market wage benchmarking, IGCE base rates | Price reasonableness for GSA orders |
| IGCE role | Base wage x burden factor | Validate proposed rates |

### Using Both Together
1. Start with BLS OEWS: look up occupation at performance location (median + range)
2. Calculate burdened range: apply 1.5x-2.5x multiplier
3. Cross-reference CALC+: GSA ceiling rates should fall within/near burdened BLS range
4. If CALC+ >> burdened BLS: specialized role, clearance, or high overhead. Document the gap.
5. If CALC+ << burdened BLS: aggressive pricing or BLS category is broader than the labor cat.

---

## 3. SOC Code Lookup Table

Common mappings for federal IT/professional services:

| Contract Title | SOC Match | Code | Notes |
|---------------|-----------|------|-------|
| Program Manager | General and Operations Managers | 111021 | |
| Project Manager | Project Management Specialists | 131082 | New in 2018 SOC |
| Management Analyst | Management Analysts | 131111 | |
| Systems Engineer | Computer Systems Analysts | 151211 | |
| Software Developer | Software Developers | 151252 | |
| Cybersecurity Analyst | Information Security Analysts | 151212 | |
| Network Engineer | Computer Network Architects | 151241 | |
| Database Administrator | Database Administrators | 151242 | |
| Systems Administrator | Network/Computer Systems Admins | 151244 | |
| QA Tester | Software QA Analysts and Testers | 151253 | |
| Help Desk / Tier 1 | Computer User Support Specialists | 151232 | |
| Data Scientist | Data Scientists | 152051 | Under Math, not IT |
| Technical Writer | Technical Writers | 273042 | |
| Accountant | Accountants and Auditors | 132011 | |
| Admin Assistant | Secretaries and Admin Assistants | 436014 | |
| Contracting Specialist (1102) | Buyers and Purchasing Agents | 131020 | Minor group; for senior 1102s also consider 131082 |
| IT Manager | Computer and Info Systems Managers | 113021 | |
| Computer Programmer | Computer Programmers | 151251 | |
| Web Developer | Web Developers | 151254 | |

Common administrative/support:
- 431011 = First-Line Supervisors of Office Workers
- 436011 = Executive Secretaries
- 439061 = Office Clerks, General

Full SOC list: https://www.bls.gov/oes/current/oes_stru.htm

When mapping is ambiguous, query multiple SOC codes and present the range.

---

## 4. IGCE Rate Derivation

BLS annual wages assume 2,080 hours/year. To convert to burdened hourly rate:

```python
def bls_to_igce_rate(annual_wage, burden_multiplier=2.0):
    """Convert BLS annual wage to estimated fully burdened hourly rate.
    Typical multipliers:
      1.5x-1.7x = Lean contractor
      1.8x-2.2x = Mid-range professional services
      2.0x-2.5x = Large contractor with clearance overhead
      2.5x-3.0x = High-overhead (SCIF, deployed)
    """
    return round((annual_wage / 2080) * burden_multiplier, 2)

# Software Developer DC median $150,880 at 2.0x = $145.08/hr burdened
```

---

## 5. Complete IGCE Workflow Example

```python
OEWS_CURRENT_YEAR = "2024"
BLS_API_KEY = None

occupations = {
    "151211": "Systems Analyst", "151252": "Software Developer",
    "151232": "Help Desk Specialist", "151244": "Network Administrator",
}
datatypes = ["04", "11", "13", "15"]
target_metro = "0042660"

all_series = []
for occ in occupations:
    for dt in datatypes:
        all_series.append(build_oes_series_id("OEUM", target_metro, "000000", occ, dt))

response = query_bls(all_series, key=BLS_API_KEY)

data_year = "N/A"
for s in response['Results']['series']:
    if s['data']:
        data_year = s['data'][0]['year']
        break

print(f"=== IGCE Market Wage Research: Seattle Metro ===")
print(f"    Source: BLS OEWS, May {data_year}\n")

for occ_code, title in occupations.items():
    print(f"  {title} (SOC {occ_code[:2]}-{occ_code[2:]}):")
    for dt in datatypes:
        sid = build_oes_series_id("OEUM", target_metro, "000000", occ_code, dt)
        for s in response['Results']['series']:
            if s['seriesID'] == sid and s['data']:
                entry = s['data'][0]
                val = entry['value']
                labels = {"04": "Mean", "11": "10th%", "13": "Median", "15": "90th%"}
                if val in BLS_SPECIAL_VALUES:
                    footnotes = [f.get("text", "") for f in entry.get("footnotes", []) if f.get("text")]
                    print(f"    {labels[dt]:>8}: {footnotes[0] if footnotes else f'Suppressed ({val})'}")
                else:
                    wage = int(float(val))
                    hourly = wage / 2080
                    burdened_low, burdened_high = hourly * 1.8, hourly * 2.2
                    print(f"    {labels[dt]:>8}: ${wage:>9,}/yr | ${hourly:>6.2f}/hr | ${burdened_low:>6.2f}-${burdened_high:>6.2f}/hr burdened")
    print()
```

---

## 6. Error Handling

| Response | Meaning | Action |
|----------|---------|--------|
| `"Series does not exist"` | Invalid series ID | Verify 25-char format, check area/industry/occ codes |
| `"No Data Available for Series X Year: Y"` | Valid series, wrong year | Use OEWS_CURRENT_YEAR ("2024"), not calendar year |
| Empty `data` array | Data suppressed (small sample) | Try broader geography |
| Value `"-"` (footnote 5) | Wage >= $239,200/yr or $115/hr | Use cap as lower bound |
| Value `"*"` (footnote 8) | RSE > 50% or <50 observations | Try broader geography or parent SOC |
| `"REQUEST_NOT_PROCESSED"` | Rate limit or malformed request | Wait and retry |
| `"REQUEST_SUCCEEDED"` with messages | Partial success | Check individual series |

### Additional Area Code Tables

**Full state FIPS codes:**
```
0600000=CA  1100000=DC  1200000=FL  1300000=GA  2400000=MD
3400000=NJ  3600000=NY  4200000=PA  4800000=TX  5100000=VA  5300000=WA
```

**Full metro MSA codes (verified May 2024):**
```
0012420=Austin   0012580=Baltimore  0014460=Boston   0016980=Chicago
0017140=Cincinnati  0019100=Dallas  0026420=Houston  0031080=LA
0033100=Miami  0033460=Minneapolis  0035380=New Orleans  0035620=NYC
0037980=Philadelphia  0038060=Phoenix  0040140=Riverside  0019820=Detroit
0041740=San Diego  0041860=San Francisco  0042660=Seattle  0047900=DC
0045300=Tampa
```

Full MSA list: https://www.bls.gov/oes/current/msa_def.htm
