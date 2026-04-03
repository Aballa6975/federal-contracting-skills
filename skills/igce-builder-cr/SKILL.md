---
name: igce-builder-cr
description: >
  Build IGCEs for Cost-Reimbursement (CPFF/CPAF/CPIF) federal contracts
  using layered cost pool buildup with fee structure analysis. Orchestrates
  BLS OEWS, GSA CALC+, and GSA Per Diem skills. Supports SOW/PWS
  decomposition into labor categories and rate validation against CALC+
  market data. Trigger for: cost reimbursement IGCE, CPFF estimate,
  CPAF estimate, CPIF estimate, cost-plus estimate, BAA cost estimate,
  CR IGCE, cost reimbursement cost estimate, fixed fee estimate,
  award fee estimate, incentive fee estimate, fee structure analysis.
  Also trigger for cost pool buildup, fee rate analysis, share ratio,
  or CR scenario analysis. Do NOT use for FFP contracts or wrap rate
  buildup (use IGCE Builder FFP). Do NOT use for Labor Hour or T&M
  (use IGCE Builder LH/T&M). Do NOT use for grant budgets under
  2 CFR 200 (use Grant Budget Builder). Requires BLS OEWS API, GSA
  CALC+ Ceiling Rates API, and GSA Per Diem Rates API skills.
---

# IGCE Builder: Cost-Reimbursement (CPFF / CPAF / CPIF)

**Version 1.0** | March 2026

## Overview

This skill produces Independent Government Cost Estimates for cost-reimbursement contracts. CR contracts reimburse the contractor for allowable costs incurred plus a fee. The cost buildup is structurally similar to FFP (layered cost pools: fringe, overhead, G&A), but instead of profit-as-markup, CR contracts use a negotiated fee that varies by subtype. The IGCE estimates what those allowable costs should be and what fee structure is appropriate.

CR contracts are common outcomes from BAAs (FAR 35.016), R&D contracts, and complex requirements where the government assumes cost risk but controls it through auditable cost pools and negotiated fee structures.

**Required L1 skills (must be installed):**
1. **BLS OEWS API** -- market wage data by occupation and geography
2. **GSA CALC+ Ceiling Rates API** -- awarded GSA MAS schedule hourly rates
3. **GSA Per Diem Rates API** -- federal travel lodging and M&IE rates

**Required API keys (must be in user memory):**
- BLS API key (v2) for BLS OEWS
- api.data.gov key for GSA Per Diem
- CALC+ requires no key

If a key is missing, prompt the user to register: BLS at https://data.bls.gov/registrationEngine/, api.data.gov at https://api.data.gov/signup/

**Regulatory basis:** FAR 15.402 (cost/pricing data). FAR 15.404-1(a) (cost analysis). FAR 15.404-4 (profit/fee analysis). FAR 16.301 through 16.307 (cost-reimbursement contracts). 10 USC 3322(a) (statutory fee caps).

## Workflow Selection

### Workflow A: Full CR IGCE Build (Default)
User needs a complete cost-reimbursement estimate. Execute Steps 1 through 8.
Triggers: "cost reimbursement IGCE," "CPFF estimate," "CPAF estimate," "CPIF estimate," "cost-plus estimate," "BAA cost estimate."

### Workflow A+: SOW/PWS-Driven CR Build
User provides a requirement document instead of structured labor inputs. Execute Step 0 first, validate, then Steps 1-8.
Triggers: "build a CR IGCE from this SOW," "price this BAA requirement," or when user provides requirement text and specifies cost-reimbursement.

Detection: If the user mentions a BAA and does not specify contract type, suggest CR as the most likely fit and confirm before proceeding.

### Workflow B: Rate Validation Only
User has proposed rates and wants to check reasonableness.
Triggers: "is this CR rate reasonable," "validate these cost pool rates," "check this cost proposal."

**Workflow B steps:**
1. Collect the vendor's proposed labor categories and fully burdened rates (or cost pool breakdown).
2. For each category, query CALC+ per Step 4.
3. Position each rate within CALC+ distribution: below 25th (aggressive), 25th-75th (competitive), above 75th (premium), above 90th (outlier).
4. Optionally run Steps 1-3 to show where the rate falls relative to BLS wages with cost pool buildup.
5. Produce Rate Validation sheet and narrative. No full workbook unless requested.

## Information to Collect

Ask for everything in a single pass. Provide defaults where noted.

### Required Inputs

