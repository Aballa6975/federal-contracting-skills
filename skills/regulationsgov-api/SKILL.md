---
name: regulationsgov-api
description: >
  Query the Regulations.gov REST API for federal rulemaking data including proposed rules, final rules, notices, public comments, and dockets. Trigger for any mention of Regulations.gov, FAR cases, DFARS cases, proposed rules, NPRMs, ANPRMs, comment periods, rulemaking, dockets, Federal Register notices, or regulatory tracking. Also trigger when the user needs to monitor regulatory changes from FAR Council, DARS, SBA, OFPP, or any agency supplement. This skill is essential for tracking active and upcoming regulatory changes that affect federal procurement policy, contract clauses, and acquisition procedures.
---

# Regulations.gov API Skill

## Overview

The Regulations.gov API provides access to all federal rulemaking data: proposed rules, final rules, notices, comments, and docket metadata.

Base URL: `https://api.regulations.gov/v4/`
Docs: https://open.gsa.gov/api/regulationsgov/

**API Key Required.** Free at https://open.gsa.gov/api/regulationsgov/#getting-started. `DEMO_KEY` available (40 req/hr). Real key: 1,000 req/hr. Pass as `api_key=KEY` or header `X-Api-Key: KEY`.

This skill is self-contained. Composite workflows, response schemas, pagination, document ID patterns, and troubleshooting are all below.

## Critical Rules

### 1. Bracket Syntax in URLs
All params use brackets: `filter[searchTerm]`, `page[size]`. Python `urllib.parse.urlencode()` handles encoding automatically.

### 2. Page Size Limits
Min 5, max 250. Default 25. Values outside range return 400.

### 3. Pagination Ceiling (~5,000 Records)
Max ~20 pages at size 250. Beyond that, use cursor-based pagination with `lastModifiedDate`. See Pagination section below.

### 4. objectId vs documentId for Comments
To find comments on a document, use the hex `objectId` (from search attributes), NOT the human-readable documentId. Pass to `filter[commentOnId]`.

### 5. Date Format Asymmetry (SECOND MOST COMMON ERROR)

| Filter | Format | Example |
|--------|--------|---------|
| `postedDate` | Date only | `filter[postedDate][ge]=2025-01-01` |
| `commentEndDate` | Date only | `filter[commentEndDate][ge]=2025-06-01` |
| `lastModifiedDate` | **Datetime only** | `filter[lastModifiedDate][ge]=2025-01-01 00:00:00` |

`lastModifiedDate` rejects date-only and ISO T/Z formats. Must use space-separated `YYYY-MM-DD HH:MM:SS`.

### 6. Filter Values Are Case-Sensitive
`Rulemaking` works; `rulemaking` silently returns 0 results (no error). Use exact casing: `Proposed Rule`, `Rule`, `Notice`, `Supporting & Related Material`, `Rulemaking`, `Nonrulemaking`.

### 7. Sort and Filter Support Varies by Endpoint

**Sort:**

| Field | documents | comments | dockets |
|-------|:-:|:-:|:-:|
| `postedDate` | Yes | Yes | No |
| `commentEndDate` | Yes | No | No |
| `lastModifiedDate` | Yes | Yes | Yes |
| `title` | Yes | No | Yes |
| `documentId`/`docketId` | Yes | Yes | Yes |

**Filters:**

| Filter | documents | comments | dockets |
|--------|:-:|:-:|:-:|
| `searchTerm` | Yes | Yes | Yes |
| `agencyId` | Yes | Yes | Yes |
| `documentType` | Yes | No | No |
| `docketId` | Yes | Yes | No |
| `withinCommentPeriod` | Yes | No | No |
| `postedDate[ge/le]` | Yes | Yes | No |
| `commentEndDate[ge/le]` | Yes | No | No |
| `lastModifiedDate[ge/le]` | Yes | Yes | Yes |
| `commentOnId` | No | Yes | No |
| `docketType` | No | No | Yes |

