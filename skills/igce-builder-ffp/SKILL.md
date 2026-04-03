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

**Version 1.1** | April 2026

### Changelog
- **v1.1** (April 2026): Added Step 2B — BLS wage aging factor. Wages are now aged forward from BLS data vintage (May 2024) to contract start date using the escalation rate, closing the ~2-year data lag gap that was understating base year costs.
- **v1.0** (March 2026): Initial release.

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
User needs a complete FFP cost estimate. Execute Steps 1 through 8 in order.
Triggers: "FFP IGCE," "firm fixed price estimate," "wrap rate buildup," "cost buildup."

### Workflow A+: SOW/PWS-Driven FFP Build
User provides a Statement of Work or requirement description instead of pre-structured labor inputs. Execute Step 0 (Requirements Decomposition) first, validate with user, then Steps 1-8.
Triggers: "build an FFP IGCE from this SOW," "price this PWS as FFP," or when the user provides a block of requirement text rather than a labor category table.

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

Ask for everything in a single pass. Provide defaults where noted.

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Labor categories | Job titles or SOC codes | Software Developer, Project Manager |
| Performance location | City/state or metro area | Washington, DC |
| Staffing | Headcount per labor category | 2 developers, 1 PM |
| Hours per year | Productive hours per person (default: 1,880) | 1,880 |
| Period of performance | Base year + option years | Base + 2 OYs |

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
| FY for per diem | Current FY | FY2026 as of March 2026 |
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

## Constants Reference

| Constant | Value | Source |
|----------|-------|--------|
| Standard work year | 2,080 hours | 40 hrs x 52 weeks; converts annual wages to hourly |
| Default productive hours | 1,880 hours/year | 2,080 minus holidays and avg leave |
| BLS wage cap (annual) | $239,200 | May 2024 OEWS reporting ceiling |
| BLS wage cap (hourly) | $115.00 | May 2024 OEWS reporting ceiling |
| OEWS data year | 2024 | May 2024 estimates |
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

6. **User validation gate.** Confirm or adjust before proceeding to Step 1.

### Step 1: Map Labor Categories to SOC Codes

Map user job titles to Standard Occupational Classification codes. Common mappings:

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

**Use the BLS OEWS API skill.** For each labor category, query datatypes 04 (annual mean), 11-15 (10th through 90th percentiles) at the user's performance location.

Use metro-level prefix (OEUM) when available. Fall back to state (OEUS), then national (OEUN). Present the full wage distribution. Recommend the median (50th percentile) as default basis.

If BLS returns "-" with footnote code 5, the wage exceeds the $239,200 cap. Use the cap as a lower bound and flag in the narrative.

### Step 2B: Age BLS Wages to Contract Start Date

BLS OEWS data has a ~2-year lag (May 2024 estimates released April 2025). If the contract Period of Performance starts after the data reference period, the base wages must be aged forward to avoid understating costs.

```
months_gap = months between BLS data vintage (May 2024) and contract PoP start date
aging_factor = (1 + escalation_rate) ^ (months_gap / 12)
aged_annual_wage = annual_median * aging_factor
```

Example: BLS data from May 2024, contract starts October 2026 = 29 months gap. At 2.5% escalation: aging_factor = 1.025^(29/12) = ~1.061. A $100,000 BLS median becomes $106,100 before wrap rate buildup.

Use the aged wage as the basis for all subsequent calculations. Document the aging adjustment in the Methodology sheet: "BLS OEWS May 2024 wages aged forward [X] months to [contract start] at [escalation rate]%/yr to account for data lag."

If the user does not provide a contract start date, ask for one. If unknown, default to 6 months from today and note the assumption.

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

This produces a wider range than T&M scenarios, which is appropriate given FFP's structural cost uncertainty.

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

Compare mid-scenario FFP burdened rate to CALC+ median. Flag divergence >25%. Divergence is a data point requiring explanation, not an error. FFP rates running higher than CALC+ medians is expected since CALC+ reflects T&M/LH ceiling rates and FFP embeds cost risk.

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

