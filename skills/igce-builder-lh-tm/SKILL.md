---
name: igce-builder-lh-tm
description: >
  Build IGCEs for Labor Hour (LH) and Time-and-Materials (T&M) federal
  contracts using burden multiplier pricing. Orchestrates BLS OEWS, GSA
  CALC+, and GSA Per Diem skills. T&M adds materials estimation at cost
  (FAR 16.601(b)). Supports SOW/PWS decomposition into labor categories
  and rate validation against CALC+ market data. Trigger for: IGCE,
  independent government cost estimate, cost estimate, price estimate,
  labor hour IGCE, LH IGCE, T&M IGCE, time and materials estimate,
  build an IGCE, estimate costs for, how much should this contract cost,
  burden multiplier, burdened rate, IGCE with travel, IGCE with materials.
  Also trigger for pricing requirements, burdened rates, CALC+ rate
  comparison, or materials estimation for T&M. Do NOT use for FFP
  contracts or wrap rate buildup (use IGCE Builder FFP). Do NOT use for
  cost-reimbursement CPFF/CPAF/CPIF (use IGCE Builder CR). Do NOT use
  for grant budgets (use Grant Budget Builder). Requires BLS OEWS API,
  GSA CALC+ Ceiling Rates API, and GSA Per Diem Rates API skills.
---

# IGCE Builder: Labor Hour & Time-and-Materials (LH/T&M)

## Overview

This skill produces Independent Government Cost Estimates for Labor Hour and Time-and-Materials contracts. It uses a burden multiplier model: take the BLS base wage, multiply by a single factor that rolls up fringe, overhead, G&A, and profit into one number. This is the most common IGCE pricing approach for federal professional services. T&M adds a materials estimation step for non-labor costs reimbursed at cost.

**LH vs. T&M:** The only structural difference is materials. LH contracts pay hourly rates for labor only. T&M contracts pay hourly rates for labor plus reimburse materials at cost (FAR 16.601(b)). Both use the same burden multiplier for the labor component. If the user says "IGCE" without specifying a contract type, default to LH unless they mention materials, supplies, licenses, cloud hosting, or similar non-labor costs, in which case default to T&M.

**Required L1 skills (must be installed):**
1. **BLS OEWS API** -- market wage data by occupation and geography
2. **GSA CALC+ Ceiling Rates API** -- awarded GSA MAS schedule hourly rates
3. **GSA Per Diem Rates API** -- federal travel lodging and M&IE rates

**Required API keys (must be in user memory):**
- BLS API key (v2) for BLS OEWS
- api.data.gov key for GSA Per Diem
- CALC+ requires no key

If a key is missing, prompt the user to register: BLS at https://data.bls.gov/registrationEngine/, api.data.gov at https://api.data.gov/signup/

**Regulatory basis:** FAR 15.402 (cost/pricing data). FAR 15.404-1(b) (price analysis). FAR 16.601 (T&M/LH contracts and limited-use criteria).

## Workflow Selection

### Workflow A-LH: Labor Hour IGCE (Default)
User needs a cost estimate for a Labor Hour contract. Labor only, no materials. Execute Steps 1 through 9.
Triggers: "build an IGCE," "labor hour IGCE," "LH estimate," "estimate costs for," "price a requirement."

### Workflow A-TM: Time-and-Materials IGCE
Same as A-LH for labor, plus Step 5B for materials. T&M contracts reimburse materials at cost.
Triggers: "T&M IGCE," "time and materials estimate," or when user mentions materials, supplies, licenses, cloud hosting alongside hourly rates.

### Workflow A+: SOW/PWS-Driven Build
User provides a requirement document instead of structured labor inputs. Execute Step 0 first, validate, then route to A-LH or A-TM based on whether materials are needed.
Triggers: "build an IGCE from this SOW," "price this statement of work," or when user provides a block of requirement text.

### Workflow B: Rate Validation Only
User has proposed rates and wants to check reasonableness against market data.
Triggers: "is this rate reasonable," "validate these rates," "compare vendor pricing," "check this proposal."

**Workflow B steps:**
1. Collect the vendor's proposed labor categories and hourly rates.
2. For each category, query CALC+ per Step 4.
3. Position each rate: below 25th percentile (aggressive), 25th-75th (competitive), above 75th (premium), above 90th (outlier requiring justification).
4. Optionally run Steps 1-3 to show where the rate falls relative to BLS wages at different burden multiplier assumptions.
5. Produce Rate Validation sheet and narrative. No full workbook unless requested.

## Information to Collect

Ask for everything in a single pass. Provide defaults where noted.

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Labor categories | Job titles or SOC codes | Software Developer, InfoSec Analyst, PM |
| Performance location | City/state or metro area | Washington, DC |
| Staffing | Headcount per labor category | 2 developers, 1 analyst, 1 PM |
| Hours per year | Productive hours per person (default: 1,880; user input wins, see rule below) | 1,880 |
| Period of performance | Base year + option years | Base + 2 OYs |
| Contract start date | For wage aging | 2026-10-01 |

### Optional Inputs (Defaults Applied If Not Provided)

| Input | Default | Notes |
|-------|---------|-------|
| Burden multiplier | 2.0x | Mid scenario; low (1.8x) and high (2.2x) also produced |
| Escalation rate | 2.5%/yr | Applied to labor, travel, and materials |
| Shift coverage | Single shift | Specify 24x7 if needed; Step 0.5 computes FTE |
| Travel destinations | None | City/state per destination |
| Travel frequency | None | Trips/year per destination |
| Travel duration | None | Nights per trip (0 = day trip) |
| Number of travelers | All staff | Travelers per trip |
| Travel months | Max monthly rate | Specific months if known |
| FY for per diem | Current federal FY | Compute at build time (Oct-Sep cycle) |
| Duty station / origin | Performance location | For City Pair airfare lookup |
| NAICS code | None | Include in output if provided |
| PSC code | None | Include in output if provided |
| Partial start | Full year (12 months) | Specify months if base year is partial |
| Materials (T&M only) | None | Categories and estimated annual costs |

### Productive Hours Reconciliation (user input wins)

When the user provides productive hours per FTE (commonly 1,920 = 48 × 40, or 1,860 for heavy leave environments), USE THE USER VALUE. Do NOT silently replace with 1,880.