### 8. Aggregations Always Present
Every search response includes `meta.aggregations` scoped to your current filters. Use for quick counts without paging. Docket aggregations include `ruleStage` (pre-rule, proposed, final, completed).

### 9. Acquisition-Relevant Agency IDs

| ID | Agency | Publishes |
|----|--------|-----------|
| FAR | FAR Council | FAR rules, cases |
| DARS | Defense Acquisition Regs | DFARS rules |
| GSA | GSA | GSAR rules, MAS policy |
| SBA | Small Business Admin | Size standards, set-asides |
| OFPP | Procurement Policy Office | Policy memos |
| DOD | Defense Department | Acquisition DODIs |
| NASA | NASA | NFS supplement rules |
| VA | VA | VAAR supplement rules |
| HHS | HHS | HHSAR supplement rules |

---

## Core Endpoints

### 1. Document Search (PRIMARY WORKHORSE)

**Endpoint:** `GET /v4/documents`

```python
import urllib.request, urllib.parse, json

def search_documents(api_key, search_term=None, agency_id=None, document_type=None,
                     docket_id=None, within_comment_period=None, subtype=None,
                     posted_date_ge=None, posted_date_le=None,
                     comment_end_date_ge=None, comment_end_date_le=None,
                     last_modified_date_ge=None, last_modified_date_le=None,
                     sort="-postedDate", page_size=25, page_number=1):
    params = {'api_key': api_key, 'page[size]': page_size, 'page[number]': page_number}
    if sort: params['sort'] = sort
    if search_term: params['filter[searchTerm]'] = search_term
    if agency_id: params['filter[agencyId]'] = agency_id
    if document_type: params['filter[documentType]'] = document_type
    if docket_id: params['filter[docketId]'] = docket_id
    if within_comment_period is not None: params['filter[withinCommentPeriod]'] = str(within_comment_period).lower()
    if subtype: params['filter[subtype]'] = subtype
    if posted_date_ge: params['filter[postedDate][ge]'] = posted_date_ge
    if posted_date_le: params['filter[postedDate][le]'] = posted_date_le
    if comment_end_date_ge: params['filter[commentEndDate][ge]'] = comment_end_date_ge
    if comment_end_date_le: params['filter[commentEndDate][le]'] = comment_end_date_le
    if last_modified_date_ge: params['filter[lastModifiedDate][ge]'] = last_modified_date_ge
    if last_modified_date_le: params['filter[lastModifiedDate][le]'] = last_modified_date_le
    url = f"https://api.regulations.gov/v4/documents?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

**Document Types:** `Proposed Rule`, `Rule`, `Notice`, `Supporting & Related Material`, `Other`

### 2. Document Detail

**Endpoint:** `GET /v4/documents/{documentId}`

```python
def get_document_detail(api_key, document_id, include_attachments=False):
    params = {'api_key': api_key}
    if include_attachments: params['include'] = 'attachments'
    url = f"https://api.regulations.gov/v4/documents/{document_id}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Returns: `fileFormats` (download URLs), `cfrPart`, `displayProperties`, plus frequently-null fields: `frVolNum`, `startEndPage`, `effectiveDate`.

### 3. Comment Search

**Endpoint:** `GET /v4/comments`

