---
name: federalregister-api-reference
description: >
  Reference file for the Federal Register API skill. Do not trigger directly. Contains composite workflows, full field reference, response schema, agency slug table, docket ID patterns, and troubleshooting. Loaded on demand by the main federalregister-api skill.
---

# Federal Register API Reference

## Table of Contents
1. Response Schema
2. Requestable Fields
3. Composite Workflows
4. Agency Slug Table
5. Docket ID Patterns
6. Troubleshooting

---

## 1. Response Schema

### Document Search
```json
{"description": "...", "count": 36, "total_pages": 12, "next_page_url": "...",
 "results": [{"title": "...", "document_number": "2026-03065",
   "publication_date": "2026-02-17", "type": "Proposed Rule",
   "agencies": [{"name": "...", "slug": "...", "id": 184}],
   "docket_ids": ["FAR Case 2023-008"], "regulation_id_numbers": ["9000-AO56"],
   "comments_close_on": "2026-04-20", "cfr_references": [{"title": 48, "part": 15}],
   "citation": "91 FR 7223", "html_url": "..."}]}
```

### Single Document Detail (additional fields beyond search)
`body_html_url`, `raw_text_url`, `full_text_xml_url`, `dockets` (with Regulations.gov supporting docs), `regulation_id_number_info` (Unified Agenda links), `page_views`, `topics`, `significant`, `volume`, `start_page`/`end_page`, `corrections`, `correction_of` (API URL of original), `signing_date`, `executive_order_number`, `subtype` (Executive Order, Proclamation, Memorandum, etc.).

### PI Documents
Different field set: `filed_at`, `filing_type`, `num_pages`, `subject_1`/`2`/`3`, `agency_names`, `docket_numbers`, `editorial_note`. Do NOT have `abstract`, `cfr_references`, `comments_close_on`, or `docket_ids`.

---

## 2. Requestable Fields

| Field | Type | Notes |
|-------|------|-------|
| `title` | string | Document title |
| `type` | string | "Proposed Rule", "Rule", "Notice", "Presidential Document" |
| `abstract` | string | Summary |
| `document_number` | string | Primary identifier |
| `publication_date` | string | YYYY-MM-DD |
| `html_url` / `pdf_url` | string | FR page / GovInfo PDF |
| `citation` | string | e.g., "91 FR 7223" |
| `agencies` | list | Objects with name, slug, id, parent_id |
| `docket_ids` | list | Docket ID strings (inconsistent format) |
| `regulation_id_numbers` | list | RIN strings |
| `cfr_references` | list | Objects with title (int), part (int) |
| `comment_url` | string | Regulations.gov comment link |
| `comments_close_on` | string | Comment deadline YYYY-MM-DD |
| `dates` | string | Free-text date info |
| `effective_on` | string | Effective date YYYY-MM-DD |
| `action` | string | e.g., "Proposed rule.", "Final rule." |
| `significant` | bool | EO 12866 significant |
| `topics` | list | CFR indexing terms |
| `body_html_url` / `raw_text_url` / `full_text_xml_url` | string | Full text URLs |
| `start_page` / `end_page` / `page_length` | int | FR pages |
| `subtype` | string | Presidential doc subtype |
| `signing_date` | string | Presidential docs |
| `executive_order_number` | int | EO number |
| `correction_of` | string | API URL of original (extract doc number from path) |
| `corrections` | list | Corrections to this document |
| `regulations_dot_gov_url` | string | Regulations.gov URL |

---

## 3. Composite Workflows

### Open Comment Periods for Procurement

```python
from datetime import date

def open_comment_periods_procurement():
    """Proposed rules and notices with open comment periods from FAR Council agencies."""
    today = date.today().isoformat()
    data = search_documents(
        agencies=["federal-procurement-policy-office", "defense-department",
                  "general-services-administration", "national-aeronautics-and-space-administration"],
        doc_types=["PRORULE", "NOTICE"],
        comment_date_gte=today,
        fields=["title", "document_number", "publication_date", "type", "abstract",
                "docket_ids", "comments_close_on", "comment_url", "cfr_references",
                "agencies", "regulation_id_numbers"],
        per_page=100, order="newest")
    results = data.get("results", [])
    results.sort(key=lambda x: x.get("comments_close_on", "9999-99-99"))
    return results
```

### FAR Case History

```python
def far_case_history(docket_id):
    """All FR documents for a FAR case, sorted chronologically.
    If empty, try conditions[term] with quoted docket ID as fallback."""
    data = search_documents(docket_id=docket_id,
        fields=["title", "document_number", "publication_date", "type", "abstract",
                "action", "docket_ids", "regulation_id_numbers", "cfr_references",
                "comments_close_on", "effective_on", "html_url", "citation", "page_length"],
        per_page=100, order="oldest")
    return data.get("results", [])
```

### Agency Regulatory Summary

```python
def agency_regulatory_summary(agency_slug, since_date):
    """Facet counts + recent documents for an agency."""
    facets = get_facet_counts("type", agencies=[agency_slug], pub_date_gte=since_date)
    docs = search_documents(agencies=[agency_slug], pub_date_gte=since_date,
        fields=["title", "document_number", "publication_date", "type", "abstract",
                "docket_ids", "effective_on", "comments_close_on", "action",
                "significant", "html_url"],
        per_page=25, order="newest")
    return {"agency": agency_slug, "since": since_date,
            "type_breakdown": facets, "total_documents": docs.get("count", 0),
            "recent_documents": docs.get("results", [])}
```

### Rules Affecting Specific CFR Parts