- If user gives `total_hours` and `fte` but not `productive_hours`, back-solve: `productive_hours = total_hours / fte`. If result deviates from 1,880 by more than 5%, flag in methodology.
- If user gives `productive_hours` directly in the handoff, use verbatim.
- Example formulas in this skill use 1,880 for illustration only. Do NOT hardcode 1,880 in your Sheet 1 formulas; reference `$B$6` (the user-provided or default value) instead.

### Contract Vehicle Usage Rule (burden multiplier tuning)

The vehicle collected in Required Inputs is NOT metadata only. It tunes the burden scenario range:

| Vehicle | Low | Mid | High | Notes |
|---------|-----|-----|------|-------|
| GSA MAS IT Schedule 70 (commercial) | 1.8 | 2.0 | 2.2 | Standard commercial IT services |
| OASIS+ (services-centric, commercial) | 1.9 | 2.1 | 2.3 | Slightly higher due to multi-agency overhead |
| Agency-specific IDIQ (cleared / DoD) | 2.0 | 2.2 | 2.4 | Cleared personnel, security overhead |
| DoD Secret cleared (SCIF-adjacent but not SCIF) | 2.2 | 2.4 | 2.6 | Facility clearance, compartmented work |
| SCIF-only (TS/SCI, compartmented) | 2.4 | 2.6 | 3.0 | SCIF facility overhead, TS/SCI eligibility premium |
| DoE M&O contract | 2.2 | 2.4 | 2.6 | M&O overhead structure |
| OCONUS | 2.6 | 2.9 | 3.2 | Hardship, foreign deployment |

If the user provides a vehicle not in the table, default to GSA MAS commercial and flag the assumption in methodology.

### Burden Multiplier Guidance

The burden multiplier converts BLS base wages to fully burdened rates (fringe + overhead + G&A + profit in one factor). Provide this when the user is unsure:

| Range | Typical Scenario |
|-------|-----------------|
| 1.5x - 1.7x | Lean contractor, minimal overhead, commercial-style work |
| 1.8x - 2.0x | Mid-range professional services, most IT contracts |
| 2.0x - 2.2x | Large contractor with compliance overhead |
| 2.2x - 2.5x | Cleared work, SCIF environments, high-overhead settings |
| 2.5x - 3.0x | Deployed, OCONUS, or specialized niche environments |

If user does not specify, use 2.0x as mid and produce low (1.8x) and high (2.2x) scenarios. If user provides a custom multiplier (e.g., 2.3x for cleared work), set low = custom - 0.2, high = custom + 0.2.

## Constants Reference

| Constant | Value | Source |
|----------|-------|--------|
| Standard work year | 2,080 hours | 40 hrs x 52 weeks; converts annual wages to hourly |
| Default productive hours | 1,880 hours/year | 2,080 minus holidays and avg leave |
| Annual coverage hours (24x7) | 8,760 hours | 24 x 365; divide by 2,080 × availability for FTE |
| Default burden multiplier | 2.0x | Mid-range professional services |
| Low scenario burden | 1.8x | Lower bound for scenario analysis |
| High scenario burden | 2.2x | Upper bound for scenario analysis |
| Default escalation rate | 2.5% annually | Standard federal IGCE assumption |
| BLS wage cap (annual) | $239,200 | May 2024 OEWS reporting ceiling |
| BLS wage cap (hourly) | $115.00 | May 2024 OEWS reporting ceiling |
| OEWS data year | 2024 | May 2024 estimates |
| GSA mileage rate | $0.70/mile | CY2025 GSA POV rate |
| First/last day M&IE | 75% of full day | FTR 301-11.101 |
| City Pair fare source | GSA City Pair Program | cpsearch.fas.gsa.gov; use YCA fare |

## Orchestration Sequence

### Step 0: Requirements Decomposition (Workflow A+ Only)

Converts an unstructured SOW/PWS into structured pricing inputs.

**Process:**
1. **Sufficiency check.** Scan for six priceable elements: labor categories, staffing levels, performance location, period of performance, deliverables, and travel. Flag anything missing. Hard stop if performance location is absent. If 3+ elements missing and document is under 500 words, ask user whether to proceed with assumptions or get clarification.

2. **Task decomposition.** Parse into discrete task areas with description, skill discipline, complexity, and recurring vs. finite classification.

3. **Domain triage.** Identify agency domain (DoD / IC / DOE / civilian IT / research / medical) BEFORE SOC mapping. Domain signals which SOC block applies: DOE → 17-2xxx physical engineering; IC/DoD cyber → 15-1212; civilian IT → 15-125x software/systems; research → 19-1xxx / 15-2xxx; medical → 29-xxxx.

4. **Labor category mapping.** Map tasks to SOC codes using Step 1 heuristics with domain triage result. When a task spans disciplines, map to multiple categories.

5. **Staffing estimation.** Estimate FTEs per category based on scope indicators (system count, shift coverage, surge language, site count). If 24x7 coverage is required, invoke Step 0.5. Present as ranges when ambiguous.

6. **Present decomposition table** for user validation:
```
Task Area               | Labor Category      | SOC Code | Est. FTEs | Basis
Application Development | Software Developer  | 15-1252  | 2-3       | 3 apps, agile
Security Operations     | InfoSec Analyst     | 15-1212  | 1-2       | Continuous monitoring
Project Oversight       | Project Manager     | 13-1082  | 1         | Single contract
```

7. **User validation gate.** Confirm before proceeding. Also determine LH vs. T&M: "Does this requirement include materials the contractor will procure (software licenses, cloud hosting, hardware)? If yes, I'll build a T&M IGCE with materials. If labor only, I'll build LH."

### Step 0.5: Shift Coverage Staffing (If 24x7 or Multi-Shift)

If the requirement specifies 24x7 coverage, around-the-clock SOC, NOSC, help desk, or continuous monitoring, headcount must be grossed up from productive hours to coverage hours.

**Single-seat 24x7 (one analyst always on duty):**
```
annual_coverage_hours = 24 * 365 = 8,760
productive_hours_per_fte = 2,080
availability_factor = 0.50   # leave, training, turnover, overlap
single_seat_fte = 8,760 / (2,080 * availability_factor) = ~8.4 FTE
```
Simplification: use 4.2 FTE for single-seat 24x7 as the common industry convention (accounts for 50% availability + leave + overlap).

**Double-seat 24x7 (two analysts always on duty):** 8.4 FTE.

**12x5 coverage (business hours, weekdays only):** 60 hrs/wk × 52 = 3,120 annual hrs. 3,120 / 1,880 = 1.66 FTE single-seat, ~2 FTE with overlap.

