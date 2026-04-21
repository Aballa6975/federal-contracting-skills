---
name: igce-builder-ffp
description: >
  Build IGCEs for Firm-Fixed-Price (FFP) federal contracts using structured
  wrap rate buildup (fringe, overhead, G&A, profit). Orchestrates BLS OEWS,
  GSA CALC+, and GSA Per Diem skills. Supports FFP-by-period and
  FFP-by-deliverable pricing structures, SOW/PWS decomposition into labor
  categories, and rate validation against CALC+ market data. Trigger for:
  FFP IGCE, firm fixed price estimate, firm fixed price cost estimate,
  wrap rate, wrap rate buildup, cost buildup, FFP cost model, build an
  FFP IGCE, price this FFP contract, fixed price estimate, FFP from this
  SOW. Also trigger for wrap rate analysis, implied multiplier, FFP
  scenario analysis, or FFP rate comparison. Do NOT use for Labor Hour,
  T&M, or cost-reimbursement IGCEs (use IGCE Builder LH/T&M or IGCE
  Builder CR). Do NOT use for grant budgets (use Grant Budget Builder).
  Requires BLS OEWS API, GSA CALC+ Ceiling Rates API, and GSA Per Diem
  Rates API skills.
---

# IGCE Builder: Firm-Fixed-Price (FFP)

## Overview

This skill produces Independent Government Cost Estimates for FFP contracts using a layered wrap rate buildup model. Instead of the single burden multiplier used in T&M/LH pricing, FFP separates direct labor, fringe benefits, overhead, G&A, and profit into distinct auditable cost pools. The BLS base wage anchors the estimate; each cost pool adds a layer; the result is a fully burdened FFP rate per labor category.

**Required L1 skills (must be installed):**
1. **BLS OEWS API** -- market wage data by occupation and geography
2. **GSA CALC+ Ceiling Rates API** -- awarded GSA MAS schedule hourly rates
3. **GSA Per Diem Rates API** -- federal travel lodging and M&IE rates

**Required API keys (must be in user memory):**
- BLS API key (v2) for BLS OEWS
- api.data.gov key for GSA Per Diem
- CALC+ requires no key

If a key is missing, prompt the user to register: BLS at https://data.bls.gov/registrationEngine/, api.data.gov at https://api.data.gov/signup/

**Regulatory basis:** FAR 15.402 (cost/pricing data). FAR 15.404-1(a) (cost analysis). FAR 15.404-1(b) (price analysis). FAR 15.404-4 (profit/fee analysis). FAR 16.202 (FFP contracts).

## Workflow Selection

### Workflow A: Full FFP IGCE Build (Default)
User needs a complete FFP cost estimate. Execute Steps 1 through 9 in order.
Triggers: "FFP IGCE," "firm fixed price estimate," "wrap rate buildup," "cost buildup."

### Workflow A+: SOW/PWS-Driven FFP Build
User provides a Statement of Work or requirement description instead of pre-structured labor inputs. Execute Step 0 (Requirements Decomposition) first, validate with user, then Steps 1-9.
Triggers: "build an FFP IGCE from this SOW," "price this PWS as FFP," or when the user provides a block of requirement text rather than a labor category table.

**Skip Step 0 if the user provides explicit staffing** (headcount per labor category) even if they reference an underlying PWS or SOW. Go straight to Workflow A.

### Workflow B: FFP Rate Validation Only
User has proposed rates and wants to check reasonableness. Compare against CALC+ and optionally BLS with wrap rate buildup.
Triggers: "is this FFP rate reasonable," "validate these wrap rates," "check this FFP proposal."

**Workflow B steps:**
1. Collect the vendor's proposed labor categories and fully burdened hourly rates.
2. For each category, query CALC+ per Step 4.
3. Position each rate: below 25th percentile (aggressive), 25th-75th (competitive), above 75th (premium), above 90th (outlier requiring justification).
4. If the user wants BLS context, run Steps 1-3 to show where the vendor rate falls relative to the wrap rate buildup at low/mid/high scenarios.
5. Produce the Rate Validation sheet and narrative. No full workbook unless requested.

## Information to Collect

Batch clarifying questions rather than ask iteratively. If key inputs are missing, ask all in one message before building. Provide defaults where noted.

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Labor categories | Job titles or SOC codes | Software Developer, Project Manager |
| Performance location | City/state or metro area | Washington, DC |
| Staffing | Headcount per labor category | 2 developers, 1 PM |
| Hours per year | Productive hours per person (default: 1,880) | 1,880 |
| Period of performance | Base year + option years | Base + 2 OYs |
| Contract start date | Needed for wage aging | October 1, 2026 |

### Optional Inputs (Defaults Applied If Not Provided)

| Input | Default | Notes |
|-------|---------|-------|
| Fringe rate | 32% | FICA + health + retirement + PTO + workers' comp |
| Overhead rate | 80% | Applied to labor + fringe |
| G&A rate | 12% | Applied to subtotal |
| Profit rate | 10% | Applied to total cost; see FAR 15.404-4 |
| Escalation rate | 2.5%/yr | Applied to labor and travel |
| Travel destinations | None | City/state per destination |
| Travel frequency | None | Trips/year per destination |
| Travel duration | None | Nights per trip |
| Number of travelers | All staff | Travelers per trip |
| Travel months | Max monthly rate | Specific months if known |
| FY for per diem | Current federal FY | Compute at build time (Oct-Sep cycle) |
| Duty station / origin | Performance location | For City Pair airfare lookup |
| NAICS code | None | Include in output if provided |
| PSC code | None | Include in output if provided |
| Partial start | Full year (12 months) | Specify months if base year is partial |
| FFP pricing structure | By period | "By period" or "By deliverable/CLIN" |

### Wrap Rate Component Guidance

Provide this when the user is unsure about cost pool rates:

| Component | Low | Mid | High | Notes |
|-----------|-----|-----|------|-------|
| Fringe | 25% | 32% | 40% | Higher for generous benefits, union shops |
| Overhead | 60% | 80% | 120% | Higher for SCIF/cleared, large firms |
| G&A | 8% | 12% | 18% | Higher for large corporate structures |
| Profit | 7% | 10% | 15% | FAR 15.404-4: risk, investment, complexity |