| Input | Description | Example |
|-------|-------------|---------|
| Labor categories | Job titles or SOC codes | Research Scientist, Data Analyst, PM |
| Performance location | City/state or metro area | Bethesda, MD |
| Staffing | Headcount per labor category | 3 researchers, 1 analyst, 1 PM |
| Hours per year | Productive hours per person (default: 1,880) | 1,880 |
| Period of performance | Base year + option years | Base + 2 OYs |
| Fee type | CPFF, CPAF, or CPIF | CPFF |

### Optional Inputs (Defaults Applied If Not Provided)

| Input | Default | Notes |
|-------|---------|-------|
| Fringe rate | 32% | FICA + health + retirement + PTO + workers' comp |
| Overhead rate | 80% | Applied to labor + fringe |
| G&A rate | 12% | Applied to subtotal |
| Fee percentage (CPFF) | 8% | Fixed fee as % of estimated cost |
| Base fee (CPAF) | 3% | Minimum fee regardless of performance |
| Award fee pool (CPAF) | 7% | Max additional fee based on evaluation |
| Target fee (CPIF) | 8% | Fee at target cost |
| Share ratio (CPIF) | 80/20 gov/contractor | Applied to over/underruns |
| Min fee (CPIF) | 3% | Floor on fee |
| Max fee (CPIF) | 12% | Ceiling on fee |
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

### Cost Pool Rate Guidance

Provide this when the user is unsure:

| Component | Low | Mid | High | Notes |
|-----------|-----|-----|------|-------|
| Fringe | 25% | 32% | 40% | Higher for generous benefits, union shops |
| Overhead | 60% | 80% | 120% | Higher for SCIF/cleared, large firms, R&D labs |
| G&A | 8% | 12% | 18% | Higher for large corporate structures |

### Fee Structure Reference

| Type | FAR Ref | Mechanism | Default | When Used |
|------|---------|-----------|---------|-----------|
| CPFF | 16.306 | Fixed fee set at award, unchanged by actual costs | 8% | Most common CR. R&D, studies, analysis. |
| CPAF | 16.305 | Base fee (0-3%) plus award pool (5-10%) earned on performance | 3% base + 7% pool | Performance-driven with periodic evaluation |
| CPIF | 16.304 | Target fee adjusted by share ratio; bounded by min/max | 8% target, 80/20 share | Complex work with cost uncertainty but measurable efficiency |

**Statutory fee caps:** R&D contracts: 15% of estimated cost (10 USC 3322(a)). Non-R&D: no statutory cap but 10% is the practical ceiling per agency policy.

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

Converts an unstructured SOW/PWS into structured pricing inputs.

**Process:**
1. **Sufficiency check.** Scan for six priceable elements: labor categories, staffing levels, performance location, period of performance, deliverables, and travel. Flag anything missing. Hard stop if performance location is absent. If 3+ elements missing and document under 500 words, ask user whether to proceed with assumptions or get clarification.

2. **Task decomposition.** Parse into discrete task areas with description, skill discipline, complexity, and recurring vs. finite classification.

3. **Labor category mapping.** Map tasks to SOC codes using Step 1 heuristics. When a task spans disciplines, map to multiple categories.

4. **Staffing estimation.** Estimate FTEs per category based on scope indicators. Present as ranges when ambiguous.

5. **Present decomposition table** for user validation.

6. **User validation gate.** Confirm labor mix. Also confirm fee type: "Cost-reimbursement contracts require a fee structure. Based on [rationale], I recommend CPFF. Should I proceed with CPFF, or do you need CPAF or CPIF?"

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
| Research Scientist | 19-1099 | Life Scientists, All Other (or domain-specific) |
| Statistician | 15-2041 | Statisticians |
| Epidemiologist | 19-1041 | Epidemiologists |

When mapping is ambiguous, query multiple SOC codes and present the range.

### Step 2: Pull BLS Wage Data

**Use the BLS OEWS API skill.** For each labor category, query datatypes 04 (annual mean), 11-15 (10th through 90th percentiles) at the performance location.

Use metro-level prefix (OEUM) when available. Fall back to state (OEUS), then national (OEUN). Present the full wage distribution. Recommend the median as default basis.

If BLS returns "-" with footnote code 5, the wage exceeds the $239,200 cap. Use the cap as a lower bound and flag in the narrative.

### Step 2B: Age BLS Wages to Contract Start Date

BLS OEWS data has a ~2-year lag (May 2024 estimates released April 2025). If the contract Period of Performance starts after the data reference period, the base wages must be aged forward to avoid understating costs.

```
months_gap = months between BLS data vintage (May 2024) and contract PoP start date
aging_factor = (1 + escalation_rate) ^ (months_gap / 12)
aged_annual_wage = annual_median * aging_factor
```

