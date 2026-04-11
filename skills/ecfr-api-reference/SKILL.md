---
name: ecfr-api-reference
description: Reference file for the eCFR API skill. Do not trigger directly. Contains response schemas, composite workflows, Title 48 chapter map, common FAR section reference, and troubleshooting. Loaded on demand by the main ecfr-api skill.
---

# eCFR API Reference

Supplemental reference for the eCFR API skill. Load this file on demand when you need response schemas, composite workflows, reference tables, or troubleshooting.

## Table of Contents
1. Response Schemas
2. Composite Workflows
3. Title 48 Chapter Map
4. Common FAR Section Reference
5. Troubleshooting
6. Important Notes

---

## 1. Response Schemas

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

## 2. Composite Workflows

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

### Find Recently Changed FAR Parts (via versions endpoint, more comprehensive)

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

## 3. Title 48 Chapter Map

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

## 4. Common FAR Section Reference

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

## 5. Troubleshooting

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

## 6. Important Notes

1. **Not an official legal edition:** Editorial compilation maintained by OFR. For official citations, use annual CFR from GPO's govinfo.gov.
2. **Point-in-time coverage since January 2017:** Version tracking begins 2017; content from earlier exists but version-by-version history does not.
3. **Data freshness:** Updated daily, ~2 business days after Federal Register publication. Check `up_to_date_as_of`.
4. **Cross-reference with Federal Register:** `<CITA>` elements contain FR citations (e.g., `[88 FR 53764]`). Use those with the Federal Register skill.
5. **Alternate references:** Title 48 `hierarchy_metadata` includes `alternate_reference` (e.g., "FAR 15.305").
6. **DFARS and supplements:** All agency FAR supplements are in Title 48; use chapter parameter to scope queries.


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*