### Wrap Rate Presets by Contract Vehicle

**CRITICAL: ASK about contract vehicle before applying default wrap rates.** Workers have historically defaulted to skill mid (32/80/12/10, implied multiplier 2.93x) regardless of vehicle. That is correct for GSA MAS commercial or agency BPA non-cleared, but materially wrong for DoE M&O, cleared DoD, or OCONUS. Use this table to select MID scenario defaults keyed by the actual vehicle/environment the contract will use:

| Vehicle / environment | Fringe | Overhead | G&A | Profit | Implied multiplier | Notes |
|----------------------|--------|----------|-----|--------|-------------------|-------|
| GSA MAS (commercial) | 30% | 60% | 10% | 8% | **2.47x** | SIN 520, 541611, etc. Ceiling-rate vehicle |
| GSA MAS (cleared services) | 32% | 80% | 12% | 8% | **2.59x** | MAS with clearance overhead |
| Agency BPA / IDIQ (non-cleared) | 32% | 75% | 12% | 10% | **2.53x** | Mid-range commercial services |
| Agency BPA / IDIQ (cleared) | 32% | 95% | 12% | 10% | **2.91x** | TS/SCI in SCIF |
| DoD prime (non-cleared) | 32% | 80% | 12% | 10% | **2.93x** | DCMA oversight standard |
| **DoD prime (Secret, non-SCIF)** | **32%** | **100%** | **12%** | **10%** | **3.25x** | **Secret-cleared without SCIF** |
| DoD prime (SCIF / deployed) | 32% | 120% | 14% | 10% | **3.67x** | Full SCIF buildout, TS/SCI |
| **DoE M&O / FFRDC** | **35%** | **95%** | **12%** | **8%** | **3.18x** | **UT-Battelle, LANS, Sandia patterns; higher fringe, lower profit** |
| R&D / BAA CR | 32% | 90% | 12% | 8% | **2.99x** | Lower profit layer; fee separate on CR |
| OCONUS / hostile theater | 35% | 120% | 14% | 12% | **3.80x** | Hazard, austere env, insurance |

**Math check:** Multipliers computed as `(1+fringe) × (1+OH) × (1+G&A) × (1+profit)`. Example GSA MAS commercial: 1.30 × 1.60 × 1.10 × 1.08 = 2.47x. Verify this arithmetic in your workbook; Methodology narrative must match the actual cell values, not a rounded guess.

**Sanity band is vehicle-aware.** The generic 2.2x-3.5x "commercial CONUS" band does NOT apply to every vehicle. Vehicle-specific expected ranges:
- GSA MAS commercial / Agency BPA non-cleared: 2.2x-2.6x
- Agency BPA cleared / DoD non-cleared: 2.8x-3.0x
- DoD Secret non-SCIF: 3.1x-3.4x
- DoD SCIF / DoE M&O / R&D CR: 3.0x-3.8x
- OCONUS / hostile theater: 3.5x-4.2x

Flag for user review only if the MID multiplier falls OUTSIDE its vehicle-specific band. A 3.25x DoD Secret non-SCIF build is normal; a 3.25x GSA MAS commercial build is not.

**Use the MID column as your scenario mid. Generate LOW as mid minus ~20% on each component, HIGH as mid plus ~20%.**

If the user doesn't specify a vehicle, ASK before defaulting. If the user provides explicit rates, use those (custom rate workflow below).

**Custom rate workflow:** When the CO provides explicit wrap rates (e.g., for cleared/SCIF environments), those rates ARE the mid-scenario estimate. Do NOT use skill defaults as mid and the CO's rates as a scenario variant. Instead:
- Use CO-provided rates as MID scenario
- Generate LOW as mid minus offset (e.g., 20% reduction on each component)
- Generate HIGH as mid plus offset (e.g., 20% increase on each component)
- Document the CO-provided rates as the authoritative basis

These presets are anchors, not DCAA-certified rates. For final IGCE defensibility, prefer a certified indirect rate disclosure when available.

## Constants Reference

| Constant | Value | Source |
|----------|-------|--------|
| Standard work year | 2,080 hours | 40 hrs x 52 weeks; converts annual wages to hourly |
| Default productive hours | 1,880 hours/year | 2,080 minus holidays and avg leave |
| BLS wage cap (annual) | $239,200 | May 2024 OEWS reporting ceiling |
| BLS wage cap (hourly) | $115.00 | May 2024 OEWS reporting ceiling |
| BLS data vintage | May 2024 | Released April 2025; next release May 15, 2026 |
| GSA mileage rate | $0.70/mile | CY2025 GSA POV rate |
| First/last day M&IE | 75% of full day | FTR 301-11.101 |
| City Pair fare source | GSA City Pair Program | cpsearch.fas.gsa.gov; use YCA fare |

## Orchestration Sequence

### Step 0: Requirements Decomposition (Workflow A+ Only)

Converts an unstructured SOW/PWS into the structured inputs needed for pricing.

**Process:**
1. **Sufficiency check.** Scan for six priceable elements: labor categories, staffing levels, performance location, period of performance, deliverables, and travel. Flag anything missing. Hard stop if performance location is absent. If 3+ elements are missing and the document is under 500 words, ask the user whether to proceed with flagged assumptions or get clarification first.

2. **Task decomposition.** Parse into discrete task areas. For each: one-sentence description, primary skill discipline, complexity (routine/moderate/complex), recurring vs. finite.

3. **Labor category mapping.** Map tasks to SOC codes using the heuristics in Step 1. When a task spans disciplines, map to multiple categories.

4. **Staffing estimation.** Estimate FTEs per category based on scope indicators (number of systems, shift coverage language, surge/on-call, site count). Present as ranges when scope is ambiguous.

