---
name: ecfr-api
description: Query the eCFR (Electronic Code of Federal Regulations) API for current and historical regulatory text, structure, and version history. Use when the user asks about CFR text, FAR clauses, DFARS provisions, agency FAR supplements, regulatory definitions, clause lookups, point-in-time comparisons, version history, or CFR hierarchy. Trigger for any mention of eCFR, CFR, Code of Federal Regulations, FAR text, DFARS text, clause lookup, regulatory text, CFR title/part/section, or specific citations (e.g., 48 CFR 15.305, FAR 52.212-4, DFARS 252.227-7014). Also trigger when the user needs to read a FAR/DFARS clause, list sections in a part, compare regulation text across dates, check amendment dates, or find definitions. Complements the Federal Register skill (what is changing) by showing what regulations currently say and what they said historically.
---

# eCFR (Electronic Code of Federal Regulations) API Skill

## Overview

The eCFR API (https://www.ecfr.gov) provides free, no-auth access to the full text, structure, and version history of the Code of Federal Regulations. No API key, no registration, no auth headers. Just HTTP GET.

Base URL: `https://www.ecfr.gov`

**What this data is:** The continuously updated online CFR, incorporating Federal Register amendments as published. Point-in-time access back to January 2017.

**What this data is NOT:** Not an official legal edition. For official citations, reference the annual CFR from GPO's govinfo.gov.

**Relationship to Federal Register skill:** The Federal Register is the newspaper (what changed today, what's proposed). The eCFR is the book (full current text after all changes are incorporated).

**For composite workflows, response schemas, reference tables, and troubleshooting:** `view` the REFERENCE.md file in this skill directory.

## Critical Rules

### 1. Content is XML Only (MOST COMMON MISTAKE)
The full-text content endpoint (`/api/versioner/v1/full/`) returns XML only. Requesting `.json` returns HTTP 406. You MUST request `.xml` and parse the XML response. Structure/metadata endpoints return JSON normally.

### 2. Date Must Not Exceed `up_to_date_as_of` (CAUSES 404s)
Versioner endpoints require a date in `YYYY-MM-DD`. No `current` keyword. If the date exceeds `up_to_date_as_of`, the API returns 404. Today's date often fails because eCFR lags 1-2 business days. **Always call `get_latest_date()` first.**

### 3. Search Returns All Historical Versions by Default
Without `date=current`, search returns ALL versions including superseded. A section amended 5 times appears 5 times. **Always use `date=current` for current text.**

### 4. Search Caps at 10,000 Results
Use hierarchy filters (`hierarchy[title]`, `hierarchy[part]`) to narrow. `per_page` max is 5000; values 9999+ return HTTP 400.

### 5. Search Order Only Supports "relevance"
No `newest`, `oldest`, or `date` ordering.

### 6. CFR Hierarchy
```
Title > Subtitle > Chapter > Subchapter > Part > Subpart > Subject Group > Section > Appendix
```
Title 48: Chapter 1 = FAR (Parts 1-99), Chapter 2 = DFARS (Parts 200-299). Full chapter map in REFERENCE.md.

### 7. Structure Endpoint Does Not Support Section Filtering
Use part or subpart filters. Section-level filtering returns HTTP 400.

### 8. RFO Deviation Awareness
Many agencies have issued RFO (Revolutionary FAR Overhaul) class deviations that supersede codified FAR text for those agencies. The eCFR still shows the pre-RFO text. When citing FAR sections for a specific agency's contract action, check whether that agency has adopted an RFO deviation for the relevant Part before relying on codified text. Current agency adoption status: https://www.acquisition.gov/far-overhaul/far-part-deviation-guide

---

## API Architecture

| Group | Base Path | Purpose |
|-------|-----------|---------|
| Admin | `/api/admin/v1/` | Agencies, corrections |
| Versioner | `/api/versioner/v1/` | Titles, structure, content, versions, ancestry |
| Search | `/api/search/v1/` | Full-text search with hierarchy filters |

---

## Core Functions

### Get Latest Available Date (USE BEFORE EVERY VERSIONER CALL)

```python
import urllib.request, json

def get_latest_date(title_number=48):
    """Get the most recent available date for a CFR title.
    ALWAYS use this instead of datetime.date.today() for versioner calls.
    """
    url = "https://www.ecfr.gov/api/versioner/v1/titles.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode())
    title = next(t for t in data["titles"] if t["number"] == title_number)
    return title["up_to_date_as_of"]
```

### Get Full Content (PRIMARY WORKHORSE)

**Endpoint:** `GET /api/versioner/v1/full/{date}/title-{number}.xml`

Returns XML only. Specify section-level when possible to keep response size manageable.

```python
import urllib.parse

def get_content(title_number, date=None, part=None, subpart=None,
                section=None, chapter=None):
    """Retrieve CFR regulatory text as XML."""
    if date is None:
        date = get_latest_date(title_number)
    url = f"https://www.ecfr.gov/api/versioner/v1/full/{date}/title-{title_number}.xml"
    params = []
    if chapter: params.append(("chapter", chapter))
    if part: params.append(("part", part))
    if subpart: params.append(("subpart", subpart))
    if section: params.append(("section", section))
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read().decode()
```

### Parse XML to Clean Text

```python
import re

def extract_section_text(xml_content):
    """Extract clean text from eCFR XML."""
    text = re.sub(r'<\?xml[^>]+\?>', '', xml_content)
    head_match = re.search(r'<HEAD>(.*?)</HEAD>', text)
    heading = head_match.group(1) if head_match else ""
    cita_match = re.findall(r'<CITA[^>]*>(.*?)</CITA>', text, re.DOTALL)
    citations = [re.sub(r'<[^>]+>', '', c).strip() for c in cita_match]
    paragraphs = re.findall(r'<P>(.*?)</P>', text, re.DOTALL)
    clean_paragraphs = []
    for p in paragraphs:
        p = re.sub(r'<I>(.*?)</I>', r'*\1*', p)
        p = re.sub(r'<E[^>]*>(.*?)</E>', r'*\1*', p)
        p = re.sub(r'<[^>]+>', '', p)
        p = p.strip()
        if p:
            clean_paragraphs.append(p)
    return {"heading": heading, "paragraphs": clean_paragraphs, "citations": citations}
```

### Get Title Structure (Table of Contents)

**Endpoint:** `GET /api/versioner/v1/structure/{date}/title-{number}.json`

```python
def get_structure(title_number, date=None, chapter=None, subchapter=None,
                  part=None, subpart=None):
    """Get hierarchical structure (TOC). Does NOT support section filtering."""
    if date is None:
        date = get_latest_date(title_number)
    url = f"https://www.ecfr.gov/api/versioner/v1/structure/{date}/title-{title_number}.json"
    params = []
    if chapter: params.append(f"chapter={chapter}")
    if subchapter: params.append(f"subchapter={subchapter}")
    if part: params.append(f"part={part}")
    if subpart: params.append(f"subpart={subpart}")
    if params:
        url += "?" + "&".join(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())
```

### Get Version History

**Endpoint:** `GET /api/versioner/v1/versions/title-{number}`

```python
def get_versions(title_number, part=None, section=None, subpart=None):
    """Get version history. 'substantive' field = True means text changed."""
    url = f"https://www.ecfr.gov/api/versioner/v1/versions/title-{title_number}"
    params = []
    if part: params.append(("part", part))
    if section: params.append(("section", section))
    if subpart: params.append(("subpart", subpart))
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())
```

### Get Ancestry (Breadcrumb Path)

**Endpoint:** `GET /api/versioner/v1/ancestry/{date}/title-{number}.json`

```python
def get_ancestry(title_number, date=None, part=None, section=None):
    """Get ancestor hierarchy path (title > chapter > subchapter > part)."""
    if date is None:
        date = get_latest_date(title_number)
    url = f"https://www.ecfr.gov/api/versioner/v1/ancestry/{date}/title-{title_number}.json"
    params = []
    if part: params.append(("part", part))
    if section: params.append(("section", section))
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### Full-Text Search

**Endpoint:** `GET /api/search/v1/results`

```python
def search_ecfr(query, title=None, chapter=None, part=None, subpart=None,
                section=None, date="current", last_modified_after=None,
                last_modified_before=None, per_page=20, page=1):
    """Search eCFR content. Use date='current' for only in-effect versions."""
    params = [("query", query)]
    if title: params.append(("hierarchy[title]", str(title)))
    if chapter: params.append(("hierarchy[chapter]", str(chapter)))
    if part: params.append(("hierarchy[part]", str(part)))
    if subpart: params.append(("hierarchy[subpart]", str(subpart)))
    if section: params.append(("hierarchy[section]", str(section)))
    if date: params.append(("date", date))
    if last_modified_after: params.append(("last_modified_on_or_after", last_modified_after))
    if last_modified_before: params.append(("last_modified_on_or_before", last_modified_before))
    params.append(("per_page", str(per_page)))
    params.append(("page", str(page)))
    url = f"https://www.ecfr.gov/api/search/v1/results?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### List Agencies

**Endpoint:** `GET /api/admin/v1/agencies.json`

```python
def get_agencies():
    """Get all agencies with CFR title/chapter references."""
    url = "https://www.ecfr.gov/api/admin/v1/agencies.json"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

### Get Corrections

**Endpoint:** `GET /api/admin/v1/corrections.json?title={number}`

```python
def get_corrections(title_number):
    """Get editorial corrections for a CFR title."""
    url = f"https://www.ecfr.gov/api/admin/v1/corrections.json?title={title_number}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode())
```

---

## Quick Workflow: Look Up a FAR Clause

```python
def lookup_far_clause(section_id, date=None):
    """Most common use case: get current text of a FAR clause."""
    if date is None:
        date = get_latest_date(48)
    xml_content = get_content(title_number=48, date=date, section=section_id)
    return extract_section_text(xml_content)
```

For DFARS: same pattern, sections use 2xx numbering (e.g., 252.227-7014).

---

## Rate Limiting and Best Practices

1. No authentication required; fully public API
2. No official rate limit; add 0.2-0.3s delays in batch operations
3. Request the smallest scope possible (section > subpart > part)
4. Use `date=current` in search unless you need historical versions
5. Timeouts: 15s for search/metadata, 30s for structure, 60s for full content
6. Versions go back to January 2017 only
7. XML `hierarchy_metadata` attributes contain `alternate_reference` (e.g., "FAR 15.305")

---

## Additional Resources

For response schemas, composite workflows (compare versions, list sections, find recent changes, search definitions), the full Title 48 chapter map, common FAR section reference, and troubleshooting: `view` the **REFERENCE.md** file in this skill directory.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*