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

This skill is self-contained. Composite workflows, response schemas, Title 48 chapter map, common FAR section reference, and troubleshooting are all below.

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
Title 48: Chapter 1 = FAR (Parts 1-99), Chapter 2 = DFARS (Parts 200-299). Full chapter map below.

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

## Response Schemas

### Titles Endpoint Response
```json
{"titles": [{"number": 48, "name": "Federal Acquisition Regulations System",
  "latest_amended_on": "2026-01-17", "latest_issue_date": "2026-01-17",
  "up_to_date_as_of": "2026-03-05", "reserved": false}]}
```

### Agencies Endpoint Response
```json
{"agencies": [{"name": "Federal Acquisition Regulatory Council", "slug": "federal-acquisition-regulation",
  "children": [], "cfr_references": [{"title": 48, "chapter": "1"}]}]}
```

### Structure Endpoint Response (nested tree)
Key fields per node: `identifier`, `type` (title/chapter/subchapter/part/subpart/section), `label_description`, `size` (bytes), `children[]`, `received_on` (sections only).

### Content XML Structure
- `DIV` elements with `TYPE` attributes: `DIV1 TYPE="TITLE"`, `DIV5 TYPE="PART"`, `DIV8 TYPE="SECTION"`
- Text in `<P>` (paragraph), `<I>` (italic), `<E>` (emphasis), `<EXTRACT>` (clause text blocks)
- Citations in `<CITA>` elements (e.g., `[48 FR 42103, Sept. 19, 1983]`)
- `hierarchy_metadata` attribute contains citation, path, and `alternate_reference` (e.g., "FAR 15.305")

### Versions Endpoint Response
```json
{"content_versions": [{"date": "2023-11-06", "amendment_date": "2023-11-06",
  "identifier": "52.212-4", "part": "52", "substantive": true, "removed": false,
  "subpart": "52.2", "title": "48", "type": "section"}]}
```

### Ancestry Endpoint Response
```json
{"ancestors": [{"identifier": "48", "type": "title"}, {"identifier": "1", "type": "chapter",
  "descendant_range": "1 - 99"}, {"identifier": "15", "type": "part",
  "label_description": "Contracting by Negotiation"}]}
```

### Search Endpoint Response
Key fields per result: `starts_on`, `ends_on` (null = currently active), `type`, `hierarchy{}`, `hierarchy_headings{}`, `headings{}` (contains `<strong>` tags around matches), `full_text_excerpt`, `score`, `change_types[]`. Meta: `current_page`, `total_pages`, `total_count`, `max_score`.

Search notes:
- `headings` and `full_text_excerpt` contain HTML `<strong>` tags; strip before displaying
- `change_types`: `"initial"`, `"effective"`, `"cross_reference"`, `"effective_cross_reference"`, `"withdrawn"`

### Corrections Endpoint Response
```json
{"ecfr_corrections": [{"cfr_references": [{"cfr_reference": "48 CFR 13.003",
  "hierarchy": {"title": "48", "part": "13", "section": "13.003"}}],
  "corrective_action": "(g)(2) amended", "error_corrected": "2005-09-27",
  "fr_citation": "69 FR 59699", "title": 48}]}
```

---

## Composite Workflows

### Extract Hierarchy Metadata from XML

```python
def extract_hierarchy_metadata(xml_content):
    """Extract hierarchy_metadata JSON from XML (contains alternate_reference like 'FAR 15.305')."""
    import re, json
    matches = re.findall(r'hierarchy_metadata="([^"]+)"', xml_content)
    metadata = []
    for m in matches:
        cleaned = m.replace('&quot;', '"').replace('&amp;quot;', '"')
        try:
            metadata.append(json.loads(cleaned))
        except json.JSONDecodeError:
            continue
    return metadata
```

### Compare a Section at Two Points in Time

```python
def compare_section_versions(title_number, section_id, date_before, date_after):
    """Retrieve a section at two dates for comparison."""
    old_xml = get_content(title_number, date=date_before, section=section_id)
    new_xml = get_content(title_number, date=date_after, section=section_id)
    return {
        "section": section_id,
        "before": {"date": date_before, "content": extract_section_text(old_xml)},
        "after": {"date": date_after, "content": extract_section_text(new_xml)}
    }
```

### List All Sections in a FAR Part