```python
def search_comments(api_key, search_term=None, agency_id=None, comment_on_id=None,
                    docket_id=None, posted_date_ge=None, posted_date_le=None,
                    last_modified_date_ge=None, last_modified_date_le=None,
                    sort="-postedDate", page_size=25, page_number=1):
    params = {'api_key': api_key, 'page[size]': page_size, 'page[number]': page_number}
    if sort: params['sort'] = sort
    if search_term: params['filter[searchTerm]'] = search_term
    if agency_id: params['filter[agencyId]'] = agency_id
    if comment_on_id: params['filter[commentOnId]'] = comment_on_id
    if docket_id: params['filter[docketId]'] = docket_id
    if posted_date_ge: params['filter[postedDate][ge]'] = posted_date_ge
    if posted_date_le: params['filter[postedDate][le]'] = posted_date_le
    if last_modified_date_ge: params['filter[lastModifiedDate][ge]'] = last_modified_date_ge
    if last_modified_date_le: params['filter[lastModifiedDate][le]'] = last_modified_date_le
    url = f"https://api.regulations.gov/v4/comments?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### 4. Comment Detail

**Endpoint:** `GET /v4/comments/{commentId}`

```python
def get_comment_detail(api_key, comment_id, include_attachments=False):
    params = {'api_key': api_key}
    if include_attachments: params['include'] = 'attachments'
    url = f"https://api.regulations.gov/v4/comments/{comment_id}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Returns: `comment` (full text), `firstName`, `lastName`, `organization`, `trackingNbr`, `fileFormats`, `docketId`, `duplicateComments`. Some fields are agency-configurable and may be hidden.

### 5. Docket Search

**Endpoint:** `GET /v4/dockets`

```python
def search_dockets(api_key, search_term=None, agency_id=None, docket_type=None,
                   last_modified_date_ge=None, last_modified_date_le=None,
                   sort=None, page_size=25, page_number=1):
    params = {'api_key': api_key, 'page[size]': page_size, 'page[number]': page_number}
    if sort: params['sort'] = sort
    if search_term: params['filter[searchTerm]'] = search_term
    if agency_id: params['filter[agencyId]'] = agency_id
    if docket_type: params['filter[docketType]'] = docket_type
    if last_modified_date_ge: params['filter[lastModifiedDate][ge]'] = last_modified_date_ge
    if last_modified_date_le: params['filter[lastModifiedDate][le]'] = last_modified_date_le
    url = f"https://api.regulations.gov/v4/dockets?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Types: `Rulemaking`, `Nonrulemaking`. Only supports `searchTerm`, `agencyId`, `docketType`, `lastModifiedDate` filters.

### 6. Docket Detail

**Endpoint:** `GET /v4/dockets/{docketId}`

```python
def get_docket_detail(api_key, docket_id):
    url = f"https://api.regulations.gov/v4/dockets/{docket_id}?api_key={api_key}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

Returns: `title`, `docketType`, `agencyId`, `rin` (links to Unified Agenda), `dkAbstract`, `keywords`, `modifyDate`.

---

## Response Schemas

### Search Endpoints (documents, comments, dockets)
```json
{"data": [{"id": "FAR-2023-0008-0023", "type": "documents",
   "attributes": {"documentType": "Proposed Rule", "title": "...", "agencyId": "FAR",
     "docketId": "FAR-2023-0008", "postedDate": "2025-01-15T00:00:00Z",
     "commentEndDate": "2025-03-17T00:00:00Z", "withinCommentPeriod": true,
     "openForComment": true, "objectId": "09000064b91b1fcd", "frDocNum": "2025-00123"},
   "links": {"self": "..."}}],
 "meta": {"aggregations": {"documentType": [{"docCount": 4473, "label": "Proposed Rule"}],
   "agencyId": [{"docCount": 393, "value": "EPA"}], "withinCommentPeriod": [{"docCount": 1, "label": "true"}]},
  "hasNextPage": true, "totalElements": 4473, "totalPages": 179, "pageNumber": 1, "pageSize": 25}}
```

### Detail Endpoints
Single object (not array): `{"data": {"id": "...", "type": "documents", "attributes": {...}}}`

With `include=attachments`: adds top-level `included` array with attachment objects containing `fileFormats` URLs.

### Aggregation Keys by Endpoint
- **documents:** `documentType`, `subtype`, `agencyId`, `withinCommentPeriod`, `postedDate`, `commentEndDate`
- **comments:** `agencyId`, `postedDate`
- **dockets:** `agencyId`, `docketType`, `ruleStage`, `major`, `smallEntities`, `priorityCategory`

