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

**Version 1.1** | April 2026

### Changelog
- **v1.1** (April 2026): Added Step 2B — BLS wage aging factor. Wages are now aged forward from BLS data vintage (May 2024) to contract start date using the escalation rate, closing the ~2-year data lag gap that was understating base year costs.
- **v1.0** (March 2026): Initial release.

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
User needs a cost estimate for a Labor Hour contract. Labor only, no materials. Execute Steps 1 through 8.
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
| Hours per year | Productive hours per person (default: 1,880) | 1,880 |
| Period of performance | Base year + option years | Base + 2 OYs |

### Optional Inputs (Defaults Applied If Not Provided)

| Input | Default | Notes |
|-------|---------|-------|
| Burden multiplier | 2.0x | Mid scenario; low (1.8x) and high (2.2x) also produced |
| Escalation rate | 2.5%/yr | Applied to labor, travel, and materials |
| Travel destinations | None | City/state per destination |
| Travel frequency | None | Trips/year per destination |
| Travel duration | None | Nights per trip |
| Number of travelers | All staff | Travelers per trip |
| Travel months | Max monthly rate | Specific months if known |
| FY for per diem | Current FY | FY2026 as of March 2026 |
| Duty station / origin | Performance location | For City Pair airfare lookup |
| NAICS code | None | Include in output if provided |
| PSC code | None | Include in output if provided |
| Partial start | Full year (12 months) | Specify months if base year is partial |
| Materials (T&M only) | None | Categories and estimated annual costs |

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

3. **Labor category mapping.** Map tasks to SOC codes using Step 1 heuristics. When a task spans disciplines, map to multiple categories.

4. **Staffing estimation.** Estimate FTEs per category based on scope indicators (system count, shift coverage, surge language, site count). Present as ranges when ambiguous.

5. **Present decomposition table** for user validation:
```
Task Area               | Labor Category      | SOC Code | Est. FTEs | Basis
Application Development | Software Developer  | 15-1252  | 2-3       | 3 apps, agile
Security Operations     | InfoSec Analyst     | 15-1212  | 1-2       | Continuous monitoring
Project Oversight       | Project Manager     | 13-1082  | 1         | Single contract
```

6. **User validation gate.** Confirm before proceeding. Also determine LH vs. T&M: "Does this requirement include materials the contractor will procure (software licenses, cloud hosting, hardware)? If yes, I'll build a T&M IGCE with materials. If labor only, I'll build LH."

### Step 1: Map Labor Categories to SOC Codes

Map user job titles to SOC codes. Common mappings:

| Common Title | SOC Code | BLS Title |
|-------------|----------|-----------|
| Program Manager | 11-1021 | General and Operations Managers |
| Project Manager | 13-1082 | Project Management Specialists |
| Management Analyst | 13-1111 | Management Analysts |
| Systems Engineer / Analyst | 15-1211 | Computer Systems Analysts |
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

When mapping is ambiguous, query multiple SOC codes and present the range.

### Step 2: Pull BLS Wage Data

**Use the BLS OEWS API skill.** For each labor category, query datatypes 04 (annual mean), 11-15 (10th through 90th percentiles) at the performance location.

Use metro-level prefix (OEUM) when available. Fall back to state (OEUS), then national (OEUN). Present the full wage distribution. Recommend the median (50th percentile) as default basis.

If BLS returns "-" with footnote code 5, the wage exceeds the $239,200 cap. Use the cap as a lower bound and flag in the narrative.

### Step 2B: Age BLS Wages to Contract Start Date

BLS OEWS data has a ~2-year lag (May 2024 estimates released April 2025). If the contract Period of Performance starts after the data reference period, the base wages must be aged forward to avoid understating costs.

```
months_gap = months between BLS data vintage (May 2024) and contract PoP start date
aging_factor = (1 + escalation_rate) ^ (months_gap / 12)
aged_annual_wage = annual_median * aging_factor
```

Example: BLS data from May 2024, contract starts October 2026 = 29 months gap. At 2.5% escalation: aging_factor = 1.025^(29/12) = ~1.061. A $100,000 BLS median becomes $106,100 before burden multiplier.

Use the aged wage as the basis for all subsequent calculations. Document the aging adjustment in the Methodology sheet: "BLS OEWS May 2024 wages aged forward [X] months to [contract start] at [escalation rate]%/yr to account for data lag."

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

**Use the GSA CALC+ Ceiling Rates API skill.** For each labor category, search with `page_size=0` to get aggregations.

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

**WARNING:** Do NOT read from `wage_percentiles` (empty when page_size=0). Always use `histogram_percentiles`.

Compare BLS burdened rate (mid scenario) to CALC+ median. Flag divergence >25%. Divergence formula: `((bls_burdened - calc_median) / calc_median) * 100`. Divergence is a data point requiring explanation, not an error.