Example: BLS data from May 2024, contract starts October 2026 = 29 months gap. At 2.5% escalation: aging_factor = 1.025^(29/12) = ~1.061. A $100,000 BLS median becomes $106,100 before cost pool buildup.

Use the aged wage as the basis for all subsequent calculations. Document the aging adjustment in the Methodology sheet: "BLS OEWS May 2024 wages aged forward [X] months to [contract start] at [escalation rate]%/yr to account for data lag."

If the user does not provide a contract start date, ask for one. If unknown, default to 6 months from today and note the assumption.

The escalation applied in Step 7 across option years starts AFTER this aging adjustment. Step 2B ages the base wage to the contract start; Step 7 escalates from that adjusted base across the period of performance. These are not double-counted.

### Step 3: Cost Pool Buildup

Build the estimated cost layer by layer for each labor category:

```
1. Direct Labor Rate    = aged_annual_wage / 2080
2. Fringe               = Direct Labor * fringe_rate
3. Labor + Fringe       = Direct Labor + Fringe
4. Overhead             = Labor_Fringe * overhead_rate
5. Subtotal             = Labor_Fringe + Overhead
6. G&A                  = Subtotal * ga_rate
7. Total Estimated Cost = Subtotal + G&A
8. Fee                  = see fee calculation by type below
9. Total Estimated Price = Total_Estimated_Cost + Fee
```

**CPFF fee:**
```
fixed_fee = total_estimated_cost * cpff_fee_rate
total_price = total_estimated_cost + fixed_fee
```
Fee is fixed at award. Does not change with actual costs.

**CPAF fee:**
```
base_fee = total_estimated_cost * cpaf_base_rate
award_fee_pool = total_estimated_cost * cpaf_pool_rate
estimated_fee = base_fee + (award_fee_pool * 0.85)   # assume 85% earned
total_price = total_estimated_cost + estimated_fee
```
For IGCE purposes, assume 85% of award fee pool earned (common convention). Note in methodology.

**CPIF fee:**
```
target_cost = total_estimated_cost
target_fee = target_cost * cpif_target_rate

# At target cost
fee_at_target = target_fee

# 10% overrun scenario
overrun_cost = target_cost * 1.10
fee_at_overrun = target_fee - (overrun_cost - target_cost) * contractor_share_over
fee_at_overrun = max(fee_at_overrun, target_cost * cpif_min_fee)

# 10% underrun scenario
underrun_cost = target_cost * 0.90
fee_at_underrun = target_fee + (target_cost - underrun_cost) * contractor_share_under
fee_at_underrun = min(fee_at_underrun, target_cost * cpif_max_fee)
```

**Implied multiplier:** `implied_multiplier = total_estimated_price / direct_labor_rate`. Display for comparison to typical T&M burdens and FFP wrap rates.

**Three-scenario approach:** Vary each cost pool component:

| Component | Low | Mid | High |
|-----------|-----|-----|------|
| Fringe | 25% | 32% | 40% |
| Overhead | 60% | 80% | 120% |
| G&A | 8% | 12% | 18% |

Fee is calculated on each scenario's total cost. For CPIF, this produces a 3x3 matrix: 3 cost scenarios x 3 fee outcomes (underrun/target/overrun).

### Step 4: Cross-Reference Against CALC+

**Use the GSA CALC+ Ceiling Rates API skill.** For each labor category, search with `page_size=0`.

**CRITICAL JSON paths:**
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

Compare mid-scenario burdened rate (cost + fee) to CALC+ median. Flag divergence >25%. CR burdened rates may diverge more from CALC+ than T&M since CALC+ reflects MAS ceiling rates (T&M/LH pricing), not cost-reimbursement structures. Note this context in the validation narrative.

### Step 5: Pull Per Diem Rates (If Travel Required)

**Use the GSA Per Diem Rates API skill.** Query monthly lodging and M&IE for each destination.

**City Pair airfare (optional):** When origin and destination known, look up YCA fares at cpsearch.fas.gsa.gov. Skip if origin unknown, OCONUS, local travel, or user provides own airfare.

**Per-trip cost:**
```
lodging_per_trip = nightly_rate * nights
travel_days = nights + 1
full_day_mie = mie_rate * max(0, travel_days - 2)
partial_day_mie = mie_rate * 0.75 * 2
mie_per_trip = full_day_mie + partial_day_mie
trip_total = lodging_per_trip + mie_per_trip
annual_travel = trip_total * trips_per_year * travelers
```

Edge case for 1-night trips: both days partial, `mie_per_trip = mie_rate * 0.75 * 2`.

### Step 6: Handle Multi-Location Weighting