5. **Present decomposition table** for user validation:
```
Task Area               | Labor Category      | SOC Code | Est. FTEs | Basis
Application Development | Software Developer  | 15-1252  | 2-3       | 3 apps, agile
Security Operations     | InfoSec Analyst     | 15-1212  | 1-2       | Continuous monitoring
Project Oversight       | Project Manager     | 13-1082  | 1         | Single contract
```

6. **User validation gate (CRITICAL).** Response MUST END after presenting the decomposition table. Use `AskUserQuestion` with multi-choice defaults where possible. DO NOT self-approve and proceed to workbook build. DO NOT continue past the validation step in the same turn. Wait for explicit user confirmation before any Step 1+ work.

### Step 0.5: Shift Coverage Staffing (if PWS specifies 24x7, continuous, or on-call)

When the requirement specifies continuous coverage, convert to FTE using industry-standard backfill math:

```
24x7x365 single-seat coverage    = positions_per_shift x 4.2 FTE
24x7x365 double-seat coverage    = positions_per_shift x 8.4 FTE
8x5 single-seat coverage         = positions_per_shift x 1.2 FTE
```

The 4.2 factor accounts for ~25% non-productive time: PTO (10%), federal holidays (4%), training (5%), sick leave/turnover buffer (6%). Do NOT staff 4.0 FTE for 24x7 - that undercovers leave. Do NOT staff 1.0 FTE - that only covers one shift.

Document shift-coverage FTE derivation in the Methodology sheet: "24x7x365 SOC coverage at single-seat: 4.2 FTE per covered position per industry standard accounting for leave and training backfill."

**Escalation overlay.** Add on-call or overtime reserve for surge-driven work beyond base coverage. Typical on-call premium: 10-15% of base labor hours for incident response positions.

### Step 1: Map Labor Categories to SOC Codes

Map user job titles to Standard Occupational Classification codes.

**Domain triage first.** Before mapping, confirm: is this an IT/software requirement, a non-IT engineering requirement, a scientific/research requirement, a medical requirement, or a professional services requirement? This single branch prevents the most common mis-mapping (using 15-1211 Computer Systems Analyst for non-IT systems engineers).

**IT and software (15-12xx):**

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| IT / Program Manager (technology) | 11-3021 | Computer and Information Systems Managers |
| Management Analyst | 13-1111 | Management Analysts |
| Project Manager | 13-1082 | Project Management Specialists |
| Systems Engineer / Analyst (IT) | 15-1211 | Computer Systems Analysts |
| Cybersecurity / InfoSec Analyst | 15-1212 | Information Security Analysts |
| Network Architect | 15-1241 | Computer Network Architects |
| Database Administrator | 15-1242 | Database Administrators |
| Sysadmin | 15-1244 | Network and Computer Systems Administrators |
| Software Developer | 15-1252 | Software Developers |
| QA Tester | 15-1253 | Software QA Analysts and Testers |
| Help Desk / User Support | 15-1232 | Computer User Support Specialists |
| Data Scientist | 15-2051 | Data Scientists |

**Physical and non-IT engineering (17-2xxx):** Use these for reactors, aerospace, civil infrastructure, chemical, mechanical, and any "Systems Engineer" that integrates hardware rather than software.

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| Aerospace Engineer | 17-2011 | Aerospace Engineers |
| Biomedical Engineer | 17-2031 | Biomedical Engineers |
| Chemical Engineer | 17-2041 | Chemical Engineers |
| Civil Engineer | 17-2051 | Civil Engineers |
| Electrical Engineer | 17-2071 | Electrical Engineers |
| Industrial Engineer | 17-2112 | Industrial Engineers |
| Mechanical Engineer | 17-2141 | Mechanical Engineers |
| Nuclear Engineer | 17-2161 | Nuclear Engineers |
| Petroleum Engineer | 17-2171 | Petroleum Engineers |
| Systems Engineer (non-IT) | 17-2199 | Engineers, All Other |

**Science, research, and medical:**

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| Physicist | 19-2012 | Physicists |
| Chemist | 19-2031 | Chemists |
| Medical Scientist | 19-1042 | Medical Scientists, Except Epidemiologists |
| Registered Nurse | 29-1141 | Registered Nurses |
| Physician Assistant | 29-1071 | Physician Assistants |

**Program / Project Management — context-dependent:**

Program Manager SOC depends on the contract type:
- **Operations / administrative contracts:** 11-1021 (General and Operations Managers) — help desk, logistics, facilities, admin support
- **Engineering / technical contracts:** 11-9041 (Architectural and Engineering Managers) — reactor design, aerospace, infrastructure, R&D
- **IT / software contracts:** 11-3021 (Computer and Information Systems Managers) — software development, cybersecurity, enterprise IT

The engineering variant (11-9041) runs 20-40% higher than 11-1021 and is more defensible for technical programs. Document the choice in the Methodology sheet.

**Technical writing and support:**

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| Technical Writer | 27-3042 | Technical Writers |
| Contracting Specialist | 13-1020 | Buyers and Purchasing Agents |

When mapping is ambiguous, query multiple SOC codes and present the range.

### Step 2: Pull BLS Wage Data

**Use the BLS OEWS API skill.** For each labor category, query datatypes 04 (annual mean), 11-15 (annual 10th/25th/50th/75th/90th percentiles), plus 02 and 05 (employment RSE and wage RSE for data quality signals) at the user's performance location.

**Series ID format (25 chars total):** `{PREFIX:4}{AREA:7}{INDUSTRY:6}{SOC:6}{DATATYPE:2}` = 25. Common mistake: using 8-char SOC codes with trailing zeros. SOC must be exactly 6 chars (e.g., `151212` not `15121200`).

**Geography fallback:** metro (OEUM) > state (OEUS) > national (OEUN). Present the full wage distribution. Recommend the median (50th percentile) as default basis.

**Seniority modeling when BLS lacks granularity.** BLS typically does not break out junior / mid / senior variants within a single SOC. When a PWS specifies seniority tiers but the SOC is single, use percentile positioning as a documented convention:

