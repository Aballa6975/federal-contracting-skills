# 1102tools Claude Skills

Claude Skills for federal contracting professionals. No subscriptions, no paywalls. Every skill in this collection uses a public federal API that's free to query.

Website: [1102tools.com](https://1102tools.com)

![Architecture diagram showing three parallel chains. Left: FAR-based contracts where SOW/PWS Builder feeds three IGCE Builders (FFP, LH/T&M, Cost-Reimbursement). Middle: Other Transactions where OT Project Description Builder feeds OT Cost Analysis (milestone-based pricing under 10 USC 4021/4022). Right: Grants and Cooperative Agreements where Grants Program Description Builder feeds Grants Budget Builder (2 CFR 200, SF-424A). All three chains pull from shared API data sources: BLS OEWS, GSA CALC+, and GSA Per Diem. Also in the collection: Market Research Builder, Vendor Intelligence, and Award Review.](docs/architecture.png?v=2026-04-15)

> **Before you build:** Not every acquisition capability should be an AI tool. Dozens of potential skills were evaluated and several were intentionally excluded. Some are planned and coming. Others will never be built because they cross the line from data assembly into professional judgment -- the kind of output that would not survive a protest, would not be adopted by the workforce, and would not be worth the time to develop. Read **[AI-BOUNDARIES.md](AI-BOUNDARIES.md)** for the full reasoning. It will save you development time and your users the backlash.

## Skills

### API Data Sources

| Skill | Key | Description |
|-------|-----|-------------|
| [USASpending API](skills/usaspending-api) | No key | Federal contract and award data. PIIDs, vendor awards, transaction histories, agency spending. |
| [USASpending Reference](skills/usaspending-api-reference) | No key | Filter tables, composite workflows, bulk download, vendor dedup. Install alongside main skill. |
| [GSA CALC+ Ceiling Rates](skills/gsa-calc-ceilingrates) | No key | Awarded NTE hourly rates from GSA MAS contracts (230K+ records). |
| [GSA CALC+ Reference](skills/gsa-calc-ceilingrates-reference) | No key | Aggregation schemas, IGCE benchmarking, price reasonableness. Install alongside main skill. |
| [BLS OEWS Wages](skills/bls-oews-api) | BLS key | Market wage data covering ~830 occupations across 530+ metro areas. |
| [BLS OEWS Reference](skills/bls-oews-api-reference) | No key | Query recipes, SOC code lookup, IGCE rate derivation. Install alongside main skill. |
| [GSA Per Diem Rates](skills/gsa-perdiem-rates) | api.data.gov | Federal travel per diem (lodging + M&IE) for all CONUS locations. |
| [GSA Per Diem Reference](skills/gsa-perdiem-rates-reference) | No key | Travel cost recipes, common rates table, IGCE travel formula. Install alongside main skill. |
| [Federal Register API](skills/federalregister-api) | No key | All Federal Register documents since 1994. Proposed rules, final rules, notices, executive orders. |
| [Federal Register Reference](skills/federalregister-api-reference) | No key | Composite workflows, FAR case history, regulatory timeline. Install alongside main skill. |
| [eCFR Lookup](skills/ecfr-api) | No key | Full current CFR text, updated daily. FAR/DFARS clauses, version comparison back to 2017. |
| [eCFR Reference](skills/ecfr-api-reference) | No key | Title 48 chapter map, common FAR sections, composite workflows. Install alongside main skill. |
| [Regulations.gov](skills/regulationsgov-api) | api.data.gov | Federal rulemaking dockets, proposed rules, public comments, docket histories. |
| [Regulations.gov Reference](skills/regulationsgov-api-reference) | No key | Comment tracker, FAR case history, regulatory monitor. Install alongside main skill. |
| [SAM.gov API](skills/sam-gov-api) | SAM.gov | Entity registration (UEI/CAGE), exclusion/debarment records, contract opportunities, contract awards (FPDS replacement). |
| [SAM.gov Reference](skills/sam-gov-api-reference) | No key | Entity and award schemas, business type codes, composite workflows. Install alongside main skill. |

### Orchestration Skills

| Skill | Key | Requires | Description |
|-------|-----|----------|-------------|
| [SOW/PWS Builder](skills/sow-pws-builder) | No key | -- | Structured scope decision tree producing contract-file-ready SOW or PWS. FAR 37.102(d) compliant: staffing handoff for the IGCE Builder is delivered as chat output, never embedded in the document body. |
| [IGCE Builder: FFP](skills/igce-builder-ffp) | No key* | BLS OEWS, GSA CALC+, GSA Per Diem | Firm-fixed-price IGCEs with layered wrap rate model (fringe, overhead, G&A, profit). |
| [IGCE Builder: LH/T&M](skills/igce-builder-lh-tm) | No key* | BLS OEWS, GSA CALC+, GSA Per Diem | Labor Hour and T&M IGCEs with burden multiplier pricing. |
| [IGCE Builder: Cost-Reimbursement](skills/igce-builder-cr) | No key* | BLS OEWS, GSA CALC+, GSA Per Diem | CPFF, CPAF, CPIF IGCEs with fee structure analysis and statutory fee caps. |
| [Market Research Builder](skills/market-research-builder) | No key* | USASpending API | FAR Part 10 market research report from USASpending data. |
| [Vendor Intelligence](skills/vendor-intelligence) | No key* | SAM.gov API, USASpending API | Pre-award vendor due diligence: entity profiles, exclusion checks, award history, FAR 9.104-1 mapping, 11 risk flags. |
| [Vendor Intelligence Reference](skills/vendor-intelligence-reference) | No key | -- | FAR 9 responsibility guide, risk flag definitions, business type codes. Install alongside main skill. |
| [Award Review](skills/award-review) | No key* | SAM.gov API, USASpending API | Post-award contract review: 12 factual observations covering entity registration, competition, subawards, and contract structure. |
| [Award Review Reference](skills/award-review-reference) | No key | -- | Observation definitions, thresholds, code tables, FFRDC/M&O exclusion list. Install alongside main skill. |

### Other Transaction (OT) Skills

| Skill | Key | Requires | Description |
|-------|-----|----------|-------------|
| [OT Project Description Builder](skills/ot-project-description-builder) | No key | -- | Milestone-based project descriptions for prototype OT agreements under 10 USC 4021/4022. Replaces the SOW/PWS for OTs: structures work around TRL progression phases and go/no-go gates instead of task/subtask CLINs. Handles NDC, small business, traditional (with cost sharing), and consortium-brokered agreements. Produces a .docx agreement attachment and a chat-only milestone handoff table for the OT Cost Analysis. |
| [OT Cost Analysis](skills/ot-cost-analysis) | No key* | BLS OEWS, GSA CALC+, GSA Per Diem | Should-cost estimates and price reasonableness analyses for OT agreements. Milestone-based pricing citing 10 USC 4021 instead of FAR 15.404. Handles cost-sharing math (10 USC 4022(d)), consortium management fees, fixed-price and cost-type milestone payments, and pre-solicitation budget planning. Produces a formula-driven .xlsx workbook with scenario analysis and a price reasonableness memo for the agreement file. |

### Grants and Cooperative Agreement Skills

| Skill | Key | Requires | Description |
|-------|-----|----------|-------------|
| [Grants Program Description Builder](skills/grants-program-description-builder) | No key | -- | Program Description section of a Notice of Funding Opportunity (NOFO) for federal grants and cooperative agreements under 2 CFR 200. The grants analog to the SOW/PWS for FAR contracts and the OT Project Description for OT agreements. Walks program officers through a 4-question Program Authority Intake (instrument type, program category, statutory authority, duration) and a 6-block scope decision tree. Produces a .docx that drops into the agency's NOFO template plus a chat-only program parameters handoff table for the Grants Budget Builder. |
| [Grants Budget Builder](skills/grants-budget-builder) | No key* | BLS OEWS, GSA Per Diem | Federal grant budget estimates aligned to 2 CFR 200 / SF-424A. Calculates personnel costs with percent-effort, fringe by appointment type, travel via Per Diem, and indirect costs via NICRA or de minimis rate. The cost-side sister skill to the Grants Program Description Builder. |

*Uses keys from other installed skills. No additional key needed.

## API Keys

Three free keys cover everything:

- **BLS**: Register at [data.bls.gov/registrationEngine](https://data.bls.gov/registrationEngine/) (500 queries/day)
- **api.data.gov**: Register at [api.data.gov/signup](https://api.data.gov/signup/) (1,000 req/hr; covers Per Diem + Regulations.gov)
- **SAM.gov**: Register at [SAM.gov](https://sam.gov/) (free account; API key in your profile; keys expire every 90 days)

Tell Claude to remember your keys and it will use them automatically.

## Install

1. Download and unzip a skill
2. In Claude: Customize > Skills > + > Create skill > Upload a skill > drag in each SKILL.md file individually
3. For skills with a reference companion, install both
4. Ask a question naturally. Claude reads the instructions and makes the API call.

## What's Not Here

If you're looking for a capability that doesn't exist in this collection, there are two possible reasons: it's planned, or it was evaluated and deliberately excluded. Proposal scoring, best value tradeoff analysis, responsibility determinations, negotiation strategy, OCI analysis, and several other capabilities were considered and rejected because they require warrant-level judgment that AI cannot replicate and the acquisition workforce will not accept. See **[AI-BOUNDARIES.md](AI-BOUNDARIES.md)** for the complete list and the reasoning behind each decision.

## License

MIT