**Option A (default):** Use highest median across locations per category.
**Option B (weighted):** `weighted_wage = (wage_A * pct_A) + (wage_B * pct_B)`.
**Option C (separate lines):** Dedicated staff per location get separate rows.

### Step 7: Calculate Estimated Costs by Period and Apply Escalation

**Per-period calculation:**
```
period_labor_cost = sum(burdened_rate * productive_hours * headcount) per category
period_travel = travel costs from Step 5
period_total_cost = period_labor_cost + period_travel
period_fee = period_total_cost * fee_rate (varies by CR subtype)
period_total_price = period_total_cost + period_fee
```

**Partial-year proration:**
```
prorated_hours = productive_hours * (months_in_period / 12)
prorated_travel = annual_travel * (months_in_period / 12)
```

**Escalation:** `year_N_cost = base_year_cost * (1 + escalation_rate) ^ N`

**Three-scenario math:** Vary cost pool components (fringe/overhead/G&A) at low/mid/high. Fee calculated on each scenario's total cost.

For CPIF, each cost scenario shows three fee outcomes (underrun/target/overrun), producing a 3x3 matrix:
```
              | Low Cost  | Mid Cost  | High Cost
Underrun Fee  | $X        | $X        | $X
Target Fee    | $X        | $X        | $X
Overrun Fee   | $X        | $X        | $X
```

Travel is identical across all scenarios.

### Step 8: Produce the CR IGCE Workbook

Generate a multi-sheet .xlsx workbook using openpyxl. Use Excel formulas for all calculations. Run recalc script (`python /mnt/skills/public/xlsx/scripts/recalc.py <file>`) before presenting.

**Workbook structure (7 sheets):**

**Sheet 1: IGCE Summary.** Labor categories as rows, periods as columns. Shows Total Estimated Cost, Fee (labeled by type: "Fixed Fee," "Estimated Award Fee," or "Target Fee"), and Total Estimated Price. Travel rows below labor. Placeholder rows for Airfare, Ground Transportation, ODCs. Grand total with SUM formulas.

**Assumption cell layout (Sheet 1, rows 1-10):**
```
A1: "IGCE Assumptions (Cost-Reimbursement)"   (bold, merged A1:B1)
A2: "Fringe Rate"                              B2: 0.32     (blue font, percentage)
A3: "Overhead Rate"                            B3: 0.80     (blue font, percentage)
A4: "G&A Rate"                                 B4: 0.12     (blue font, percentage)
A5: "Fee Type"                                 B5: "CPFF"   (blue font)
A6: "Fee Rate"                                 B6: 0.08     (blue font, percentage)
A7: "Escalation Rate"                          B7: 0.025    (blue font, percentage)
A8: "Productive Hours/Year"                    B8: 1880     (blue font)
A9: "Base Year Months"                         B9: 12       (blue font)
A10: (blank row separator)
A11: header row for data table
```

For CPAF: replace A6/B6 with "Base Fee Rate" and add A6a: "Award Fee Pool Rate" B6a: 0.07, A6b: "Assumed Earned %" B6b: 0.85.
For CPIF: replace A6/B6 with "Target Fee Rate" and add rows for Share Ratio (Over), Share Ratio (Under), Min Fee, Max Fee.

**Sheet 2: Cost Buildup.** One block per labor category showing direct labor through G&A, plus a fee analysis block below:

```
Cost Buildup: [Labor Category]
Row 2: A="BLS Base Wage (Annual)"     B=[annual median]
Row 3: A="Direct Labor Rate (Hourly)" B==B2/2080               (formula)
Row 5: A="Fringe Rate"                B=0.32                   (blue font)
Row 6: A="Fringe Amount"              B==B3*B5                  (formula)
Row 7: A="Labor + Fringe"             B==B3+B6                  (formula)
Row 8: A="Overhead Rate"              B=0.80                   (blue font)
Row 9: A="Overhead Amount"            B==B7*B8                  (formula)
Row 10: A="Subtotal"                  B==B7+B9                  (formula)
Row 11: A="G&A Rate"                  B=0.12                   (blue font)
Row 12: A="G&A Amount"                B==B10*B11                (formula)
Row 13: A="Total Estimated Cost"      B==B10+B12                (formula)

Fee Analysis:
Row 15: A="Fee Type"                  B="CPFF"                 (blue font)
Row 16: A="Fee Rate"                  B=0.08                   (blue font)
Row 17: A="Fee Amount"                B==B13*B16                (formula)
Row 18: A="Total Estimated Price"     B==B13+B17                (formula, bold)
Row 19: A="Implied Multiplier"        B==B18/B3                 (formula, 0.00"x")
```

