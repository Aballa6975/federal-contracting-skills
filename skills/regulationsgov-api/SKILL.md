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

**For composite workflows, response schemas, pagination, document ID patterns, and troubleshooting:** `view` the REFERENCE.md file in this skill directory.

## Critical Rules

### 1. Bracket Syntax in URLs
All params use brackets: `filter[searchTerm]`, `page[size]`. Python `urllib.parse.urlencode()` handles encoding automatically.

### 2. Page Size Limits
Min 5, max 250. Default 25. Values outside range return 400.

### 3. Pagination Ceiling (~5,000 Records)
Max ~20 pages at size 250. Beyond that, use cursor-based pagination with `lastModifiedDate`. See REFERENCE.md.

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

## Rate Limiting

1. **Key required.** DEMO_KEY: 40/hr. Registered: 1,000/hr
2. Add 0.5s delays in batch operations
3. Check `x-ratelimit-remaining` header (lowercase)
4. Use aggregations for counts instead of paging
5. Filter aggressively before paginating
6. Use `sort=-postedDate` for most recent first

---

## Additional Resources

For composite workflows (open comment tracker, FAR case history, comment analysis, regulatory change monitor, multi-agency docket search), response schemas, cursor-based pagination, document ID format guide, FAR case docket IDs, and troubleshooting: `view` the **REFERENCE.md** file in this skill directory.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*