**16x7 coverage (extended hours, every day):** 16 × 365 = 5,840 annual hrs. 5,840 / 1,880 × availability = ~3.1 FTE single-seat.

Document the FTE math in Sheet 5 Methodology. Do NOT quietly use 3 FTE for 24x7 coverage: that understaffs by 28%.

### Step 1: Map Labor Categories to SOC Codes

Map user job titles to SOC codes. Apply domain triage from Step 0 first.

**IT and Professional Services (most common):**

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| Program Manager (general ops) | 11-1021 | General and Operations Managers |
| Program Manager (IT) | 11-3021 | Computer and Information Systems Managers |
| Program Manager (engineering) | 11-9041 | Architectural and Engineering Managers |
| Project Manager | 13-1082 | Project Management Specialists |
| Management Analyst | 13-1111 | Management Analysts |
| Systems Engineer / Analyst (IT) | 15-1211 | Computer Systems Analysts |
| Software Developer | 15-1252 | Software Developers |
| Cybersecurity / InfoSec | 15-1212 | Information Security Analysts |
| Network Architect | 15-1241 | Computer Network Architects |
| DBA | 15-1242 | Database Administrators |
| Sysadmin | 15-1244 | Network and Computer Systems Administrators |
| QA Tester | 15-1253 | Software QA Analysts and Testers |
| Help Desk | 15-1232 | Computer User Support Specialists |
| Data Scientist | 15-2051 | Data Scientists |
| Technical Writer | 27-3042 | Technical Writers |
| Contracting Specialist | 13-1020 | Buyers and Purchasing Agents |

**Physical / DOE / Defense Engineering (use these for hardware, labs, weapons systems, DOE M&O, physical infrastructure):**

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| Aerospace Engineer | 17-2011 | Aerospace Engineers |
| Biomedical Engineer | 17-2031 | Biomedical Engineers |
| Chemical Engineer | 17-2041 | Chemical Engineers |
| Civil Engineer | 17-2051 | Civil Engineers |
| Electrical Engineer | 17-2071 | Electrical Engineers |
| Electronics Engineer | 17-2072 | Electronics Engineers, Except Computer |
| Environmental Engineer | 17-2081 | Environmental Engineers |
| Industrial Engineer | 17-2112 | Industrial Engineers |
| Mechanical Engineer | 17-2141 | Mechanical Engineers |
| Nuclear Engineer | 17-2161 | Nuclear Engineers |
| Petroleum Engineer | 17-2171 | Petroleum Engineers |
| Engineers, All Other (catch-all) | 17-2199 | Engineers, All Other |

When mapping is ambiguous, query multiple SOC codes and present the range. PM mapping is context-dependent: do NOT default to 11-3021 for non-IT programs.

**PM mapping decision rule (addresses the -21% CALC+ divergence trap on 15-1299):**

| Context | Default SOC | Why |
|---------|-------------|-----|
| IT task order PM at DoD/IC installation | 11-3021 Computer and Information Systems Managers | Matches the IT PM labor pool in CALC+; validates within ±5% |
| IT task order PM at civilian agency | Pull BOTH 11-3021 and 13-1082; pick the one with <15% CALC+ divergence | Civilian agency mix varies |
| Physical engineering PM / hardware program | 11-9041 Architectural and Engineering Managers | DoE M&O, hardware programs, aerospace |
| Non-IT operations PM | 11-1021 General and Operations Managers | Ops / logistics / services |
| Technical-but-not-IT PM at DoD | 13-1082 Project Management Specialists | Specialty services, not tech-stack focused |

Do NOT default to 15-1299 (Computer Occupations, All Other) for IT PM. It under-represents DoD IT PM wages by ~20% vs CALC+.

**Network Engineer SOC disambiguation:**

| Title / Scope | SOC | Note |
|---|---|---|
| Network Engineer (design / architecture / enterprise redesign) | 15-1241 Computer Network Architects | Default; higher wage (~25% above sysadmin) |
| Network Engineer (ops / sysadmin / NOC tier 2-3) | 15-1244 Network and Computer Systems Administrators | Use when PWS scope is operations-heavy |

Default to 15-1241 (conservative) unless the PWS specifies operations/sysadmin scope. Document the choice and the alternative in the Raw Data sheet.

**Seniority inference when no tier label:** The user may provide a role title without an explicit "Junior/Mid/Senior" qualifier (e.g., "Project Manager," "Cybersecurity Engineer"). Default to P50 (median). Exception: **when the role is a PM on a technical or cleared contract (DoD, IC, cyber), default to P75.** The cleared-contract PM pool skews senior; P50 understates. Cite the basis in methodology.

**Divergence-triggered SOC re-pick (automate what manual analysis does):**

If an LCAT's BLS burdened rate shows >15% divergence vs CALC+ median AND the SOC was a judgment call (not user-specified), automatically pull alternative SOCs per the decision rules above, compute divergence for each, and pick the one that validates within ±15%. Retain all queried SOCs (including rejected alternatives) in the Raw Data sheet for defensibility; document the winner and the losers in Methodology.

**Raw Data sheet retention requirement:** The Raw Data sheet MUST include every SOC queried, including rejected alternatives. Example: if you initially pulled 15-1299 for IT PM, got -21% divergence, and switched to 11-3021, the Raw Data sheet shows BOTH series ID queries with the returned wages, not just the winner. This is audit-defensibility material.

### Step 2: Pull BLS Wage Data

**Use the BLS OEWS API skill.** For each labor category, query datatypes 04 (annual mean), 11-15 (10th through 90th percentiles) at the performance location.

**BLS series ID component breakdown (25 chars total):**
```
prefix(4) + area(7) + industry(6) + SOC(6) + datatype(2) = 25
OEU  M  +  0047900 +  000000  +  151212 +  13  = OEUM004790000000015121213
```
- Prefix OEUM = metro; OEUS = state; OEUN = national
- Area must be 7 chars (pad with leading zeros)
- SOC must be exactly 6 chars (no trailing zeros: 151212 not 15121200)
- Industry 000000 for cross-industry

Use metro-level prefix (OEUM) when available. Fall back to state (OEUS), then national (OEUN). Present the full wage distribution.

**Seniority modeling via percentiles:** When an LCAT is explicitly Junior / Mid / Senior, map to wage percentiles rather than pulling three separate SOCs:
- Junior → P25 (datatype 12)
- Mid → P50 median (datatype 13)
- Senior → P75 (datatype 14)