---

## Search Response Fields

### Document Search Fields
| Field | Description |
|-------|-------------|
| `id` | Document ID (e.g., FAR-2023-0008-0023) |
| `attributes.documentType` | Proposed Rule, Rule, Notice, Supporting & Related Material, Other |
| `attributes.title` | Document title |
| `attributes.agencyId` | Agency code |
| `attributes.docketId` | Parent docket |
| `attributes.postedDate` | Posted date (ISO 8601) |
| `attributes.commentStartDate` / `commentEndDate` | Comment period dates |
| `attributes.withinCommentPeriod` | Boolean: active comment period? |
| `attributes.openForComment` | Boolean: accepting comments? (response only, not a filter) |
| `attributes.subtype` | NPRM, ANPRM, etc. |
| `attributes.frDocNum` | Federal Register doc number |
| `attributes.objectId` | Hex ID (needed for comment lookups) |
| `attributes.highlightedContent` | HTML snippet with `<mark><em>` tags |

### Document Detail (additional fields)
`fileFormats` (download URLs), `cfrPart`, `displayProperties`, `frVolNum`, `startEndPage`, `effectiveDate`, `authors`.

Content URLs: `https://downloads.regulations.gov/{documentId}/content.{format}`. May return 403 programmatically.

### Comment Search Fields
| Field | Description |
|-------|-------------|
| `id` | Comment ID |
| `attributes.title` | Comment title |
| `attributes.agencyId` | Agency |
| `attributes.postedDate` | Posted date |
| `attributes.objectId` | Hex ID |
| `attributes.highlightedContent` | HTML snippet |

Detail-only fields: `comment` (full text), `organization`, `firstName`, `lastName`, `docketId`, `fileFormats`, `trackingNbr`, `duplicateComments`.

### Docket Search Fields
`id`, `attributes.agencyId`, `attributes.docketType`, `attributes.title`, `attributes.lastModifiedDate`, `attributes.objectId`.

Detail-only: `rin`, `dkAbstract`, `keywords`, `modifyDate`, `effectiveDate`, `category`, `subType`.

---

## Composite Workflows

### Open Comment Period Tracker

```python
import time

PROCUREMENT_AGENCIES = ['FAR', 'DARS', 'GSA', 'SBA', 'OFPP', 'OMB', 'DOD', 'NASA', 'VA', 'HHS', 'FDA']

def open_comment_periods(api_key, agencies=None):
    """Find documents with open comment periods from procurement agencies."""
    if agencies is None: agencies = PROCUREMENT_AGENCIES
    open_docs = []
    for agency in agencies:
        try:
            result = search_documents(api_key, agency_id=agency,
                within_comment_period=True, sort='-commentEndDate', page_size=50)
            for item in result.get('data', []):
                attrs = item['attributes']
                open_docs.append({'document_id': item['id'], 'agency': attrs['agencyId'],
                    'title': attrs['title'], 'document_type': attrs['documentType'],
                    'comment_end_date': attrs.get('commentEndDate'),
                    'docket_id': attrs.get('docketId'),
                    'url': f"https://www.regulations.gov/document/{item['id']}"})
        except: pass
        time.sleep(0.5)
    valid = [d for d in open_docs if d.get('comment_end_date')]
    valid.sort(key=lambda x: x['comment_end_date'])
    return valid
```

### FAR Case History