- Junior / entry: P25 (25th percentile)
- Mid / journeyman: P50 (median)
- Senior: P50 to P75 depending on scope and BLS distribution shape
- Principal / director / SME: P75 to P90

Document this in Methodology as a convention, not a BLS standard. Percentile-based seniority modeling is defensible for price reasonableness but should be disclosed.

**MSA code renumbering.** OMB Bulletin 23-01 (2020 census) renumbered some MSAs in the May 2024 OEWS release. Confirmed via live BLS API (April 2026): Cleveland 17460 → 17410, Dayton 19380 → 19430. If a previously-valid MSA code returns NO_DATA across every SOC, the metro was renumbered - do NOT assume suppression. Check the current BLS area list or try adjacent codes. See the BLS OEWS skill's MSA realignment note.

**Wage cap.** If BLS returns "-" with footnote code 5, the wage exceeds the $239,200 cap. Use the cap as a lower bound and flag in the narrative.

**Cap decision tree when P75 ALSO caps.** In single-employer-dominated metros (ORNL/Y-12 Knoxville Nuclear, certain LANL/INL physicists), P90 and sometimes P75 both cap. The BLS skill's decision tree prescribes "use P75 when P90 is capped." When P75 is also capped:
1. Use BLS **Mean** (datatype 04) as the senior-tier anchor. Document as "P75 capped, Mean used as uncapped senior anchor."
2. Cross-reference commercial compensation surveys (Radford, Mercer, Payscale) for the specialty market.
3. Apply national P75/median ratio to the local median as a derived P75 estimate. Document as derivation, not BLS figure.
4. Never use $239,200 as the point estimate; it is a floor, not the value.

### Step 2B: Age BLS Wages to Contract Start Date

BLS OEWS data has a ~2-year lag (May 2024 estimates released April 2025). If the contract Period of Performance starts after the data reference period, the base wages must be aged forward to avoid understating costs.

```
months_gap = months between BLS data vintage (May 2024) and contract PoP start date
aging_factor = (1 + escalation_rate) ^ (months_gap / 12)
aged_annual_wage = annual_median * aging_factor
```

**Compute months_gap at build time** from the contract start date the user provides. Do NOT copy the 29-month example from this skill. Contract start dates vary; aging factors must be current.

Example: if the contract start is 29 months after the BLS data vintage, at 2.5% escalation the aging_factor = 1.025^(29/12) = ~1.061. A $100,000 BLS median becomes $106,100 before wrap rate buildup.

Use the aged wage as the basis for all subsequent calculations. Document the aging adjustment in the Methodology sheet: "BLS OEWS wages (data vintage: May 2024) aged forward [X] months to [contract start] at [escalation rate]%/yr to account for data lag."

**Contract start date default.** If the user does not specify, default to October 1 of the next federal fiscal year (computed at build time). Surface the assumption in the Summary sheet as a blue-font editable cell. If the user clarifies later, changing the cell recalculates the aging factor and the entire workbook. Do NOT invent a start date silently without noting it in the output.

**The aging factor must be a cell-referenced formula in the workbook, not hardcoded.** See Step 8 assumption block layout.

The escalation applied in Step 7 across option years starts AFTER this aging adjustment. Step 2B ages the base wage to the contract start; Step 7 escalates from that adjusted base across the period of performance. These are not double-counted.

### Step 3: FFP Wrap Rate Buildup

Build the fully burdened rate layer by layer for each labor category:

```
1. Direct Labor Rate    = aged_annual_wage / 2080
2. Fringe               = Direct Labor * fringe_rate
3. Labor + Fringe       = Direct Labor + Fringe
4. Overhead             = Labor_Fringe * overhead_rate
5. Subtotal             = Labor_Fringe + Overhead
6. G&A                  = Subtotal * ga_rate
7. Total Cost           = Subtotal + G&A
8. Profit               = Total_Cost * profit_rate
9. Fully Burdened Rate  = Total_Cost + Profit
```

**Implied wrap rate:** `implied_multiplier = fully_burdened_rate / direct_labor_rate`. For default rates: 1.0 x 1.32 x 1.80 x 1.12 x 1.10 = ~2.93x. FFP rates are typically higher than T&M because the contractor absorbs cost risk.

**Three-scenario approach:** Vary each component, not a single multiplier:

| Component | Low | Mid | High |
|-----------|-----|-----|------|
| Fringe | 25% | 32% | 40% |
| Overhead | 60% | 80% | 120% |
| G&A | 8% | 12% | 18% |
| Profit | 7% | 10% | 15% |

**Sanity band applies to MID only.** The mid-scenario implied multiplier should fall within 2.2x-3.5x for commercial-item CONUS services. The high-scenario multiplier naturally hits 4.18x from arithmetic (1.40 x 2.20 x 1.18 x 1.15) - that's expected, not an outlier, and does not trigger the "SCIF/niche" flag. Flag only the MID multiplier for review against the 2.2x-3.5x band.

For SCIF, cleared, or OCONUS environments, the mid multiplier routinely hits 3.0x-3.8x. That is not an outlier either - it's the actual market. When overhead is user-specified above 85% or the prompt references SCIF/cleared/OCONUS, document the elevated multiplier in methodology regardless of whether it falls inside or outside the nominal band.

### Step 4: Cross-Reference Against CALC+

**Use the GSA CALC+ Ceiling Rates API skill.** Follow the discovery-first pattern; do NOT use the `keyword=` parameter alone for rate statistics.

**CALC+ endpoint and query signature (inline to prevent silent-wrong-answer bugs):**

```
Base URL:  https://api.gsa.gov/acquisition/calc/v3/api/ceilingrates/
Auth:      None required
Parameter: keyword=<term>           (NOT q=; q is silently ignored and returns 265,308-record full corpus)
Better:    search=labor_category:<exact bucket name>   (precise, no cross-field contamination)
```

**Why this matters:** the `keyword=` parameter searches three fields simultaneously (labor_category, vendor_name, idv_piid). A search for "Program Manager" returns 7,763 records, but only ~1,849 are actually Program Manager LCATs; the remainder are vendor-name and PIID matches that pollute the statistics.