Pull all 5 percentiles (P10/P25/P50/P75/P90) for any multi-level LCAT. Cite which percentile was used per LCAT in methodology.

**Silent-wrong-answer traps:**
- **MSA renumbering (2024 OMB Bulletin 23-01).** If a metro query returns NO_DATA across EVERY SOC (not just one), the metro was renumbered, not suppressed. Cleveland moved from 17460 to 17410. Dayton may also have moved. Verify against the current BLS MSA list: `https://www.bls.gov/oes/current/oessrci.htm`. Do NOT fall back to state assuming occupation suppression until you've checked the code.
- **Wrong trailing zeros.** 151212 is the 6-char SOC. 15121200 is a Standard SOC 8-digit format that will fail the 25-char series ID assertion AFTER several queries have already constructed.

If BLS returns "-" with footnote code 5, the wage exceeds the $239,200 cap. Use the cap as a lower bound and flag in the narrative.

### Step 2B: Age BLS Wages to Contract Start Date

BLS OEWS data has a ~2-year lag (May 2024 estimates released April 2025). If the contract Period of Performance starts after the data reference period, the base wages must be aged forward to avoid understating costs.

```
months_gap = months between BLS data vintage (May 2024) and contract PoP start date
aging_factor = (1 + escalation_rate) ^ (months_gap / 12)
aged_annual_wage = annual_median * aging_factor
```

Example: if the contract start is 29 months after the BLS data vintage, at 2.5% escalation the aging_factor = 1.025^(29/12) = ~1.061. A $100,000 BLS median becomes $106,100 before burden multiplier.

**Aging factor must be a cell-referenced formula in the workbook, NOT hardcoded.** Use the assumption block rows to hold BLS_vintage, contract_start, months_gap, and aging_factor. If the user changes the contract start assumption, the whole sheet must recompute correctly. See Step 8 assumption block layout.

Use the aged wage as the basis for all subsequent calculations. Document the aging adjustment in the Methodology sheet: "BLS OEWS wages (data vintage: [BLS_vintage]) aged forward [X] months to [contract start] at [escalation rate]%/yr to account for data lag."

If the user does not provide a contract start date, ask for one. If unknown, default to 6 months from today and note the assumption.

The escalation applied in Step 7 across option years starts AFTER this aging adjustment. Step 2B ages the base wage to the contract start; Step 7 escalates from that adjusted base across the period of performance. These are not double-counted.

### Step 3: Apply Burden Multiplier (Three Scenarios)

Convert BLS base wages to estimated fully burdened hourly rates:

```
hourly_base = aged_annual_wage / 2080
burdened_low  = hourly_base * burden_low    # default 1.8
burdened_mid  = hourly_base * burden_mid    # default 2.0
burdened_high = hourly_base * burden_high   # default 2.2
```

Note: 2,080 converts annual to hourly. Productive hours (1,880) are used separately in Step 7 for annual cost and account for holidays and leave.

### Step 4: Cross-Reference Against CALC+

**Invoke the GSA CALC+ Ceiling Rates API skill per its own documentation for base URL, pre-flight endpoint check, and `keyword=` vs `search=` rules.** Do NOT hardcode a CALC+ URL in this skill's code blocks; the CALC+ skill is authoritative and has moved endpoints in the past.

**IGCE use case for CALC+:** directional sanity-layer validation of BLS-burdened rates against GSA MAS awarded ceiling pool. `keyword=` is acceptable here per the CALC+ skill (sanity layer, not formal rate statistics). Full endpoint base URL, response envelope shape, and corpus skew guidance all live in the CALC+ skill.

**Fetch aggregations only:** `page_size=0` (aggregations compute over the full result set regardless of page_size).

Example call pattern (resolve actual base URL from the CALC+ skill at invocation time):
```
GET {CALC_BASE_URL}?keyword=Software+Developer&page_size=0
```

**CRITICAL JSON paths for CALC+ statistics:**
```python
aggs = response_json["aggregations"]
count    = aggs["wage_stats"]["count"]
min_rate = aggs["wage_stats"]["min"]
max_rate = aggs["wage_stats"]["max"]
avg_rate = aggs["wage_stats"]["avg"]
median   = aggs["histogram_percentiles"]["values"]["50.0"]   # CORRECT median
p25      = aggs["histogram_percentiles"]["values"]["25.0"]
p75      = aggs["histogram_percentiles"]["values"]["75.0"]
```

**WARNING:** Do NOT read `wage_stats` or `histogram_percentiles` from the top level. They live under `aggregations.*`. Do NOT read from `wage_percentiles` (empty when page_size=0). Always use `histogram_percentiles`.

**Dual-pool analysis for senior LCATs:** When title-match alone returns N<10, add a second query with experience-anchored keyword:
- Pool A (title-match): `keyword=Senior+Software+Engineer`
- Pool B (experience-match): `keyword=Software+Engineer+10+years`

Report both counts and medians. Use Pool A primary if N≥10; otherwise blend or cite Pool B as sanity layer.

**Rate validation band for LH/T&M (BLS burdened mid vs CALC+ median):**

LH/T&M burdened rates are a DIRECT comparison to CALC+ ceiling rates (both represent total billable hourly labor). Tighter tolerance than FFP or CR.

| Divergence | Interpretation | Action |
|------------|---------------|--------|
| 0 to ±5% | Expected range | Accept without explanation |
| ±5 to ±15% | Cite range | Document in narrative, show distribution |
| > ±15% | Needs justification | Flag in Status column |

Divergence formula: `((bls_burdened - calc_median) / calc_median) * 100`. Divergence is a data point requiring explanation, not an error.

### Step 5: Pull Per Diem Rates (If Travel Required)

**Use the GSA Per Diem Rates API skill.** Query monthly lodging rates and M&IE for each destination.

**City Pair airfare (optional):** When origin and destination are known, look up YCA fares at cpsearch.fas.gsa.gov. Skip if origin unknown, OCONUS, local travel, or user provides own airfare.

**Per-trip cost by trip length:**

**Standard multi-night trip (2+ nights):**
```
lodging_per_trip = nightly_rate * nights
travel_days = nights + 1
full_day_mie = mie_rate * max(0, travel_days - 2)
partial_day_mie = mie_rate * 0.75 * 2    # first and last day at 75%
mie_per_trip = full_day_mie + partial_day_mie
trip_total = lodging_per_trip + mie_per_trip
```