```python
def rules_affecting_cfr(title, part, since_date=None, doc_types=None):
    """Find FR documents referencing a CFR title/part. Keyword search + cfr_references verification."""
    data = search_documents(term=f"{title} CFR {part}",
        doc_types=doc_types or ["RULE", "PRORULE"], pub_date_gte=since_date,
        fields=["title", "document_number", "publication_date", "type", "abstract",
                "cfr_references", "docket_ids", "effective_on", "comments_close_on",
                "agencies", "html_url", "citation"],
        per_page=50, order="newest")
    matched = [d for d in data.get("results", [])
               if any(r.get("title") == title and r.get("part") == part
                      for r in d.get("cfr_references", []))]
    return {"cfr_citation": f"{title} CFR Part {part}",
            "total_search_hits": data.get("count", 0),
            "verified_matches": len(matched), "documents": matched}
```

### Multi-Agency Regulatory Scan

```python
import time

def multi_agency_scan(agency_slugs, since_date, doc_types=None):
    """Per-agency summaries of recent rulemaking."""
    if doc_types is None: doc_types = ["PRORULE", "RULE"]
    results = {}
    for slug in agency_slugs:
        try:
            data = search_documents(agencies=[slug], doc_types=doc_types,
                pub_date_gte=since_date,
                fields=["title", "document_number", "publication_date", "type",
                        "docket_ids", "comments_close_on", "effective_on",
                        "significant", "action"],
                per_page=50, order="newest")
            results[slug] = {"count": data.get("count", 0), "documents": data.get("results", [])}
        except Exception as e:
            results[slug] = {"error": str(e)}
        time.sleep(0.3)
    return results
```

### Pre-Publication Watch

```python
def procurement_prepub_watch():
    """Check public inspection for upcoming procurement docs. Filters client-side."""
    pi_data = get_public_inspection_current()
    keywords = ["acquisition", "procurement", "contract", "FAR", "DFARS",
                "small business", "set-aside", "solicitation", "debarment"]
    procurement_docs = []
    for doc in pi_data.get("results", []):
        title = (doc.get("title", "") or "").lower()
        agencies = [a.get("slug", "") for a in doc.get("agencies", [])]
        if (any(kw.lower() in title for kw in keywords) or
            "federal-procurement-policy-office" in agencies):
            procurement_docs.append(doc)
    return {"total_pi": pi_data.get("count", 0),
            "procurement_related": len(procurement_docs), "documents": procurement_docs}
```

### Regulatory Timeline

```python
def regulatory_timeline(term, since_date, agency_slugs=None):
    """Chronological timeline of all regulatory actions for a topic."""
    all_docs, page = [], 1
    while True:
        data = search_documents(term=term, agencies=agency_slugs, pub_date_gte=since_date,
            fields=["title", "document_number", "publication_date", "type", "abstract",
                    "action", "docket_ids", "regulation_id_numbers", "comments_close_on",
                    "effective_on", "significant", "agencies", "citation", "html_url"],
            per_page=100, page=page, order="oldest")
        results = data.get("results", [])
        all_docs.extend(results)
        if not data.get("next_page_url"): break
        page += 1
        time.sleep(0.3)
    return {"topic": term, "total_documents": data.get("count", 0),
            "retrieved": len(all_docs), "timeline": all_docs}
```

---

## 4. Procurement-Relevant Agency Slugs

| Slug | Agency |
|------|--------|
| `federal-procurement-policy-office` | OFPP (OMB) |
| `defense-department` | DoD |
| `general-services-administration` | GSA |
| `national-aeronautics-and-space-administration` | NASA |
| `small-business-administration` | SBA |
| `management-and-budget-office` | OMB |
| `veterans-affairs-department` | VA |
| `health-and-human-services-department` | HHS |
| `food-and-drug-administration` | FDA |
| `homeland-security-department` | DHS |
| `energy-department` | DOE |
| `interior-department` | DOI |
| `labor-department` | DOL |
| `commerce-department` | DOC |
| `state-department` | DOS |
| `cost-accounting-standards-board` | CASB (OMB) |
| `defense-acquisition-regulations-system` | DARS (DoD) |

---

## 5. Docket ID Patterns

| Pattern | Example | Source |
|---------|---------|--------|
| FAR Case YYYY-NNN | FAR Case 2023-008 | FAR Council |
| FAC YYYY-NN, FAR Case YYYY-NNN | FAC 2025-05, FAR Case 2023-018 | FAC |
| Docket No. FAR-YYYY-NNNN | Docket No. FAR-2023-0008 | Regulations.gov |
| Docket DARS-YYYY-NNNN | Docket DARS-2024-0032 | DFARS |

Note: `docket_ids` array format is inconsistent. Sometimes separate elements, sometimes comma-separated within one string. Parse defensively.

---

## 6. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| Missing fields | Not requested via `fields[]` | Always specify needed fields |
| `commenting_on` invalid | Wrong parameter | Use `conditions[comment_date][gte/lte]` |
| Empty results for known docket | String mismatch | Try `conditions[term]` with quoted phrase |
| URL returns HTML | Missing `.json` suffix | Ensure URL ends with `.json` |
| Brackets not parsed | Not URL-encoded | Encode `[` as `%5B`, `]` as `%5D` |
| Facet 404 | Invalid facet name | Only `type`, `agency`, `topic` |
| Wrong sort | Bad `order` value | Use `newest`, `oldest`, `relevance`, `executive_order_number` |
| PI stale data | Weekend query | PI refreshes business days only |
| `comments_close_on` null | No formal comment period | Check `dates` for informal text |
| PI filters ignored | `/current` ignores `conditions[]` | Filter client-side; `fields[]` works |
| Count = 10000 | Hard cap | Use date ranges for accurate counts |
| `docket_ids` parsing fails | Inconsistent format | Split on commas defensively |
| CORRECT type returns old data | Legacy pre-2009 only | Use `conditions[correction]=1` for modern |
| Term search returns 0 | Stop words filtered | Use substantive keywords |


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*