Edge case for 1-night trips: both days are partial, so `mie_per_trip = mie_rate * 0.75 * 2`.

Use max monthly lodging rate as conservative ceiling if specific months not provided.

### Step 6: Handle Multi-Location Weighting

**Option A (default, conservative):** Use highest median across locations per category.
**Option B (weighted):** `weighted_wage = (wage_A * pct_A) + (wage_B * pct_B)` if user provides split.
**Option C (separate lines):** Dedicated staff per location get separate rows.

Ask the user which approach if multiple locations mentioned. Default to Option A.

### Step 7: Calculate Fixed Prices and Apply Escalation

**Two FFP pricing structures (ask user which applies):**

**Structure A: FFP by Period (default for services)**
```
period_labor = sum(fully_burdened_rate * productive_hours * headcount) per category
period_travel = travel costs from Step 5
period_fixed_price = period_labor + period_travel + ODCs
```

**Structure B: FFP by Deliverable/CLIN**
```
deliverable_price = sum(burdened_rate * est_hours_per_category) + allocated_travel + ODCs
```

**Partial-year proration:**
```
prorated_hours = productive_hours * (months_in_period / 12)
prorated_travel = annual_travel * (months_in_period / 12)
```

**Escalation:** `year_N_cost = base_year_cost * (1 + escalation_rate) ^ N`

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

**Sheet 1: IGCE Summary.** Labor categories as rows, periods as columns. Rate/Hr shows fully burdened FFP rate. Extra column for implied multiplier. Travel rows below labor. Placeholder rows for Airfare, Ground Transportation, ODCs with "TBD." Grand total with SUM formulas.

**Assumption cell layout (Sheet 1, rows 1-9):**
```
A1: "IGCE Assumptions (FFP)"         (bold, merged A1:B1)
A2: "Fringe Rate"                    B2: 0.32     (blue font, percentage)
A3: "Overhead Rate"                  B3: 0.80     (blue font, percentage)
A4: "G&A Rate"                       B4: 0.12     (blue font, percentage)
A5: "Profit Rate"                    B5: 0.10     (blue font, percentage)
A6: "Escalation Rate"                B6: 0.025    (blue font, percentage)
A7: "Productive Hours/Year"          B7: 1880     (blue font)
A8: "Base Year Months"               B8: 12       (blue font)
A9: (blank row separator)
A10: header row for data table
```

All labor formulas reference these cells. Changing any input recalculates the entire workbook.

**Sheet 2: Cost Buildup.** One block per labor category showing the layered buildup:
```
Row 1: "Cost Buildup: [Labor Category]"                        (bold header)
Row 2: A="BLS Base Wage (Annual)"     B=[annual median]        (from BLS)
Row 3: A="Direct Labor Rate (Hourly)" B==B2/2080               (formula)
Row 5: A="Fringe Rate"                B=0.32                   (blue font, input)
Row 6: A="Fringe Amount"              B==B3*B5                  (formula)
Row 7: A="Labor + Fringe"             B==B3+B6                  (formula)
Row 8: A="Overhead Rate"              B=0.80                   (blue font, input)
Row 9: A="Overhead Amount"            B==B7*B8                  (formula)
Row 10: A="Subtotal"                  B==B7+B9                  (formula)
Row 11: A="G&A Rate"                  B=0.12                   (blue font, input)
Row 12: A="G&A Amount"                B==B10*B11                (formula)
Row 13: A="Total Cost"                B==B10+B12                (formula)
Row 14: A="Profit Rate"               B=0.10                   (blue font, input)
Row 15: A="Profit Amount"             B==B13*B14                (formula)
Row 16: A="Fully Burdened Rate"       B==B13+B15                (formula, bold)
Row 17: A="Implied Multiplier"        B==B16/B3                 (formula, 0.00"x")
```

Rate cells (B5, B8, B11, B14) are blue font, user-adjustable. Changing any rate recalculates through to Sheet 1.