**1-night trip:**
```
lodging_per_trip = nightly_rate * 1
mie_per_trip = mie_rate * 0.75 * 2   # both days partial
trip_total = lodging_per_trip + mie_per_trip
```

**0-night day trip (same-day return):**
```
lodging_per_trip = 0                 # no overnight stay
mie_per_trip = mie_rate * 0.75       # single partial day only
trip_total = mie_per_trip
```

```
annual_travel = trip_total * trips_per_year * travelers
```

Use max monthly lodging rate as conservative ceiling if specific months not provided.

**No travel case:** If user confirms zero travel, do NOT build Sheet 4 with placeholder zeros that break SUM formulas. Use a minimal sheet with text "Travel Not Applicable" and no cell references. Sheet 1 Travel row = 0 literal.

### Step 5B: Materials Estimation (T&M Only)

T&M contracts reimburse materials at cost per FAR 16.601(b). Skip this step for LH workflows.

**Common T&M materials categories:**

| Category | Examples | Estimation Approach |
|----------|---------|---------------------|
| Software licenses | JIRA, Confluence, IDE licenses | Per-seat annual cost x users |
| Cloud hosting / IaaS | AWS, Azure, GCP | Monthly spend x 12 |
| Hardware / equipment | Laptops, monitors, peripherals | Per-unit cost x quantity, typically year 1 only |
| Training / certifications | Cloud certs, security clearance | Per-person cost x staff |
| Subscriptions / SaaS | Monitoring tools, data services | Annual subscription cost |
| Lab / test environments | Test servers, sandbox environments | Monthly or annual cost |

**If user provides specifics:** Create Materials Detail rows with annual cost, apply escalation across option years (same rate as labor).

**If user says materials exist but no specifics:** Include placeholder rows with numeric 0 (NOT text "TBD") for each common category. Note in methodology that materials must be added before IGCE is complete. Text "TBD" in numeric cells breaks SUM formulas.

**CRITICAL: Materials are NOT affected by the burden multiplier.** They are reimbursed at cost. Burden only applies to labor. Keep materials and labor cost streams separate in all formulas.

**Materials Handling Fee Decision Gate (REQUIRED for T&M):**

FAR 16.601(b)(2) lets the contractor recover actual cost for materials. FAR 31.205-26(e) permits a reasonable material handling fee IF the contractor's indirect rates already include such costs. Most T&M IGCEs default to pure at-cost with no handling fee. But the decision must be surfaced, not silently defaulted. Before computing materials totals, explicitly state:

- **Default choice: pure at-cost (no handling fee).** Document in methodology: "Materials priced at cost per FAR 16.601(b)(2). No material handling fee applied. If the awarded contractor has a DCAA-approved material handling rate in their indirect pools, the government may apply it post-award; IGCE remains at cost as the cost-side baseline."
- **Alternative: include a handling fee** if the solicitation specifically contemplates one or the user asks. Handling fee cap: commonly 5-10% of materials cost; never apply G&A or profit on top of the fee. Cite FAR 31.205-26 in methodology.

Ask the user explicitly if the contract anticipates a handling fee before applying one. If not surfaced, default to at-cost with the methodology note above. Silent defaults are the failure mode.

**Materials in IGCE Summary (Sheet 1):**
```
Materials Subtotal       |     |         | $45,000    | $46,125    | $47,278    | $138,403
  Software Licenses      |     |         | $15,000    | $15,375    | $15,759    | $46,134
  Cloud Hosting          |     |         | $24,000    | $24,600    | $25,215    | $73,815
  Hardware               |     |         | $6,000     | $6,150     | $6,304     | $18,454
```

### Step 6: Handle Multi-Location Weighting

**Option A (default blend):** Use highest median across locations per category. Use when user does not specify per-location headcount.

**Option B (weighted):** `weighted_wage = (wage_A * pct_A) + (wage_B * pct_B)` if user provides split.

**Option C (separate lines, DEFAULT when headcount per location is explicit):** Dedicated staff per location get separate rows. Do NOT prompt for Option A/B/C when user gave headcount like "4 FTE Fort Meade, 3 FTE Colorado Springs": go straight to Option C.

### Step 7: Calculate Annual Costs, Prorate, and Apply Escalation

**Labor cost per category per year (full year):**
```
annual_labor = burdened_hourly * productive_hours * headcount
```

**Partial-year proration:**
```
prorated_hours = productive_hours * (months_in_period / 12)
prorated_labor = burdened_hourly * prorated_hours * headcount
prorated_travel = annual_travel * (months_in_period / 12)
prorated_materials = annual_materials * (months_in_period / 12)
```

**Escalation:** `year_N_cost = base_year_cost * (1 + escalation_rate) ^ N`

Apply to labor, travel, and materials. Default 2.5%.

**Scenario math (three burden levels across all periods):**
```
low_year_N  = (hourly_base * burden_low)  * productive_hours * headcount * (1+esc)^N
mid_year_N  = (hourly_base * burden_mid)  * productive_hours * headcount * (1+esc)^N
high_year_N = (hourly_base * burden_high) * productive_hours * headcount * (1+esc)^N
```

Travel and materials are identical across all three scenarios (per diem is published; materials are at cost). **Sheet 2 formula:** Each scenario's period total = labor(at that burden) + travel + materials. Do NOT apply burden to travel or materials.

### Step 8: Produce the IGCE Workbook

Generate a multi-sheet .xlsx workbook using openpyxl. Use Excel formulas for all calculations. Run the recalc script (`python /mnt/skills/public/xlsx/scripts/recalc.py <file>`) before presenting.

**Workbook structure (6 sheets for LH, 7 for T&M; subtract 1 if no travel):**

**Sheet 1: IGCE Summary.** Labor categories as rows, periods as columns. Qty, Rate/Hr, annual cost per period. Travel rows below labor. For T&M: Materials rows below travel. Placeholder rows for Airfare, Ground Transportation, ODCs as numeric 0 (NOT text "TBD") to prevent #VALUE! errors in SUM formulas. Grand total with SUM formulas.