**CALC+ query-mode decision tree:**

1. **Discovery:** `suggest-contains=labor_category:<term>` - returns up to 100 bucket names with counts.
2. **If top 3 buckets have >=50 combined records:** use `search=labor_category:<exact bucket>` for each. This produces clean stats with no cross-field contamination.
3. **If buckets are fragmented (every bucket has <30 records, common for niche cleared cyber or specialty engineering):** fall back to `keyword=<term>` with `filter=price_range:30,500` to strip outliers. Document the contamination caveat in Methodology.
4. **If `suggest-contains` returns exactly 100 buckets:** the API truncated - narrow the discovery term.

**CRITICAL JSON paths for CALC+ statistics (all under `aggregations`, NOT top-level):**
```python
aggs = response_json["aggregations"]           # NOT response_json["wage_stats"]
count    = aggs["wage_stats"]["count"]
min_rate = aggs["wage_stats"]["min"]
max_rate = aggs["wage_stats"]["max"]
avg_rate = aggs["wage_stats"]["avg"]
median   = aggs["histogram_percentiles"]["values"]["50.0"]   # CORRECT median
p25      = aggs["histogram_percentiles"]["values"]["25.0"]
p75      = aggs["histogram_percentiles"]["values"]["75.0"]

# Discovery (suggest-contains) response shape:
buckets = aggs["labor_category"]["buckets"]    # NOT aggs["results"] or aggs["suggestions"]
for b in buckets:
    name   = b["key"]          # bucket label
    count  = b["doc_count"]    # records in that bucket
```

**WARNING:** Do NOT read from `wage_percentiles` (empty when page_size=0). Always use `histogram_percentiles`. Do NOT read `wage_stats` from the top level - it lives under `aggregations`.

**Apply `filter=price_range:30,500` by default** for professional services IGCE work. Strips clerical outliers (sub-$30 data entry rates) and sentinel placeholders ($9,999). Adjust bound for specialty work: `price_range:50,600` for cleared SCIF; `price_range:15,200` for routine administrative.

**Rate validation flagging - FFP premium is structural.** FFP burdened rates running above CALC+ medians is expected, not anomalous. CALC+ contains T&M/LH ceiling rates that do not embed the cost-risk premium FFP carries. Calibration:

- **0-15% above P50:** expected, within normal FFP premium band
- **15-40% above P50:** typical for FFP in DC/high-cost metros against worldwide CALC+; document as expected
- **>40% above P50:** requires justification - clearance, SCIF, specialty labor pool, or geographic premium not captured elsewhere
- **Below P25:** unusual - may indicate under-priced estimate or niche LCAT misalignment

Do NOT flag 15-40% divergence as "outlier requiring justification." Flag only divergence >40% or below P25.

**Dual-pool analysis for senior LCATs.** For "Senior X" requirements, both title-match (`suggest-contains=labor_category:Senior X`) and experience-match (`X + min_years_experience:8` filter) are legitimate benchmark pools. They often differ by 10-15% at median. Present both side-by-side. The CO decides which better matches the vendor's LCAT description.

### Step 5: Pull Per Diem Rates (If Travel Required)

**Use the GSA Per Diem Rates API skill.** Query monthly lodging rates and M&IE for each destination.

**City Pair airfare (optional):** When origin and destination are known, look up YCA fares at cpsearch.fas.gsa.gov. Skip if origin is unknown, OCONUS, local travel, or user provides their own airfare.

**Per-trip cost calculation:**
```
lodging_per_trip = nightly_rate * nights
travel_days = nights + 1
full_day_mie = mie_rate * max(0, travel_days - 2)
partial_day_mie = mie_rate * 0.75 * 2    # first and last day at 75%
mie_per_trip = full_day_mie + partial_day_mie
trip_total = lodging_per_trip + mie_per_trip
annual_travel = trip_total * trips_per_year * travelers
```

**Edge cases:**
- **1-night trip (2 travel days):** both days are partial, so `mie_per_trip = mie_rate * 0.75 * 2`. No full days.
- **Day trip (0 nights, 1 travel day):** single partial day per FTR 301-11.101. `mie_per_trip = mie_rate * 0.75`. Lodging = 0.
- **Scope to overnight trips.** Skill does not auto-handle multi-stop legs or international connections.

Use max monthly lodging rate as conservative ceiling if specific months not provided.

**If no travel is required:** do NOT omit Sheet 5. Produce it with a single "Travel - Not Applicable" block and a note about mod-based travel additions. See Step 8 workbook structure.

### Step 6: Handle Multi-Location Weighting

**When the user provides EXPLICIT headcount per location (e.g., "4 FTE Fort Meade, 3 FTE Colorado Springs"):** use Option C by default. The user has already answered the weighting question by structuring the input that way. Do NOT prompt for A/B/C; proceed.

**When staff allocation across sites is unspecified or ambiguous:** ask the user, with defaults:

- **Option A (fallback, conservative):** Use highest median across locations per category. Preserves information when allocation is truly unknown.
- **Option B (weighted):** `weighted_wage = (wage_A * pct_A) + (wage_B * pct_B)` if user provides split.
- **Option C (separate lines):** Dedicated staff per location get separate rows. Preferred when headcount is explicit.

Option C is the information-preserving choice when data is available. Option A discards real geographic wage differentials and should only be used when allocation is genuinely unknown.

### Step 7: Calculate Fixed Prices and Apply Escalation

**Two FFP pricing structures (ask user which applies):**

**Structure A: FFP by Period (default for services)**
```
period_labor = sum(fully_burdened_rate * productive_hours * headcount) per category
period_travel = travel costs from Step 5
period_fixed_price = period_labor + period_travel + ODCs
```

**Structure B: FFP by Deliverable/CLIN**

Three legitimate hour allocation approaches. Ask which applies when user provides scope weights:

- **Uniform allocation (default):** Apply scope percentage uniformly across all labor categories. `deliverable_hours = total_hours * scope_weight`.
- **Per-LCAT matrix:** Different allocation per labor category. Technical Writer may concentrate 75% of hours on D4 final report; Nuclear Engineer may spread evenly. User provides an N x M matrix (N labor categories by M deliverables).
- **Staffing-profile-driven:** Effort ramps (e.g., Technical Writer at 25% effort months 1-12, 75% effort months 13-18). Compute hours per deliverable from the overlap of staffing effort with deliverable date ranges.

**Validate scope percentages sum to 100%.** If they do not, flag and ask: normalize, reject, or use as-is with documentation. Default to flag-and-ask.

**Deliverable-timing escalation (by-deliverable only):**
- **Single-period PoP (e.g., 18-month feasibility study):** age wages once to contract start; hold flat across deliverables. No escalation between CLINs.
- **Multi-year milestone structures (e.g., 3-year OT with annual milestones):** age wages to contract start, then escalate each deliverable to its midpoint date. Rationale: midpoint tracks burn-weighted cost better than start or completion date.

**Partial-year proration:**
```
prorated_hours = productive_hours * (months_in_period / 12)
prorated_travel = annual_travel * (months_in_period / 12)
```

**Escalation across option years (Structure A):** `year_N_cost = base_year_cost * (1 + escalation_rate) ^ N`

**Scenario math:** Calculate three scenarios using low/mid/high wrap rate components:
```
low_burdened  = direct_rate * (1+fringe_low) * (1+oh_low) * (1+ga_low) * (1+profit_low)
mid_burdened  = direct_rate * (1+fringe_mid) * (1+oh_mid) * (1+ga_mid) * (1+profit_mid)
high_burdened = direct_rate * (1+fringe_high) * (1+oh_high) * (1+ga_high) * (1+profit_high)
```

Travel is identical across scenarios (per diem is a published rate, not affected by wrap rates).

### Step 8: Produce the FFP IGCE Workbook

Generate a multi-sheet .xlsx workbook using openpyxl. Use Excel formulas for all calculations. Run the recalc script (`python /mnt/skills/public/xlsx/scripts/recalc.py <file>`) before presenting.

**Workbook structure (7 sheets):**

