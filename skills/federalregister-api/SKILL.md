---
name: federalregister-api
description: >
  Query the FederalRegister.gov REST API for Federal Register documents including proposed rules, final rules, notices, executive orders, and public inspection documents. Trigger for any mention of Federal Register, FR documents, proposed rules, final rules, comment periods, FAR cases, rulemaking, regulatory tracking, CFR parts affected, RINs, docket IDs, or public inspection documents. Also trigger when the user needs to monitor regulatory changes affecting acquisition policy, track open comment periods for procurement rules, research the history of a FAR case or docket, or find agency-specific regulatory actions. Complements USASpending (spending data) and CALC+ (labor rates) for a complete procurement intelligence toolkit.
---

# FederalRegister.gov API Skill

## Overview

The FederalRegister.gov API provides free, no-auth access to all FR content since 1994. No key, no registration. Just HTTP GET.

Base URL: `https://www.federalregister.gov/api/v1/`

**What this data is:** Official daily journal of the US Government: proposed rules, final rules, notices, presidential documents, corrections. Includes metadata, docket linkages, CFR references, comment deadlines.

**What this data is NOT:** Not Regulations.gov (which hosts comments and dockets). Cross-linked via docket IDs and comment_url fields.

**For composite workflows, full field reference, agency slug table, docket ID patterns, and troubleshooting:** `view` the REFERENCE.md file in this skill directory.

## Critical Rules

### 1. Default Response Returns Only 10 Fields
Without `fields[]`, you only get: title, type, abstract, document_number, html_url, pdf_url, public_inspection_pdf_url, publication_date, agencies, excerpts. **Always request the fields you need.**

### 2. Document Type Codes

| Code | Meaning |
|------|---------|
| PRORULE | Proposed Rule |
| RULE | Final Rule |
| NOTICE | Notice |
| PRESDOCU | Presidential Document |
| CORRECT | Legacy pre-2009 corrections only |

**Modern corrections:** Use `conditions[correction]=1` (returns C1- prefix docs with `correction_of` field). Do NOT use `conditions[type][]=CORRECT`.

### 3. Agency Slugs, Not Names
Use URL slugs: `federal-procurement-policy-office`, `defense-department`, `food-and-drug-administration`. Multiple agencies supported (OR logic) by repeating parameter. Full table in REFERENCE.md.

### 4. Docket ID Uses Substring Matching
`"FAR Case 2023-008"` = exact match (4 docs). `"FAR Case 2023"` = all 2023 cases (22 docs). Be specific to avoid false positives.

### 5. Count Caps at 10,000
For broad queries, `count` returns exactly 10000. Use date ranges to get accurate counts.

### 6. Comment Period Filter
Use `conditions[comment_date][gte/lte]`, NOT `commenting_on`. Response field is `comments_close_on`.

### 7. Pagination
`per_page` default 20 (values >1000 accepted). `page` for pagination. `next_page_url` for simple iteration. 2000-page cap is not enforced in practice, but use date ranges for very large sets.

---

## Core Endpoints

### 1. Document Search (PRIMARY WORKHORSE)

**Endpoint:** `GET /api/v1/documents.json`

```python
import urllib.request, urllib.parse, json

def search_documents(agencies=None, doc_types=None, term=None, docket_id=None,
                     regulation_id_number=None,
                     pub_date_gte=None, pub_date_lte=None,
                     comment_date_gte=None, comment_date_lte=None,
                     effective_date_gte=None, effective_date_lte=None,
                     correction=None,
                     fields=None, per_page=20, page=1, order="newest"):
    """Search FR documents with flexible filtering."""
    if fields is None:
        fields = ["title", "document_number", "publication_date", "type", "abstract",
                  "agencies", "docket_ids", "regulation_id_numbers", "comment_url",
                  "comments_close_on", "cfr_references", "html_url", "pdf_url",
                  "citation", "dates", "effective_on", "action", "significant"]
    params = []
    if agencies:
        for a in agencies: params.append(("conditions[agencies][]", a))
    if doc_types:
        for t in doc_types: params.append(("conditions[type][]", t))
    if term: params.append(("conditions[term]", term))
    if docket_id: params.append(("conditions[docket_id]", docket_id))
    if regulation_id_number: params.append(("conditions[regulation_id_number]", regulation_id_number))
    if pub_date_gte: params.append(("conditions[publication_date][gte]", pub_date_gte))
    if pub_date_lte: params.append(("conditions[publication_date][lte]", pub_date_lte))
    if comment_date_gte: params.append(("conditions[comment_date][gte]", comment_date_gte))
    if comment_date_lte: params.append(("conditions[comment_date][lte]", comment_date_lte))
    if effective_date_gte: params.append(("conditions[effective_date][gte]", effective_date_gte))
    if effective_date_lte: params.append(("conditions[effective_date][lte]", effective_date_lte))
    if correction is not None: params.append(("conditions[correction]", str(correction)))
    for f in fields: params.append(("fields[]", f))
    params.append(("per_page", str(per_page)))
    params.append(("page", str(page)))
    params.append(("order", order))
    url = f"https://www.federalregister.gov/api/v1/documents.json?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 2. Single Document Detail

**Endpoint:** `GET /api/v1/documents/{document_number}.json`

Without `fields[]`, returns ALL fields including full text URLs, dockets, RIN info, page views.

```python
def get_document(document_number, fields=None):
    url = f"https://www.federalregister.gov/api/v1/documents/{document_number}.json"
    if fields:
        url += f"?{urllib.parse.urlencode([('fields[]', f) for f in fields])}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 3. Multi-Document Batch