**Sheet 3: Scenario Analysis.** Three columns (low/mid/high), each using its own fringe/overhead/G&A/profit rates. Display component rates at top of each column. Travel identical across scenarios. Summary row: "Range: $X (low) to $Y (high), Mid estimate: $Z."

**Sheet 4: Rate Validation.** BLS burdened rate (mid scenario) vs. CALC+ 25th/50th/75th percentiles, min/max range, divergence percentage (formula), Status column.

**Sheet 5: Travel Detail.** Formula-driven per destination block:
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

**Sheet 6: Methodology.** FFP-specific narrative for the contract file. Include: wrap rate buildup with each cost pool explained, FAR 15.404-1(a), FAR 15.404-4, FAR 16.202, implied multiplier comparison to typical T&M burden range, note that FFP rates exceed T&M because contractor absorbs cost risk, data sources with dates, escalation basis, travel methodology, exclusions, NAICS/PSC if provided.

**Sheet 7: Raw Data.** All API query parameters and responses: BLS series IDs, CALC+ keywords and record counts, per diem query details, City Pair fares if retrieved.

**Formatting standards:**
- Blue font (RGB 0,0,255) for all user-adjustable inputs and assumptions
- Black font for all formula cells
- Currency: $#,##0 with negatives in parentheses
- Percentage: 0.0%
- Bold headers with light gray fill
- Freeze panes below assumptions block on Sheet 1 (below row 9)
- Auto-size column widths
- Burden/multiplier display format: `0.00"x"`

When base year is partial, prorate: `=burdened_rate*$B$7*(B8/12)*headcount`. Travel prorates the same way. Full option years ignore B8.

Never output as .md or HTML unless explicitly requested.

## Edge Cases

**Labor categories not in BLS:** Find closest SOC code(s), query all candidates, present range, let user select, document mapping rationale.

**No CALC+ results:** Try broader keywords ("Information Security" instead of "Information Security Analyst"). If still nothing, note CALC+ unavailable; estimate relies on BLS alone. Mark Status as "No CALC+ data."

**BLS wage at reporting cap:** Use $239,200/$115.00 as lower bound. Flag in narrative that burdened rate is a conservative floor.

**Standard rate travel locations:** Note when destination returns CONUS standard rate (flat, no seasonal variation).

**Partial-year periods:** Prorate hours and travel. Common: base year starts 3 months post-award = 9 months (1,410 hrs). Note proration in methodology.

**Implied multiplier sanity check:** If the mid-scenario implied multiplier falls outside 2.2x-3.5x, flag for user review. Below 2.2x suggests unrealistically low overhead assumptions. Above 3.5x suggests SCIF/OCONUS/niche conditions that should be documented.

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

## Quick Start Examples

**Basic FFP:** "Build an FFP IGCE for a 3-person dev team in DC, base plus 2 OYs"
Claude will: map to SOC codes, pull DC BLS wages, build layered wrap rates at low/mid/high, validate against CALC+, apply 2.5% escalation, produce 7-sheet xlsx.

**SOW-driven:** "Here's my PWS, I need an FFP cost estimate" [user uploads PWS]
Claude will: run Step 0 decomposition, validate with user, then full Workflow A with FFP buildup.

**With travel:** "FFP IGCE for 5-person IT team in DC, monthly travel to San Antonio, base plus 4 OYs"
Claude will: ask for labor breakdown, run Steps 1-8 including City Pair lookup for DCA-SAT.

**Rate validation:** "Vendor proposes $185/hr for a Software Dev, FFP contract. Reasonable?"
Claude will: Workflow B. Pull CALC+ distribution, run BLS wrap rate buildup for context, position $185 within both, produce validation summary.

**Multi-location:** "FFP IGCE for 10-person help desk split between San Antonio and Houston, quarterly travel to DC"
Claude will: ask which multi-location approach, pull BLS for both metros, calculate travel for DC, produce combined workbook with scenario analysis.

**Custom rates:** "Use 35% fringe, 95% overhead, 15% G&A, 12% profit for a cleared environment"
Claude will: apply custom rates as mid scenario, set low = mid minus offset, high = mid plus offset, note cleared environment justification in methodology.