```python
def list_sections_in_part(part_number, chapter="1", date=None):
    """List all sections in a FAR part with headings."""
    if date is None:
        date = get_latest_date(48)
    structure = get_structure(48, date=date, chapter=chapter, part=part_number)
    sections = []
    def walk(node):
        if node.get("type") == "section":
            sections.append({"identifier": node["identifier"],
                "description": node.get("label_description", ""),
                "size": node.get("size", 0), "received_on": node.get("received_on")})
        for child in node.get("children", []):
            walk(child)
    walk(structure)
    return sections
```

### Check When a Section Was Last Amended

```python
def last_amendment(title_number, section_id):
    """Find the most recent substantive amendment date."""
    data = get_versions(title_number, section=section_id)
    versions = data.get("content_versions", [])
    for v in versions:
        if v.get("substantive"):
            return {"section": section_id, "last_substantive_amendment": v["amendment_date"],
                "issue_date": v["issue_date"], "total_versions_since_2017": len(versions)}
    if versions:
        return {"section": section_id, "last_substantive_amendment": "Before 2017 (pre-eCFR tracking)",
            "oldest_tracked_version": versions[-1]["date"], "total_versions_since_2017": len(versions)}
    return {"section": section_id, "error": "No versions found"}
```

### Find Recently Changed FAR Sections

```python
def recently_changed_far_sections(since_date):
    """Find FAR sections modified since a given date using search API."""
    import time
    all_results, page = [], 1
    while True:
        data = search_ecfr(query="*", title="48", chapter="1", date="current",
            last_modified_after=since_date, per_page=200, page=page)
        results = data.get("results", [])
        all_results.extend(results)
        meta = data.get("meta", {})
        if page >= meta.get("total_pages", 0) or page * 200 >= 10000:
            break
        page += 1
        time.sleep(0.3)
    return {"since": since_date, "total_changed_sections": meta.get("total_count", len(all_results)),
        "sections": all_results}
```

### Find Recently Changed FAR Parts (via versions endpoint)

```python
def recently_changed_far_parts(since_date, parts=None):
    """Use versions endpoint for comprehensive change tracking across FAR parts."""
    import time
    if parts is None:
        parts = ["1","2","3","4","5","6","7","8","9","10","11","12","13","14","15","16",
                 "17","18","19","22","23","25","27","28","29","30","31","32","33","34",
                 "35","36","37","38","39","42","43","44","45","46","47","49","50","51","52","53"]
    changed = []
    for part_num in parts:
        data = get_versions(48, part=part_num)
        for v in data.get("content_versions", []):
            if v["date"] >= since_date and v.get("substantive"):
                changed.append({"section": v["identifier"], "name": v["name"],
                    "amendment_date": v["amendment_date"], "part": part_num})
        time.sleep(0.2)
    seen = set()
    unique = [c for c in changed if c["section"] not in seen and not seen.add(c["section"])]
    return {"since": since_date, "changed_sections": sorted(unique, key=lambda x: x["amendment_date"], reverse=True)}
```

### Search Across All of Title 48

```python
def search_title_48(query_term, current_only=True, per_page=50):
    """Search all of Title 48 (FAR + all supplements)."""
    return search_ecfr(query=query_term, title="48",
        date="current" if current_only else None, per_page=per_page)
```

### Get a FAR Definition from 2.101

FAR 2.101 is large (~109KB XML). Fetch the full section and search within it.

```python
def get_far_definition(term, date=None):
    """Search for a term's definition in FAR 2.101."""
    if date is None:
        date = get_latest_date(48)
    xml = get_content(48, date=date, section="2.101")
    parsed = extract_section_text(xml)
    matching = []
    term_lower = term.lower()
    for i, para in enumerate(parsed["paragraphs"]):
        if term_lower in para.lower():
            start, end = max(0, i - 1), min(len(parsed["paragraphs"]), i + 3)
            matching.append({"paragraph_index": i, "context": parsed["paragraphs"][start:end]})
    return {"section": "2.101", "search_term": term, "matches": matching,
        "total_paragraphs": len(parsed["paragraphs"])}
```

---

## Title 48 Chapter Map