```python
def far_case_history(api_key, docket_id):
    """Full lifecycle: docket metadata + all documents."""
    docket = get_docket_detail(api_key, docket_id)
    docket_attrs = docket.get('data', {}).get('attributes', {})
    time.sleep(0.5)
    docs_result = search_documents(api_key, docket_id=docket_id, sort='-postedDate', page_size=250)
    documents = [{'document_id': item['id'],
        'document_type': item['attributes']['documentType'],
        'title': item['attributes']['title'],
        'posted_date': item['attributes'].get('postedDate'),
        'comment_end_date': item['attributes'].get('commentEndDate'),
        'object_id': item['attributes'].get('objectId'),
        'url': f"https://www.regulations.gov/document/{item['id']}"}
        for item in docs_result.get('data', [])]
    return {'docket_id': docket_id, 'title': docket_attrs.get('title'),
        'abstract': docket_attrs.get('dkAbstract'), 'rin': docket_attrs.get('rin'),
        'agency': docket_attrs.get('agencyId'),
        'total_documents': docs_result.get('meta', {}).get('totalElements', 0),
        'documents': documents, 'url': f"https://www.regulations.gov/docket/{docket_id}"}
```

### Comment Analysis

```python
def get_document_comments(api_key, document_id, max_comments=500):
    """Get comments on a document. Requires objectId lookup first."""
    doc = get_document_detail(api_key, document_id)
    object_id = doc.get('data', {}).get('attributes', {}).get('objectId')
    if not object_id: return {'error': f'No objectId for {document_id}'}
    time.sleep(0.5)
    all_comments, page = [], 1
    while len(all_comments) < max_comments:
        result = search_comments(api_key, comment_on_id=object_id,
            sort='-postedDate', page_size=250, page_number=page)
        data = result.get('data', [])
        all_comments.extend(data)
        if not result.get('meta', {}).get('hasNextPage') or not data: break
        page += 1; time.sleep(0.5)
    comments = [{'comment_id': item['id'], 'title': item['attributes'].get('title'),
        'posted_date': item['attributes'].get('postedDate'),
        'url': f"https://www.regulations.gov/comment/{item['id']}"}
        for item in all_comments[:max_comments]]
    return {'document_id': document_id, 'total_comments': result.get('meta', {}).get('totalElements', len(comments)),
        'comments': comments}
```

### Regulatory Change Monitor

```python
def recent_regulatory_activity(api_key, agencies=None, days_back=30, document_types=None):
    """Recent rulemaking activity across agencies."""
    from datetime import datetime, timedelta
    if agencies is None: agencies = ['FAR', 'DARS', 'GSA', 'SBA']
    if document_types is None: document_types = ['Proposed Rule', 'Rule']
    start_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
    all_activity = []
    for agency in agencies:
        for doc_type in document_types:
            try:
                result = search_documents(api_key, agency_id=agency, document_type=doc_type,
                    posted_date_ge=start_date, sort='-postedDate', page_size=50)
                for item in result.get('data', []):
                    attrs = item['attributes']
                    all_activity.append({'document_id': item['id'], 'agency': attrs['agencyId'],
                        'document_type': attrs['documentType'], 'title': attrs['title'],
                        'posted_date': attrs.get('postedDate'),
                        'comment_end_date': attrs.get('commentEndDate'),
                        'docket_id': attrs.get('docketId'),
                        'url': f"https://www.regulations.gov/document/{item['id']}"})
            except: pass
            time.sleep(0.5)
    all_activity.sort(key=lambda x: x.get('posted_date', ''), reverse=True)
    return {'activity': all_activity, 'date_range': f'{start_date} to present'}
```

### Multi-Agency Docket Search

```python
def find_rulemaking_dockets(api_key, search_term, agencies=None):
    if agencies is None: agencies = PROCUREMENT_AGENCIES
    results = []
    for agency in agencies:
        try:
            result = search_dockets(api_key, search_term=search_term,
                agency_id=agency, docket_type='Rulemaking', page_size=25)
            for item in result.get('data', []):
                attrs = item['attributes']
                results.append({'docket_id': item['id'], 'agency': attrs['agencyId'],
                    'title': attrs.get('title'), 'last_modified': attrs.get('lastModifiedDate'),
                    'url': f"https://www.regulations.gov/docket/{item['id']}"})
        except: pass
        time.sleep(0.5)
    results.sort(key=lambda x: x.get('last_modified', ''), reverse=True)
    return results
```

