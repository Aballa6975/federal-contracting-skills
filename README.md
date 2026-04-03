# 1102tools Claude Skills

Free Claude Skills for federal contracting professionals and government contractors.

All skills are free. All APIs are free.

Website: [1102tools.com](https://1102tools.com)

## Skills

### API Data Sources

| Skill | Version | Key | Description |
|-------|---------|-----|-------------|
| [USASpending API](skills/usaspending-api) | v1.6 | No key | Federal contract and award data. PIIDs, vendor awards, transaction histories, agency spending. |
| [USASpending Reference](skills/usaspending-api-reference) | v1.6 | No key | Filter tables, composite workflows, bulk download, vendor dedup. Install alongside main skill. |
| [GSA CALC+ Ceiling Rates](skills/gsa-calc-ceilingrates) | v1.3 | No key | Awarded NTE hourly rates from GSA MAS contracts (230K+ records). |
| [GSA CALC+ Reference](skills/gsa-calc-ceilingrates-reference) | v1.3 | No key | Aggregation schemas, IGCE benchmarking, price reasonableness. Install alongside main skill. |
| [BLS OEWS Wages](skills/bls-oews-api) | v1.3 | BLS key | Market wage data covering ~830 occupations across 530+ metro areas. |
| [BLS OEWS Reference](skills/bls-oews-api-reference) | v1.3 | No key | Query recipes, SOC code lookup, IGCE rate derivation. Install alongside main skill. |
| [GSA Per Diem Rates](skills/gsa-perdiem-rates) | v1.3 | api.data.gov | Federal travel per diem (lodging + M&IE) for all CONUS locations. |
| [GSA Per Diem Reference](skills/gsa-perdiem-rates-reference) | v1.3 | No key | Travel cost recipes, common rates table, IGCE travel formula. Install alongside main skill. |
| [Federal Register API](skills/federalregister-api) | v1.3 | No key | All Federal Register documents since 1994. Proposed rules, final rules, notices, executive orders. |
| [Federal Register Reference](skills/federalregister-api-reference) | v1.3 | No key | Composite workflows, FAR case history, regulatory timeline. Install alongside main skill. |
| [eCFR Lookup](skills/ecfr-api) | v1.2 | No key | Full current CFR text, updated daily. FAR/DFARS clauses, version comparison back to 2017. |
| [eCFR Reference](skills/ecfr-api-reference) | v1.2 | No key | Title 48 chapter map, common FAR sections, composite workflows. Install alongside main skill. |
| [Regulations.gov](skills/regulationsgov-api) | v1.3 | api.data.gov | Federal rulemaking dockets, proposed rules, public comments, docket histories. |
| [Regulations.gov Reference](skills/regulationsgov-api-reference) | v1.3 | No key | Comment tracker, FAR case history, regulatory monitor. Install alongside main skill. |

### Orchestration Skills

| Skill | Version | Key | Description |
|-------|---------|-----|-------------|
| [SOW/PWS Builder](skills/sow-pws-builder) | v1.0 | No key | Structured scope decision tree producing contract-file-ready SOW or PWS with staffing table. |
| [IGCE Builder: FFP](skills/igce-builder-ffp) | v1.1 | No key* | Firm-fixed-price IGCEs with layered wrap rate model (fringe, overhead, G&A, profit). |
| [IGCE Builder: LH/T&M](skills/igce-builder-lh-tm) | v1.1 | No key* | Labor Hour and T&M IGCEs with burden multiplier pricing. |
| [IGCE Builder: Cost-Reimbursement](skills/igce-builder-cr) | v1.1 | No key* | CPFF, CPAF, CPIF IGCEs with fee structure analysis and statutory fee caps. |
| [Market Research Builder](skills/market-research-builder) | v1.3 | No key* | FAR Part 10 market research report from USASpending data. |
| [Grants Builder](skills/grants-builder) | v1.0 | No key* | Federal grant budgets aligned to 2 CFR 200 / SF-424A. |

*Uses keys from other installed skills. No additional key needed.

## API Keys

Two free keys cover everything:

- **BLS**: Register at [data.bls.gov/registrationEngine](https://data.bls.gov/registrationEngine/) (500 queries/day)
- **api.data.gov**: Register at [api.data.gov/signup](https://api.data.gov/signup/) (1,000 req/hr; covers Per Diem + Regulations.gov)

Tell Claude to remember your keys and it will use them automatically.

## Install

1. Download and unzip a skill
2. In Claude: Customize > Skills > + > Create skill > Upload a skill > drag in each SKILL.md file individually
3. For skills with a reference companion, install both
4. Ask a question naturally. Claude reads the instructions and makes the API call.

## License

MIT