| Ch | Parts | Regulation |
|----|-------|------------|
| 1 | 1-99 | FAR |
| 2 | 200-299 | DFARS |
| 3 | 300-399 | HHSAR (HHS) |
| 4 | 400-499 | AGAR (Agriculture) |
| 5 | 500-599 | GSAR (GSA) |
| 6 | 600-699 | DOSAR (State) |
| 7 | 700-799 | AIDAR (USAID) |
| 8 | 800-899 | VAAR (VA) |
| 9 | 900-999 | DEAR (Energy) |
| 10 | 1000-1099 | DTAR (Treasury) |
| 12 | 1200-1299 | TAR (Transportation) |
| 13 | 1300-1399 | CAR (Commerce) |
| 14 | 1400-1499 | DIAR (Interior) |
| 15 | 1500-1599 | EPAAR (EPA) |
| 16 | 1600-1699 | OPMAR (OPM) |
| 18 | 1800-1899 | NFS (NASA) |
| 20 | 2000-2099 | NRCAR (NRC) |
| 23 | 2300-2399 | SSAAR (SSA) |
| 24 | 2400-2499 | HUDAR (HUD) |
| 25 | 2500-2599 | NSFAR (NSF) |
| 28 | 2800-2899 | JAR (Justice) |
| 29 | 2900-2999 | DOLAR (Labor) |
| 99 | 9900 | CAS (Cost Accounting Standards) |

---

## Common FAR Section Reference

| Section | Description |
|---------|-------------|
| 2.101 | Definitions (master definition section) |
| 4.1102 | SAM policy |
| 6.302-1 to 6.302-7 | Justifications for other than full and open competition |
| 8.405-1 | Ordering procedures for supplies and services not requiring a statement of work |
| 8.405-2 | Ordering procedures for services requiring a statement of work |
| 9.104-1 | General standards of responsibility |
| 9.406-2 | Causes for debarment |
| 12.301 | Solicitation provisions/clauses for commercial acquisitions |
| 13.003 | Policy for simplified acquisition procedures |
| 15.305 | Proposal evaluation |
| 15.306 | Exchanges with offerors after receipt of proposals |
| 19.502-2 | Total small business set-asides |
| 31.205 | Selected costs (allowability) |
| 33.103 | Protests to the agency |
| 42.302 | Contract administration functions |
| 52.212-1 | Instructions to Offerors (Commercial) |
| 52.212-4 | Contract Terms and Conditions (Commercial) |
| 52.212-5 | Contract Terms and Conditions Required (Commercial) |

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

## Troubleshooting

| Problem | Fix |
|---------|-----|
| HTTP 404 from versioner | Date exceeds `up_to_date_as_of`; use `get_latest_date()` |
| HTTP 406 from content | Requested `.json`; use `.xml` only |
| HTTP 404 with "current" | No `current` keyword; use specific date from `get_latest_date()` |
| Search returns duplicates | Missing `date=current` |
| 10,000+ results | Add hierarchy filters |
| Huge XML response | Narrow to section or subpart level |
| Empty results for known section | Date is before section existed; use more recent date |
| HTTP 400 from structure with section filter | Section filtering not supported; use part/subpart |
| `_SUBSTITUTE_DATE_` in metadata | Replace with the actual date used in request |
| `&#x2014;` in text | XML entities; decode with `html.unescape()` |
| Versions only go back to 2017 | Pre-2017 history not available via this API |
| Stale `up_to_date_as_of` | NARA shutdown or processing lag; check for government shutdowns |
| `order=newest` fails | Only `relevance` supported |
| `last_modified_after` rejected | Use `last_modified_on_or_after` (with `on_or_`) |

---

## Important Notes

1. **Not an official legal edition:** Editorial compilation maintained by OFR. For official citations, use annual CFR from GPO's govinfo.gov.
2. **Point-in-time coverage since January 2017:** Version tracking begins 2017; content from earlier exists but version-by-version history does not.
3. **Data freshness:** Updated daily, ~2 business days after Federal Register publication. Check `up_to_date_as_of`.
4. **Cross-reference with Federal Register:** `<CITA>` elements contain FR citations (e.g., `[88 FR 53764]`). Use those with the Federal Register skill.
5. **Alternate references:** Title 48 `hierarchy_metadata` includes `alternate_reference` (e.g., "FAR 15.305").
6. **DFARS and supplements:** All agency FAR supplements are in Title 48; use chapter parameter to scope queries.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*