**Sheet 1: IGCE Summary.** Labor categories as rows, periods as columns (Structure A) OR deliverables as columns (Structure B). Rate/Hr shows fully burdened FFP rate. Extra column for implied multiplier. Travel rows below labor. Placeholder rows for Airfare, Ground Transportation, ODCs with `0` value and "TBD" in an adjacent note column - NEVER put "TBD" text in cells that feed into SUM formulas (breaks the grand total with #VALUE!). Grand total with SUM formulas.

**Assumption cell layout (Sheet 1, rows 1-11):**
```
A1:  "IGCE Assumptions (FFP)"        (bold, merged A1:B1)
A2:  "Fringe Rate"                   B2: 0.32      (blue font, percentage)
A3:  "Overhead Rate"                 B3: 0.80      (blue font, percentage)
A4:  "G&A Rate"                      B4: 0.12      (blue font, percentage)
A5:  "Profit Rate"                   B5: 0.10      (blue font, percentage)
A6:  "Escalation Rate/Yr"            B6: 0.025     (blue font, percentage)
A7:  "Productive Hours/Year"         B7: 1880      (blue font)
A8:  "Base Year Months"              B8: 12        (blue font)
A9:  "BLS Vintage (YYYY-MM)"         B9: "2024-05" (blue font, text)
A10: "Contract Start (YYYY-MM)"      B10: "2026-10" (blue font, text)
A11: "Months Gap"                    B11: =(VALUE(LEFT(B10,4))-VALUE(LEFT(B9,4)))*12+(VALUE(MID(B10,6,2))-VALUE(MID(B9,6,2)))
A12: "Aging Factor"                  B12: =(1+B6)^(B11/12)   (formula)
A13: (blank row separator)
A14: header row for data table
```

All labor formulas reference these cells, including the aging factor. If the user changes escalation rate, contract start, or BLS vintage, the entire workbook recalculates correctly.

**Sheet 2: Cost Buildup.** One block per labor category. **Block spacing is 19 rows** (18 rows of content + 1 blank separator). First block starts at row 1; block N starts at row `1 + (N-1) * 19`. FBR is at `row(N) + 17` = `18 + (N-1) * 19`. Implied multiplier at `row(N) + 18` = `19 + (N-1) * 19`.

Per-block layout (first block, rows 1-19):

```
Row 1:  "Cost Buildup: [Labor Category]"                     (bold header)
Row 2:  A="BLS Base Wage (Annual, raw)"  B=[annual median from BLS]
Row 3:  A="Aging Factor"                 B=='IGCE Summary'!$B$12  (formula ref)
Row 4:  A="Aged Annual Wage"             B==B2*B3                  (formula)
Row 5:  A="Direct Labor Rate (Hourly)"   B==B4/2080                (formula)
Row 6:  (blank separator)
Row 7:  A="Fringe Rate"                  B==IGCE Summary'!$B$2     (formula ref, blue font)
Row 8:  A="Fringe Amount"                B==B5*B7                  (formula)
Row 9:  A="Labor + Fringe"               B==B5+B8                  (formula)
Row 10: A="Overhead Rate"                B==IGCE Summary'!$B$3     (formula ref, blue font)
Row 11: A="Overhead Amount"              B==B9*B10                 (formula)
Row 12: A="Subtotal (Labor+Fringe+OH)"   B==B9+B11                 (formula)
Row 13: A="G&A Rate"                     B==IGCE Summary'!$B$4     (formula ref, blue font)
Row 14: A="G&A Amount"                   B==B12*B13                (formula)
Row 15: A="Total Cost"                   B==B12+B14                (formula)
Row 16: A="Profit Rate"                  B==IGCE Summary'!$B$5     (formula ref, blue font)
Row 17: A="Profit Amount"                B==B15*B16                (formula)
Row 18: A="Fully Burdened Rate"          B==B15+B17                (formula, bold)
Row 19: A="Implied Multiplier"           B==B18/B5                 (formula, 0.00"x")
```

Cross-sheet references from Sheet 1 point to the FBR row: `='Cost Buildup'!$B$X` where X = `18 + (labor_category_index - 1) * 19`.

**Cell format conventions:**
- **Blue font (RGB 0,0,255):** hardcoded inputs (BLS raw wage in row 2; assumption cells B2:B10 on Sheet 1)
- **Black font:** all formula cells and formula-referenced cells
- **Annotation text:** cells containing source notes (e.g., "Source: BLS OEWS May 2024") MUST NOT start with `=`, `+`, `-`, or `@`. Excel interprets those as formula triggers. Lead with a space or prefix with `Source:`.

**Sheet 3: Scenario Analysis.** Three columns (low/mid/high), each using its own fringe/overhead/G&A/profit rates. Display component rates at top of each column. Travel identical across scenarios. Summary row: "Range: $X (low) to $Y (high), Mid estimate: $Z." Note that scenarios do NOT respect Sheet 1's Base Year Months proration (B8) - scenarios always use full-year hours. Document this in Methodology to prevent a reviewer surprise.

**Sheet 4: Rate Validation.** BLS burdened rate (mid scenario) vs. CALC+ P25/P50/P75, min/max range, divergence percentage (formula), Status column. Use the calibrated flag thresholds from Step 4:

```
=IF(divergence_pct>0.40,"Above P50 +40% - requires justification",
  IF(divergence_pct<-0.25,"Below P25 - review under-pricing",
    IF(divergence_pct>0.15,"FFP premium within expected 15-40% band",
      "Competitive")))
```

**Sheet 5: Travel Detail.** Formula-driven per destination block. If no travel is required, Sheet 5 contains a single "Travel - Not Applicable" declaration and note:

```
Row 1: "Travel Detail: Not Applicable"
Row 3: "No travel required per PWS/SOW. Placeholder retained for contract file completeness."
Row 4: "If travel scope is added via modification, populate this sheet with destination, nights,"
Row 5: "trips/year, travelers, and the Summary travel rows will pull through automatically."
```

When travel IS required, use the full per-destination block:
```
Row 3:  A="Fiscal Year"           B=<current federal FY>          (blue font)
Row 4:  A="Nightly Lodging Rate"  B=[max monthly]                 (blue font)
Row 5:  A="M&IE Daily Rate"       B=[rate]                        (blue font)
Row 6:  A="First/Last Day M&IE"   B==B5*0.75                      (formula)
Row 7:  A="Nights per Trip"       B=[nights, 0 for day trip]       (blue font)
Row 8:  A="Travel Days"           B==IF(B7=0,1,B7+1)              (formula)
Row 9:  A="Lodging per Trip"      B==B4*B7                        (formula, 0 when nights=0)
Row 10: A="M&IE per Trip"         B==IF(B7=0,B6,B5*MAX(0,B8-2)+B6*2)  (formula)
Row 11: A="Trip Total"            B==B9+B10                       (formula)
Row 12: A="Trips per Year"        B=[trips]                       (blue font)
Row 13: A="Travelers"             B=[count]                       (blue font)
Row 14: A="Annual Travel Cost"    B==B11*B12*B13                  (formula, bold)
```

**Day-trip branch required.** Without the `IF(B7=0,...)` branches on rows 8 and 10, a day trip (Nights=0) produces 150% M&IE instead of the correct 75% single-partial-day per FTR 301-11.101. This is a silent wrong-answer bug at the workbook level; do not skip the IF branches even if all planned trips are overnight.

**Sheet 6: Methodology.** FFP-specific narrative for the contract file. Include:
- Wrap rate buildup with each cost pool explained
- FAR 15.404-1(a), 15.404-4, 16.202 citations
- Implied multiplier basis (note: 2.93x at defaults, within 2.2-3.5x sanity band for commercial-item CONUS)
- Note that FFP rates exceed T&M because contractor absorbs cost risk
- Data sources with dates
- Aging methodology (use `=TEXT(Sheet1!B12,"0.0000")` formula references so numeric values update when inputs change, not hardcoded strings)
- Escalation basis
- Travel methodology
- Seniority percentile convention (if applied) with disclosure
- SOC mapping decisions (e.g., "Systems Engineer mapped to 17-2199 Engineers All Other vs. 15-1211 because this is reactor engineering, not IT")
- Multi-location weighting choice (A/B/C) with rationale
- Shift-coverage FTE derivation (if 24x7)
- CALC+ query mode used (exact-match vs keyword) with contamination caveat if keyword mode
- Rate validation interpretation (FFP premium expected, not outlier)
- Exclusions (airfare TBD, ODCs TBD, subs not included, OCONUS not covered)
- NAICS/PSC if provided

**Sheet 7: Raw Data.** All API query parameters and responses: BLS series IDs (full 25-char), CALC+ keywords and exact-match buckets with record counts, per diem query details, City Pair fares if retrieved.

**Sheet 1 Summary column presentation:**

Drop the "Implied Multiplier" column from the Summary if all labor categories use the same wrap rates (all rows will show identical 2.93x, which looks like a copy-paste error to a reviewer). Retain the implied multiplier on Sheet 2 per-block and on Sheet 3 per-scenario. If retained on Summary, add a note: "Identical across rows because wrap rates are uniform; varies by scenario - see Scenario Analysis."

**Formatting standards:**
- Blue font (RGB 0,0,255) for all user-adjustable inputs and assumptions
- Black font for all formula cells
- Currency: $#,##0 with negatives in parentheses
- Percentage: 0.0%
- Bold headers with light gray fill
- Freeze panes below assumptions block on Sheet 1 (below row 13)
- Auto-size column widths
- Burden/multiplier display format: `0.00"x"`

When base year is partial, prorate: `=burdened_rate*$B$7*(B8/12)*headcount`. Travel prorates the same way. Full option years ignore B8.

Never output as .md or HTML unless explicitly requested.

### Step 9: Present the File

**Required final step. Do NOT skip.**

After recalc verification, copy the workbook to `/mnt/user-data/outputs/` and call `present_files` to surface the deliverable to the user:

```python
import shutil
shutil.copy(workbook_path, "/mnt/user-data/outputs/")
# Then call present_files with the filename
```

The skill is not complete until the file is delivered. Do not rely on the user asking "where's the file?" - push the deliverable explicitly.

## Edge Cases

**Labor categories not in BLS:** Find closest SOC code(s), query all candidates, present range, let user select, document mapping rationale.

**No CALC+ results:** Try broader keywords, then `suggest-contains` on the parent term. If still nothing, note CALC+ unavailable; estimate relies on BLS alone. Mark Status as "No CALC+ data." Do NOT use keyword= as a last resort without documenting the contamination caveat.

**BLS wage at reporting cap:** Use $239,200/$115.00 as lower bound. Flag in narrative that burdened rate is a conservative floor. For high-wage metros where P75 or P90 is capped, use P75 as the defensible upper anchor; cross-reference commercial surveys (Levels.fyi, Radford) for senior-level positioning.

**Standard rate travel locations:** Note when destination returns CONUS standard rate (flat, no seasonal variation).

**Partial-year periods:** Prorate hours and travel. Common: base year starts 3 months post-award = 9 months (1,410 hrs). Note proration in methodology.

**Implied multiplier sanity check:** If the MID-scenario implied multiplier falls outside 2.2x-3.5x, flag for user review. Below 2.2x suggests unrealistically low overhead assumptions. Above 3.5x suggests SCIF/OCONUS/niche conditions that should be documented. The high-scenario naturally exceeds 3.5x - do NOT flag it.

**Silent-wrong-answer traps:**
- `q=` parameter on CALC+ returns the full 265K-record corpus silently. Always use `keyword=` or `search=`.
- `wage_stats` read from top level returns None. Always read from `aggregations.wage_stats`.
- CALC+ discovery buckets live at `aggregations.labor_category.buckets`, each with `key` and `doc_count`. NOT `aggregations.results` or `aggregations.suggestions`.
- MSA code renumbering (Cleveland 17460 → 17410, Dayton 19380 → 19430) returns NO_DATA silently. Verify code if all datatypes return empty.
- BLS SOC with trailing zeros (151212 vs 15121200) fails the 25-char assertion AFTER you've already constructed several queries. Use exactly 6-char SOC.
- **Text starting with `=`, `+`, `-`, or `@` in ANY cell** is parsed as a formula by Excel. This applies to Methodology prose, labels, and source citations - not just Sheet 2 annotations. Prefix with a space or lead with a non-operator character.
- **Cross-sheet row index off-by-one on the DL hourly reference.** Row 4 of each Cost Buildup block is Aged Annual Wage; row 5 is Direct Labor Rate (Hourly). Scenario formulas and rate validation formulas that reference the DL hourly rate must use `5 + (i-1)*19`, NOT `4 + (i-1)*19`. Indexing off row 4 produces workbook totals in the billions because annual wage × hours is dimensionally wrong.

## What This Skill Does NOT Cover

Include as placeholder rows or methodology notes:
- **Airfare:** Use City Pair YCA fares when origin/destination known; otherwise TBD
- **Ground transportation:** Rental cars, mileage ($0.70/mile), taxi, rideshare
- **ODCs:** Equipment, licenses, materials, subscriptions (user must provide)
- **Subcontractor costs:** Requires separate estimate or vendor input
- **Fee/profit negotiation:** This skill estimates costs, not negotiation targets
- **OCONUS travel:** Per diem covers CONUS only; State Dept rates apply for OCONUS
- **T&M/LH contracts:** Use IGCE Builder LH/T&M
- **Cost-reimbursement:** Use IGCE Builder CR
- **Grant budgets:** Use Grant Budget Builder
- **Clearance processing / DCSA fees:** Require agency-specific input
- **Tempest, SCIF build-out, COMSEC equipment:** Require specialized quotes

## Quick Start Examples

**Basic FFP:** "Build an FFP IGCE for a 3-person dev team in DC, base plus 2 OYs"
Claude will: map to SOC codes, pull DC BLS wages, build layered wrap rates at low/mid/high, validate against CALC+, apply 2.5% escalation, produce 7-sheet xlsx.

**SOW-driven:** "Here's my PWS, I need an FFP cost estimate" [user uploads PWS]
Claude will: run Step 0 decomposition, PAUSE at validation gate for user confirmation, then full Workflow A with FFP buildup.

**With travel:** "FFP IGCE for 5-person IT team in DC, monthly travel to Seattle, base plus 4 OYs"
Claude will: ask for labor breakdown, run Steps 1-9 including City Pair lookup for DCA-SEA.

**Rate validation:** "Vendor proposes $185/hr for a Software Dev, FFP contract. Reasonable?"
Claude will: Workflow B. Dual-pool CALC+ analysis (title-match vs experience-match), position $185 within both, produce validation summary.

**Multi-location (explicit headcount):** "FFP IGCE for 4 FTE at Fort Meade, 3 FTE at Colorado Springs, quarterly travel COS to BWI"
Claude will: use Option C (separate lines per location) without prompting, pull BLS for both metros, calculate travel, produce combined workbook.

**Custom rates (cleared/SCIF):** "Use 35% fringe, 95% overhead, 15% G&A, 12% profit for a cleared environment"
Claude will: apply custom rates as MID scenario (not as a variant), set low = mid minus 20% offset, high = mid plus 20% offset, note cleared environment justification in methodology.

**24x7 coverage:** "SOC analyst coverage 24x7x365, Cleveland, base plus 2 OYs"
Claude will: compute 4.2 FTE single-seat per Step 0.5, pull BLS Cleveland (0017410 post-2023 OMB renumbering), build workbook.

**FFP by deliverable:** "18-month feasibility study, 4 milestones at 15/30/25/30 scope weight, Oak Ridge TN"
Claude will: ask whether uniform / per-LCAT matrix / staffing-profile allocation, age wages once to contract start (no mid-contract escalation on single-period PoP), produce by-deliverable workbook with Summary columns = CLINs.

---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*