**Assumption cell layout (Sheet 1, rows 1-11) — LOCK THIS EXACTLY:**
```
A1: "IGCE Assumptions"                         (bold, merged A1:B1)
A2: "Burden Multiplier (Low)"                  B2: 1.8     (blue)
A3: "Burden Multiplier (Mid)"                  B3: 2.0     (blue)
A4: "Burden Multiplier (High)"                 B4: 2.2     (blue)
A5: "Escalation Rate"                          B5: 0.025   (blue, pct)
A6: "Productive Hours/Year"                    B6: 1880    (blue)
A7: "Base Year Months"                         B7: 12      (blue; <12 for partial)
A8: "BLS Vintage"                              B8: "May 2024"  (blue)
A9: "Contract Start"                           B9: 2026-10-01  (blue, date)
A10: "Months Gap"                              B10: =DATEDIF(B8,B9,"m")  (formula)
A11: "Aging Factor"                            B11: =(1+B5)^(B10/12)      (formula)
A12: (blank row separator)
A13: header row for data table
```

**DOWNSTREAM CELL REFERENCES — MEMORIZE THESE; DO NOT DRIFT:**

```
$B$2 = Burden Low                    (Sheet 2 low scenario formulas)
$B$3 = Burden Mid                    (Sheet 1 burdened-rate formulas + Sheet 2 mid)
$B$4 = Burden High                   (Sheet 2 high scenario formulas)
$B$5 = Escalation Rate               (ALL option-year AND materials formulas)
$B$6 = Productive Hours/Year         (reference only; do NOT put in formulas)
$B$7 = Base Year Months              (base-year proration as $B$7/12)
$B$11 = Aging Factor                 (multiplies ALL raw BLS wages)
```

**Validation gate: before writing Sheet 1 formulas, paste the reference map above into your working notes.** Workers have shipped off-by-one bugs where `$B$4` was treated as escalation (actually High burden) and `$B$6` as Base Year Months (actually Productive Hours). One scenario produced a $105M/FTE base year before the worker caught the drift on value inspection. Recalc does not detect this because the formulas are syntactically valid; they just reference the wrong cells.

**Sheet 2: Scenario Analysis.** Three side-by-side tables (low/mid/high burden). Burden multiplier cells in blue font. Blocks are 15 rows each per LCAT (13 content + 2 separator).

**Block layout formula:** `row(N) = 1 + (N-1) * 15` where N is the LCAT index. Within each block (offsets from block top):
- +1: LCAT header (merged)
- +2: "Measure" | "Value" | blank | "Period" | Low | Mid | High
- +3: BLS Base Annual Wage (hardcoded from raw BLS pull)
- +4: Aged to Contract Start (= base × aging_factor)
- +5: Hourly base (annual / 2080)
- +6: Burdened Low (= hourly × $B$2)
- +7: Burdened Mid (= hourly × $B$3)
- +8: Burdened High (= hourly × $B$4)
- +10 through +13: period rows (Base, OY1, OY2, OY3) × three burden columns
- +14: Total row (SUM of +10 through +13)

Travel and materials identical across scenarios. Summary row at the bottom: "Range: $X (low) to $Y (high), Mid estimate: $Z."

**Annotation text gotcha:** Annotation cells (column C or D methodology notes) cannot START with `= + - @` or Excel tries to parse as a formula. Prefix with apostrophe (`'=2,080 hours/year`) or lead with a non-operator character (`"Note: 2,080 hours/year"`). Applies anywhere a cell value starts with those four characters.

**Sheet 3: Rate Validation.** BLS burdened rate (mid), CALC+ 25th/50th/75th percentiles, min/max range, divergence percentage (formula), Status column calibrated to LH/T&M bands.
```
Row 1: "Rate Validation (LH/T&M)"
Row 3: Headers: Category | BLS Burdened (mid) | CALC+ 25th | CALC+ 50th | CALC+ 75th | CALC+ Count | Divergence vs Median | Status
Row 4+: one row per category
  Divergence = (BLS_burdened - CALC_50th) / CALC_50th
  Status =
    IF(ABS(Divergence) <= 0.05, "Expected range",
    IF(ABS(Divergence) <= 0.15, "Cite range",
    "Needs justification"))
```

Dual-pool columns when title-match N<10: add "Pool A (Title)" and "Pool B (Experience)" median columns, cite N for each.

**Sheet 4: Travel Detail.** Formula-driven per destination (skip this sheet if no travel, use text "Travel Not Applicable" only):
```
Row 1: "Travel Cost Detail: [Destination]"  (bold header)
Row 3: A="Fiscal Year"           B=<current federal FY>          (blue)
Row 4: A="Nightly Lodging Rate"  B=[max monthly]                 (blue)
Row 5: A="M&IE Daily Rate"       B=[rate]                        (blue)
Row 6: A="First/Last Day M&IE"   B==B5*0.75                      (formula)
Row 7: A="Nights per Trip"       B=[nights, 0 for day trip]       (blue)
Row 8: A="Travel Days"           B==IF(B7=0,1,B7+1)              (formula)
Row 9: A="Lodging per Trip"      B==B4*B7                        (formula, 0 when nights=0)
Row 10: A="M&IE per Trip"        B==IF(B7=0,B6,B5*MAX(0,B8-2)+B6*2)  (formula)
Row 11: A="Trip Total"           B==B9+B10                       (formula)
Row 12: A="Trips per Year"       B=[trips]                       (blue)
Row 13: A="Travelers"            B=[count]                       (blue)
Row 14: A="Annual Travel Cost"   B==B11*B12*B13                  (formula, bold)
```

**Sheet 5: Methodology.** Narrative for the contract file.

**Important: do NOT merge section-header cells if you also write to column B on the same row.** openpyxl raises "'MergedCell' object attribute 'value' is read-only" when a merge covers A:C and then a write targets B of the merged range. Two-column label/value layout: put section headers on their own rows (no merge), then use adjacent A/B rows for label/value pairs.

**Required sections in methodology:**

- Contract type (LH or T&M) with FAR citation
- Regulatory basis (use the citation set below)
- Vehicle / NAICS / PSC (if provided)
- Performance location
- Period of performance
- Data sources with vintages (BLS OEWS [data vintage], CALC+ queried [date], Per Diem [current FY])
- SOC code mapping decisions (note any alternatives pulled and why the chosen one won)
- BLS aging adjustment (months_gap, aging_factor, formula reference)
- Productive hours assumption (cite PWS-provided value if applicable)
- Burden multiplier rationale plus scenario range
- Escalation basis
- Partial-year proration if applied
- Travel calculation methodology (including 0-night day trips if applicable)
- Rate validation (CALC+) with divergence explanations
- What is NOT included (airfare, ground, subcontractor, etc.)
- Limitations and caveats