For CPAF: rows for base fee, award pool, assumed earned %, calculated fee.
For CPIF: rows for target fee, overrun/underrun scenarios with share ratio, min/max bounds.

**Sheet 3: Scenario Analysis.** Three cost columns (low/mid/high) with fee calculated on each. Display component rates at top. For CPIF: expand to 3x3 matrix (cost scenarios x fee outcomes). Summary row with range.

**Sheet 4: Rate Validation.** BLS burdened rate (mid) vs. CALC+ 25th/50th/75th, min/max, divergence, Status.

**Sheet 5: Travel Detail.** Formula-driven per destination:
```
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

**Sheet 6: Methodology.** CR-specific narrative. Include: cost pool buildup with each pool explained, fee type selection rationale and FAR reference, fee-specific notes (CPFF: fee fixed regardless of cost outcome; CPAF: assumed earned % and evaluation basis; CPIF: target cost/fee, share ratios, min/max), statutory fee caps (10 USC 3322(a) for R&D), FAR 16.301-16.307 references, data sources with dates, escalation basis, travel methodology, exclusions, NAICS/PSC if provided.

**Sheet 7: Raw Data.** All API query parameters and responses.

**Formatting standards:**
- Blue font (RGB 0,0,255) for all user-adjustable inputs
- Black font for formula cells
- Currency: $#,##0 with negatives in parentheses
- Percentage: 0.0%
- Bold headers with light gray fill
- Freeze panes below assumptions block (below row 10)
- Auto-size column widths
- Multiplier display: `0.00"x"`

When base year is partial, prorate labor and travel using $B$9. Full option years ignore $B$9.

Never output as .md or HTML unless explicitly requested.

## Edge Cases

**Labor categories not in BLS:** Find closest SOC code(s), query candidates, present range, document rationale.

**No CALC+ results:** Try broader keywords. If nothing, note unavailable; rely on BLS alone.

**BLS wage at reporting cap:** Use $239,200/$115.00 as lower bound. Flag conservative floor.

**BAA without contract type specified:** Suggest CPFF as default (most common for R&D BAAs under FAR 35.016). Confirm with user.

**Fee exceeds statutory cap:** If calculated fee exceeds 15% for R&D or 10% practical ceiling, flag and reduce to cap. Note in methodology.

**CPIF share ratio edge cases:** If fee calculation hits min or max bound, note that the share ratio no longer applies in that range. The contractor's fee is capped.

**Partial-year periods:** Prorate hours and travel. Fee calculated on prorated cost.

## What This Skill Does NOT Cover

Include as placeholder rows or methodology notes:
- **Airfare:** Use City Pair YCA fares when origin/destination known; otherwise TBD
- **Ground transportation:** Rental cars, mileage ($0.70/mile), taxi, rideshare
- **ODCs:** Equipment, licenses, materials (user must provide)
- **Subcontractor costs:** Requires separate estimate or vendor input
- **DCAA audit rates:** Actual indirect rates from contractor disclosure statements
- **OCONUS travel:** Per diem covers CONUS only; State Dept rates for OCONUS
- **FFP contracts:** Use IGCE Builder FFP
- **T&M/LH contracts:** Use IGCE Builder LH/T&M
- **Grant budgets:** Use Grant Budget Builder

## Quick Start Examples

**CPFF:** "CPFF IGCE for an R&D contract, 3 researchers in Bethesda, base plus 2 OYs"
Claude will: map to SOC codes, pull Bethesda BLS wages, build cost pools, calculate 8% fixed fee, validate against CALC+, produce 7-sheet xlsx with fee analysis.

**BAA:** "We're issuing a BAA for AI research, need a cost estimate for evaluation"
Claude will: confirm CR (suggest CPFF as default for BAAs), ask for labor details, run full workflow. Note FAR 35.016 in methodology.

**CPAF:** "CPAF IGCE for a managed services contract, 10-person team in DC"
Claude will: build cost pools, calculate base fee (3%) + award pool (7%) at 85% assumed earned, produce scenario analysis showing fee range.

**CPIF:** "CPIF IGCE with 80/20 share ratio for systems integration in DC"
Claude will: build cost pools, produce 3x3 matrix (low/mid/high cost x underrun/target/overrun fee), show fee bounded by min (3%) and max (12%).

**SOW-driven:** "Here's my SOW for an R&D effort, build me a CPFF estimate" [user uploads]
Claude will: run Step 0 decomposition, validate, confirm CPFF, then full workflow.

**Rate validation:** "Contractor proposes $195/hr on a CPFF contract. Reasonable?"
Claude will: Workflow B. Pull CALC+, run BLS cost pool buildup, position $195, produce validation.