### Step 5: Pull Per Diem Rates (If Travel Required)

**Use the GSA Per Diem Rates API skill.** Query monthly lodging rates and M&IE for each destination.

**City Pair airfare (optional):** When origin and destination are known, look up YCA fares at cpsearch.fas.gsa.gov. Skip if origin unknown, OCONUS, local travel, or user provides own airfare.

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

Edge case for 1-night trips: both days are partial, so `mie_per_trip = mie_rate * 0.75 * 2`.

Use max monthly lodging rate as conservative ceiling if specific months not provided.

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

**If user says materials exist but no specifics:** Include placeholder rows with "TBD" for each common category. Note in methodology that materials must be added before IGCE is complete.

**CRITICAL: Materials are NOT affected by the burden multiplier.** They are reimbursed at cost. Burden only applies to labor. Keep materials and labor cost streams separate in all formulas.

**Materials in IGCE Summary (Sheet 1):**
```
Materials Subtotal       |     |         | $45,000    | $46,125    | $47,278    | $138,403
  Software Licenses      |     |         | $15,000    | $15,375    | $15,759    | $46,134
  Cloud Hosting          |     |         | $24,000    | $24,600    | $25,215    | $73,815
  Hardware               |     |         | $6,000     | $6,150     | $6,304     | $18,454
```

### Step 6: Handle Multi-Location Weighting

**Option A (default, conservative):** Use highest median across locations per category.
**Option B (weighted):** `weighted_wage = (wage_A * pct_A) + (wage_B * pct_B)` if user provides split.
**Option C (separate lines):** Dedicated staff per location get separate rows.

Ask user which approach if multiple locations mentioned. Default to Option A.

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

**Workbook structure (6 sheets for LH, 7 for T&M):**

**Sheet 1: IGCE Summary.** Labor categories as rows, periods as columns. Qty, Rate/Hr, annual cost per period. Travel rows below labor. For T&M: Materials rows below travel. Placeholder rows for Airfare, Ground Transportation, ODCs with "TBD." Grand total with SUM formulas.

**Assumption cell layout (Sheet 1, rows 1-7):**
```
A1: "IGCE Assumptions"          (bold, merged A1:B1)
A2: "Burden Multiplier (Low)"   B2: 1.8    (blue font)
A3: "Burden Multiplier (Mid)"   B3: 2.0    (blue font)
A4: "Burden Multiplier (High)"  B4: 2.2    (blue font)
A5: "Escalation Rate"           B5: 0.025  (blue font, percentage)
A6: "Productive Hours/Year"     B6: 1880   (blue font)
A7: "Base Year Months"          B7: 12     (blue font; <12 for partial starts)
A8: (blank row separator)
A9: header row for data table
```

All labor formulas reference $B$3 (mid burden). Sheet 2 references $B$2, $B$3, $B$4 for scenarios. Base year formulas reference $B$7 for proration.

**Sheet 2: Scenario Analysis.** Three side-by-side tables (low/mid/high burden). Burden multiplier cells in blue font. Travel and materials identical across scenarios. Summary row: "Range: $X (low) to $Y (high), Mid estimate: $Z."

**Sheet 3: Rate Validation.** BLS burdened rate (mid), CALC+ 25th/50th/75th percentiles, min/max range, divergence percentage (formula), Status column.

**Sheet 4: Travel Detail.** Formula-driven per destination block:
```
Row 1: "Travel Cost Detail: [Destination]"  (bold header)
Row 3: A="Fiscal Year"           B=2026                          (blue font)
Row 4: A="Nightly Lodging Rate"  B=[max monthly]                 (blue font)
Row 5: A="M&IE Daily Rate"       B=[rate]                        (blue font)
Row 6: A="First/Last Day M&IE"   B==B5*0.75                      (formula)
Row 7: A="Nights per Trip"       B=[nights]                      (blue font)
Row 8: A="Travel Days"           B==B7+1                         (formula)
Row 9: A="Lodging per Trip"      B==B4*B7                        (formula)
Row 10: A="M&IE per Trip"        B==B5*MAX(0,B8-2)+B6*2          (formula)
Row 11: A="Trip Total"           B==B9+B10                       (formula)
Row 12: A="Trips per Year"       B=[trips]                       (blue font)
Row 13: A="Travelers"            B=[count]                       (blue font)
Row 14: A="Annual Travel Cost"   B==B11*B12*B13                  (formula, bold)
```

**Sheet 5: Methodology.** Narrative for the contract file. Include: data sources with dates (BLS OEWS May 2024, CALC+ queried [date], Per Diem FY2026), burden multiplier rationale plus scenario range, escalation basis, productive hours assumption, partial-year proration if applied, travel calculation methodology (first/last day at 75%), what is NOT included, CALC+ cross-reference and divergence explanations, NAICS/PSC if provided, contract type (LH or T&M), FAR 15.402 and FAR 15.404-1(b) references. For T&M: note materials reimbursed at cost per FAR 16.601(b)(2), government right to require competition for materials over SAT.