**FAR citation set (use all applicable):**

- **FAR 15.402** (cost and pricing data): always cite for IGCE defensibility
- **FAR 15.404-1(b)** (price analysis): always cite
- **FAR 16.601** (T&M and LH contracts): always cite for this skill
- **FAR 16.601(b)(2)** (T&M only; materials reimbursed at cost): cite when materials present
- **FAR 16.601(c)(3)** (T&M surveillance requirement): REQUIRED in T&M methodology. Must explicitly acknowledge: "FAR 16.601(c)(3) requires appropriate government surveillance during performance to provide reasonable assurance that efficient methods and effective cost controls are used. The awarded contract file should document the surveillance plan."
- **FAR 31.205-46** (travel costs): REQUIRED when travel is in scope. Cite alongside FTR 301-11.101 for the 75% first/last-day M&IE rule.
- **FAR 31.205-26** (material costs): cite if a material handling fee is applied (see Step 5B).

**Labor Category Ceiling Hours requirement (LH and T&M per FAR 16.601(c)(2)):** Sheet 1 labor table already shows hours per LCAT. Methodology should annotate: "Labor Category Ceiling Hours presented per FAR 16.601(c)(2); contract ceiling hours per LCAT are binding NTE limits for solicitation purposes."

**Sheet 6: Raw Data.** All API query parameters and responses: BLS series IDs, CALC+ keyword + endpoint + record counts, per diem query details, City Pair fares if retrieved.

**Sheet 7: Materials Detail (T&M only).** One row per materials category with annual cost, escalation across periods, and subtotals. Blue font on all cost inputs. Note that materials are at cost, no burden applied. Use numeric 0 for unknown amounts (not text "TBD").

**Formatting standards:**
- Blue font (RGB 0,0,255) for all user-adjustable inputs and assumptions
- Black font for all formula cells
- Currency: `$#,##0` with negatives in parentheses
- Percentage: `0.0%`
- Bold headers with light gray fill
- Freeze panes below assumption block on Sheet 1 (below row 12)
- Auto-size column widths
- Burden multiplier display format: `0.0"x"`

When base year is partial, prorate: `=burdened_rate*$B$6*($B$7/12)*headcount`. Travel and materials prorate the same way. Full option years ignore $B$7.

Never output as .md or HTML unless explicitly requested.

### Step 8.5: Post-Recalc Sanity Gates (REQUIRED before presenting)

`recalc.py` returning zero formula errors is necessary but NOT sufficient. Syntactically valid formulas can reference the wrong cells and produce wildly wrong values. Run ALL three of these checks before calling `present_files`. If any fails, fix and re-run all three.

**Gate 1: Per-FTE annualized cost in defensible range.**

Pick the first LCAT in the workbook. Compute its base-year cost divided by its FTE count. The result MUST fall in `[100,000, 1,000,000]` dollars. Outside this range, the formulas are almost certainly referencing wrong cells.

```python
from openpyxl import load_workbook
wb = load_workbook(workbook_path, data_only=True)  # data_only=True reads cached formula values post-recalc
summary = wb["IGCE Summary"]
# Find the first LCAT row (below assumption block; check your actual row numbers)
first_lcat_fte = summary["C14"].value    # adjust to your LCAT column/row
first_lcat_base_cost = summary["F14"].value
per_fte = first_lcat_base_cost / first_lcat_fte if first_lcat_fte else 0
assert 100_000 <= per_fte <= 1_000_000, f"Per-FTE ${per_fte:,.0f} outside defensible range; check cell references"
```

A failed gate means your Sheet 1 formulas are likely referencing the wrong assumption cells. Review the DOWNSTREAM CELL REFERENCES map above and re-check every $B$n reference.

**Gate 2: Sheet 1 Grand Total == Sheet 2 Mid-Scenario Grand Total.**

Sheet 1's grand total and Sheet 2's mid-scenario grand total must match within $0.01. Divergence indicates the sheets are pulling from different assumption cells.

```python
sheet1_total = wb["IGCE Summary"]["F30"].value   # adjust to your grand total cell
sheet2_total = wb["Scenario Analysis"]["F15"].value  # adjust to mid-scenario total cell
assert abs(sheet1_total - sheet2_total) < 0.01, f"Sheet 1 ({sheet1_total}) != Sheet 2 Mid ({sheet2_total})"
```

**Gate 3: Burden multiplier at the top of Sheet 2 equals $B$3 on Sheet 1.**

```python
sheet2_mid_burden = wb["Scenario Analysis"]["B6"].value  # mid column burden row
sheet1_mid_burden = wb["IGCE Summary"]["B3"].value
assert abs(sheet2_mid_burden - sheet1_mid_burden) < 0.001, "Burden multiplier drift between sheets"
```

Only after all three pass, copy to outputs and call `present_files`.

### Step 8.6: Pre-Delivery Sanity Checklist (walk through before calling present_files)

Run this checklist mentally or in writing before delivering. Any "no" means stop and fix.

- [ ] **Skill triggered and announced.** First line of response acknowledges the LH/T&M skill was loaded. User can see which skill is running.
- [ ] **Cell references match the DOWNSTREAM CELL REFERENCES map.** No drift between prose and layout.
- [ ] **Per-FTE sanity gate passed.** First LCAT base-year cost / FTE is between $100K and $1M.
- [ ] **Sheet 1 total == Sheet 2 mid total** within $0.01.
- [ ] **Aging factor is a cell-referenced formula**, not a hardcoded multiplier.
- [ ] **Escalation not double-counted.** Option years apply escalation from base; base year does NOT also apply escalation.
- [ ] **Placeholder rows use numeric 0**, not text "TBD". SUM formulas intact.
- [ ] **Per diem FY matches contract start** (or fallback documented if target FY not yet published).
- [ ] **Travel math respects FTR 301-11.101** 75% first/last day M&IE rule; 0-night day trips use single-partial-day M&IE.
- [ ] **CALC+ divergence >15% items are justified** in Methodology (corpus mismatch, thin pool, etc.) or the SOC was re-picked.
- [ ] **Raw Data sheet includes rejected SOC alternatives** when a re-pick happened.
- [ ] **FAR citations present**: 16.601 (always), 16.601(b)(2) (T&M materials), 16.601(c)(2) (LCAT ceiling hours), 16.601(c)(3) (T&M surveillance), 31.205-46 (if travel).
- [ ] **Burden multiplier range matches contract vehicle** per the Contract Vehicle Usage Rule table.
- [ ] **Staffing handoff used as-is.** FTE counts and productive hours match the user-provided values.
- [ ] **Contract type labeled clearly** on Cover / Sheet 1 (LH vs T&M).