**Endpoint:** `GET /api/v1/documents/{num1},{num2},{num3}.json`

Up to ~20 documents per call.

```python
def get_documents_batch(document_numbers, fields=None):
    nums = ",".join(document_numbers)
    url = f"https://www.federalregister.gov/api/v1/documents/{nums}.json"
    if fields:
        url += f"?{urllib.parse.urlencode([('fields[]', f) for f in fields])}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 4. Faceted Counts

**Endpoint:** `GET /api/v1/documents/facets/{facet_name}`

Facets: `type`, `agency`, `topic`. Accepts same `conditions[]` as search.

```python
def get_facet_counts(facet_name, agencies=None, doc_types=None, term=None,
                     pub_date_gte=None, pub_date_lte=None):
    params = []
    if agencies:
        for a in agencies: params.append(("conditions[agencies][]", a))
    if doc_types:
        for t in doc_types: params.append(("conditions[type][]", t))
    if term: params.append(("conditions[term]", term))
    if pub_date_gte: params.append(("conditions[publication_date][gte]", pub_date_gte))
    if pub_date_lte: params.append(("conditions[publication_date][lte]", pub_date_lte))
    query_string = urllib.parse.urlencode(params) if params else ""
    url = f"https://www.federalregister.gov/api/v1/documents/facets/{facet_name}"
    if query_string: url += f"?{query_string}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 5. Public Inspection (Pre-Publication)

**Endpoint:** `GET /api/v1/public-inspection-documents/current.json`

Does NOT support `conditions[]` filters. Returns full list; filter client-side. `fields[]` does work.

```python
def get_public_inspection_current():
    url = "https://www.federalregister.gov/api/v1/public-inspection-documents/current.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 6. Agencies Lookup

```python
def get_agencies():
    """Get all ~470 agencies with id, name, slug, parent_id."""
    url = "https://www.federalregister.gov/api/v1/agencies.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

---

## Search Conditions Reference

| Parameter | Description |
|-----------|-------------|
| `conditions[agencies][]` | Agency slug (repeatable, OR logic) |
| `conditions[type][]` | PRORULE, RULE, NOTICE, PRESDOCU (repeatable) |
| `conditions[term]` | Full-text keyword (strips stop words) |
| `conditions[docket_id]` | Docket ID (substring match) |
| `conditions[regulation_id_number]` | RIN (precise match) |
| `conditions[publication_date][gte/lte]` | Publication date range |
| `conditions[effective_date][gte/lte]` | Effective date range |
| `conditions[comment_date][gte/lte]` | Comment close date range |
| `conditions[correction]` | 0 or 1 (modern corrections) |
| `conditions[significant]` | 0 or 1 (EO 12866) |

**Order:** `newest` (default), `oldest`, `relevance`, `executive_order_number`

---

## Rate Limiting

1. No auth required; fully public
2. Add 0.3s delays in batch operations
3. Use `fields[]` to reduce payload size
4. Use `next_page_url` for simple pagination
5. Break broad queries by date range for accurate counts and performance

---

## Important Notes

1. **Not an official legal edition.** For official citations, use GPO's govinfo.gov.
2. **Coverage since 1994** (Volume 59 forward).
3. **Cross-reference with Regulations.gov** via `comment_url` and `regulations_dot_gov_url`.
4. **RINs link to Unified Agenda** at reginfo.gov for rulemaking stage tracking.

---

## Additional Resources

For composite workflows (open comment periods, FAR case history, CFR part tracking, agency regulatory summary, multi-agency scan, pre-pub watch, regulatory timeline), full requestable field reference, response schema, agency slug table, docket ID patterns, and troubleshooting: `view` the **REFERENCE.md** file in this skill directory.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*