**Sheet 6: Raw Data.** All API query parameters and responses: BLS series IDs, CALC+ keywords and record counts, per diem query details, City Pair fares if retrieved.

**Sheet 7: Materials Detail (T&M only).** One row per materials category with annual cost, escalation across periods, and subtotals. Blue font on all cost inputs. Note that materials are at cost, no burden applied.

**Formatting standards:**
- Blue font (RGB 0,0,255) for all user-adjustable inputs and assumptions
- Black font for all formula cells
- Currency: $#,##0 with negatives in parentheses
- Percentage: 0.0%
- Bold headers with light gray fill
- Freeze panes below assumptions block on Sheet 1 (below row 8)
- Auto-size column widths
- Burden multiplier display format: `0.0"x"`

When base year is partial, prorate: `=burdened_rate*$B$6*($B$7/12)*headcount`. Travel and materials prorate the same way. Full option years ignore $B$7.

Never output as .md or HTML unless explicitly requested.

## Edge Cases

**Labor categories not in BLS:** Find closest SOC code(s), query candidates, present range, let user select, document rationale.

**No CALC+ results:** Try broader keywords. If still nothing, note unavailable; estimate relies on BLS alone. Mark Status "No CALC+ data."

**BLS wage at reporting cap:** Use $239,200/$115.00 as lower bound. Flag that burdened rate is a conservative floor.

**Standard rate travel locations:** Note when destination returns CONUS standard rate (flat, no seasonal variation).

**Partial-year periods:** Prorate hours, travel, and materials. Example: base year starts 3 months post-award = 9 months (1,410 hrs).

**Materials year-1 only items (T&M):** Hardware and initial setup costs often apply only to the base year. Do not escalate or repeat in option years unless the user specifies replacement cycles.

**User provides their own rates:** Use Workflow B (Rate Validation Only).

## What This Skill Does NOT Cover

Include as placeholder rows or methodology notes:
- **Airfare:** Use City Pair YCA fares when origin/destination known; otherwise TBD
- **Ground transportation:** Rental cars, mileage ($0.70/mile), taxi, rideshare
- **ODCs (LH):** Equipment, licenses, materials for LH contracts (user must provide)
- **Subcontractor costs:** Requires separate estimate or vendor input
- **Fee/profit analysis:** This skill estimates costs, not negotiation targets
- **OCONUS travel:** Per diem covers CONUS only; State Dept rates for OCONUS
- **FFP contracts:** Use IGCE Builder FFP for wrap rate buildup
- **Cost-reimbursement:** Use IGCE Builder CR for CPFF/CPAF/CPIF
- **Grant budgets:** Use Grant Budget Builder

## Quick Start Examples

**Simple LH:** "Build an IGCE for a Systems Analyst in DC, base plus 2 option years"
Claude will: map to SOC 15-1211, pull DC BLS wages, apply 1.8x/2.0x/2.2x burden, validate against CALC+, apply 2.5% escalation, produce 6-sheet xlsx.

**T&M:** "T&M IGCE for a 4-person dev team in DC, they'll need AWS hosting and JIRA licenses, base plus 3 OYs"
Claude will: run full labor sequence plus Step 5B for materials, collect specifics, produce 7-sheet xlsx with materials separate from burden.

**SOW-driven:** "Here's my SOW, build me an IGCE" [user pastes or uploads SOW]
Claude will: run Step 0 decomposition, validate, determine LH vs. T&M based on materials need, then run appropriate workflow.

**With travel:** "IGCE for a 5-person IT team in DC with monthly travel to San Antonio, base plus 4 OYs"
Claude will: ask for labor breakdown, run Steps 1-8 including City Pair lookup for DCA-SAT.

**Rate validation:** "Vendor proposes $165/hr for a Software Dev in DC. Reasonable?"
Claude will: Workflow B. Pull CALC+ distribution, position $165, optionally BLS context, produce validation summary.

**Multi-location:** "Price a 10-person help desk split between San Antonio and Houston, quarterly travel to DC"
Claude will: ask which approach (highest/weighted/separate), pull BLS for both metros, produce combined IGCE.

**Partial year:** "IGCE for a contract starting April 1, base year is 6 months, then 4 full OYs"
Claude will: prorate base to 6 months (940 hrs), full hours for OY1-4, note proration in methodology.

**Cleared environment:** "Use 2.4x burden for a cleared IT support contract in DC"
Claude will: set mid=2.4x, low=2.2x, high=2.6x, note cleared justification in methodology.