Only after all green, proceed to Step 9.

### Step 9: Present the File

After writing the workbook, copy to the outputs directory AND call `present_files` so the user sees a download link in the UI.

```python
import shutil
shutil.copy(workbook_path, "/mnt/user-data/outputs/IGCE_LH_<project>.xlsx")
# Then invoke the file-presentation tool
present_files(["/mnt/user-data/outputs/IGCE_LH_<project>.xlsx"])
```

Do NOT skip this step. A workbook that exists in the sandbox but is not presented looks like a silent failure to the user.

## Edge Cases

**Labor categories not in BLS:** Find closest SOC code(s), query candidates, present range, let user select, document rationale.

**No CALC+ results:** Try broader keywords. If still nothing, note unavailable; estimate relies on BLS alone. Mark Status "No CALC+ data."

**BLS wage at reporting cap:** Use $239,200/$115.00 as lower bound. Flag that burdened rate is a conservative floor.

**Standard rate travel locations:** Note when destination returns CONUS standard rate (flat, no seasonal variation).

**Partial-year periods:** Prorate hours, travel, and materials. Example: base year starts 3 months post-award = 9 months (1,410 hrs).

**Materials year-1 only items (T&M):** Hardware and initial setup costs often apply only to the base year. Do not escalate or repeat in option years unless the user specifies replacement cycles.

**User provides their own rates:** Use Workflow B (Rate Validation Only).

**Silent-wrong-answer traps:**
- `q=` parameter on CALC+ returns the full 265K-record corpus silently. Always use `keyword=` or `search=`.
- `wage_stats` read from top level returns None. Always read from `aggregations.wage_stats`.
- MSA code renumbering (Cleveland 17460 → 17410) returns NO_DATA silently. Verify code if all datatypes return empty.
- BLS SOC with trailing zeros (151212 vs 15121200) fails the 25-char assertion AFTER you've already constructed several queries. Use exactly 6-char SOC.
- Annotation text starting with `= + - @` triggers Excel formula parse. Escape with apostrophe or lead with text.
- ODC / placeholder cells set to text "TBD" break SUM formulas. Use numeric 0 literal.

## What This Skill Does NOT Cover

Include as placeholder rows or methodology notes:
- **Airfare:** Use City Pair YCA fares when origin/destination known; otherwise numeric 0 placeholder
- **Ground transportation:** Rental cars, mileage ($0.70/mile), taxi, rideshare
- **ODCs (LH):** Equipment, licenses, materials for LH contracts (user must provide; placeholders as numeric 0)
- **Subcontractor costs:** Requires separate estimate or vendor input
- **Fee/profit analysis:** This skill estimates costs, not negotiation targets
- **OCONUS travel:** Per diem covers CONUS only; State Dept rates for OCONUS
- **FFP contracts:** Use IGCE Builder FFP for wrap rate buildup
- **Cost-reimbursement:** Use IGCE Builder CR for CPFF/CPAF/CPIF
- **Grant budgets:** Use Grant Budget Builder

## Quick Start Examples

**Simple LH:** "Build an IGCE for a Systems Analyst in DC, base plus 2 option years"
Claude will: map to SOC 15-1211, pull DC BLS wages with percentiles, age to contract start via cell-referenced formula, apply 1.8x/2.0x/2.2x burden, validate against CALC+ at `keyword=` endpoint, apply 2.5% escalation, produce 6-sheet xlsx and present.

**T&M:** "T&M IGCE for a 4-person dev team in DC, they'll need AWS hosting and JIRA licenses, base plus 3 OYs"
Claude will: run full labor sequence plus Step 5B for materials, collect specifics, produce 7-sheet xlsx with materials separate from burden.

**SOW-driven:** "Here's my SOW, build me an IGCE" [user pastes or uploads SOW]
Claude will: run Step 0 decomposition, domain triage, validate, determine LH vs. T&M based on materials need, then run appropriate workflow.

**With travel:** "IGCE for a 5-person IT team in DC with monthly travel to Seattle, base plus 4 OYs"
Claude will: ask for labor breakdown, run Steps 1-9 including City Pair lookup for DCA-SEA.

**Rate validation:** "Vendor proposes $165/hr for a Software Dev in DC. Reasonable?"
Claude will: Workflow B. Pull CALC+ distribution via `keyword=`, position $165 against ±5 / ±15 / outside bands, optionally BLS context, produce validation summary.

**Multi-location (explicit headcount):** "Price a 10-person help desk split 6 Baltimore / 4 Philadelphia, quarterly travel to DC"
Claude will: use Option C (separate lines per location) without prompting, pull BLS for both metros, produce combined IGCE.

**Partial year:** "IGCE for a contract starting April 1, base year is 6 months, then 4 full OYs"
Claude will: prorate base to 6 months (940 hrs), full hours for OY1-4, note proration in methodology.

**24x7 coverage:** "SOC analyst coverage 24x7x365, Cleveland, base plus 2 OYs"
Claude will: compute 4.2 FTE single-seat per Step 0.5, pull BLS Cleveland (0017410 post-2023 OMB renumbering), build workbook.

**Day trip travel:** "Quarterly day trips DCA to Pentagon, 5 travelers"
Claude will: Step 5 0-night case (no lodging, single partial M&IE), Sheet 4 formulas handle nights=0 correctly.

**Cleared environment:** "Use 2.4x burden for a cleared IT support contract in DC"
Claude will: set mid=2.4x, low=2.2x, high=2.6x, note cleared justification in methodology.

**Physical engineering (DOE):** "LH IGCE for 3 mechanical engineers + 1 PM at Oak Ridge, base + 2 OYs"
Claude will: domain triage (DOE → 17-2xxx); map to 17-2141 Mechanical + 11-9041 Engineering Manager (NOT 11-3021 IT); pull Oak Ridge 28940; apply burden; validate with dual-pool CALC+; produce workbook.

**No travel:** "LH IGCE for on-site-only help desk in DC, base + 2 OYs"
Claude will: build labor workbook; Sheet 4 shows "Travel Not Applicable" text only; Travel row in Sheet 1 is literal 0; no SUM breakage.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*