---

## Pagination

### Simple Pagination
```python
def paginate_documents(api_key, max_records=500, **search_kwargs):
    all_data, page = [], 1
    page_size = min(250, max_records)
    while len(all_data) < max_records:
        result = search_documents(api_key, page_size=page_size, page_number=page, **search_kwargs)
        data = result.get('data', [])
        all_data.extend(data)
        meta = result.get('meta', {})
        if not meta.get('hasNextPage') or not data or len(all_data) >= meta.get('totalElements', 0): break
        page += 1; time.sleep(0.5)
    return all_data[:max_records], result.get('meta', {})
```

### Cursor-Based (Beyond 5,000 Records)
Sort by `lastModifiedDate,documentId`, page through first batch, then use last record's `lastModifiedDate` as `filter[lastModifiedDate][ge]` for next batch. Convert ISO timestamp: replace `T` with space, remove `Z`.

---

## Document ID Format

Pattern: `{agencyId}-{year}-{sequence}-{document_number}`

Examples: `FAR-2023-0008-0023`, `DARS-2025-0071-0001`, `SBA-2024-0002-0001`

Docket ID = first three segments: `FAR-2023-0008`. Use `filter[docketId]` to get all documents in a docket.

---

## Common FAR Case Docket IDs

| Docket ID | FAR Case | Subject |
|-----------|----------|---------|
| FAR-2023-0008 | 2023-008 | Semiconductor Products and Services |
| FAR-2017-0016 | 2017-016 | Controlled Unclassified Information |
| FAR-2024-0007 | 2024-007 | Protests under Multiple-Award Contracts |
| FAR-2025-0006 | 2025-006 | Paper Straws |

Find all FAR cases: `filter[agencyId]=FAR&filter[docketType]=Rulemaking` on dockets endpoint.

---

## Rate Limiting

1. **Key required.** DEMO_KEY: 40/hr. Registered: 1,000/hr
2. Add 0.5s delays in batch operations
3. Check `x-ratelimit-remaining` header (lowercase)
4. Use aggregations for counts instead of paging
5. Filter aggressively before paginating
6. Use `sort=-postedDate` for most recent first

---

## Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| 400 "Invalid date format" | `lastModifiedDate` needs datetime | Use `2025-01-01 00:00:00` (space, no T/Z) |
| 400 page size error | Below 5 or above 250 | Use 5-250 range |
| 400 page number error | Exceeded ceiling or 0-indexed | 1-based; use cursor pagination for large sets |
| 429 Too Many Requests | Rate limit | Wait; use registered key (1,000/hr) |
| 400 "Invalid filter: openForComment" | Response-only field | Use `filter[withinCommentPeriod]=true` |
| 0 results unexpectedly | Case-sensitive filter values | `Rulemaking` not `rulemaking`; `Proposed Rule` not `proposed rule` |
| Comments not found | Using documentId not objectId | Get objectId from search, use with `filter[commentOnId]` |
| HTML tags in content | Normal | Strip `<mark>`, `<em>` tags |
| `frDocNum` null | Not published in FR | Normal for supporting docs |
| Comment fields missing | Agency-configurable | Never expect firstName/lastName/org |
| `withinCommentPeriod` false but `openForComment` true | Late comments accepted | Check `openForComment` client-side |
| 400 invalid sort on comments | Wrong sort field | Comments only: `postedDate`, `lastModifiedDate`, `documentId` |
| 400 invalid filter on dockets | Unsupported filter | Dockets only: `searchTerm`, `agencyId`, `docketType`, `lastModifiedDate` |
| `docketId` filter on comments returns nothing | Possible; try `commentOnId` | `docketId` works on comments but covers all docs in docket |


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*
