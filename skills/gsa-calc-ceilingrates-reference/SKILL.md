---
name: gsa-calc-ceilingrates-reference
description: >
  Reference file for the GSA CALC+ Ceiling Rates API skill. Do not trigger directly. Contains aggregation schemas, composite workflows (IGCE benchmarking, price reasonableness, vendor rate cards, SIN analysis), common SINs table, pagination, and troubleshooting. Loaded on demand by the main gsa-calc-ceilingrates skill.
---

# GSA CALC+ API Reference

Supplemental reference. Load on demand for workflows, schemas, and troubleshooting.

## Table of Contents
1. Aggregation Schemas
2. Composite Workflows
3. Common SINs
4. Pagination
5. Troubleshooting

---

## 1. Aggregation Schemas

### wage_stats (extended statistics)
```json
{"count": 10927, "min": 28.31, "max": 534.25, "avg": 155.17,
 "std_deviation": 52.09, "std_deviation_bounds": {"upper": 259.36, "lower": 50.99}}
```
`count` = TRUE record count (use over hits.total when relation="gte").

### histogram_percentiles
```json
{"values": {"10.0": 96.80, "25.0": 121.45, "30.0": 127.23, "35.0": 133.51,
  "50.0": 149.69, "65.0": 166.97, "70.0": 173.32, "75.0": 180.79, "90.0": 221.80}}
```
Use P50 here for median (not median_price; different interpolation). P25-P75 = IQR; P10/P90 = reasonable bounds.

### median_price
`{"values": {"50.0": 149.69}}` -- close to but not identical to histogram_percentiles P50.

### education_level_counts (normalized)
```json
{"buckets": [{"key": "AA", "doc_count": 2206}, {"key": "BA", "doc_count": 32183},
  {"key": "HS", "doc_count": 2102}, {"key": "MA", "doc_count": 1722},
  {"key": "PHD", "doc_count": 109}, {"key": "TEC", "doc_count": 21}]}
```
Prefer over raw `education_level` aggregation (which splits "BA"/"Bachelors" into separate buckets).

### Other aggregations
`business_size`, `worksite`, `security_clearance`, `min_years_experience`: standard term buckets.
`wage_histogram`: rate distribution histogram. `current_price`: price point buckets. `labor_category`: top term buckets.

---

## 2. Composite Workflows

### IGCE Rate Benchmarking

```python
def igce_benchmark(labor_category, education=None, min_exp=None, max_exp=None, business_size=None):
    """Get ceiling rate statistics for IGCE development."""
    filters = []
    if education: filters.append(f"education_level:{education}")
    if min_exp is not None and max_exp is not None:
        filters.append(f"experience_range:{min_exp},{max_exp}")
    elif min_exp is not None:
        filters.append(f"min_years_experience:{min_exp}")
    if business_size: filters.append(f"business_size:{business_size}")
    result = keyword_search(labor_category, page_size=100, filters=filters)
    aggs = result.get('aggregations', {})
    stats = aggs.get('wage_stats', {})
    percentiles = aggs.get('histogram_percentiles', {}).get('values', {})
    ed_counts = aggs.get('education_level_counts', {}).get('buckets', [])
    return {
        'labor_category': labor_category,
        'total_comparable_rates': stats.get('count', 0),
        'min_rate': stats.get('min'), 'max_rate': stats.get('max'),
        'avg_rate': round(stats.get('avg', 0), 2),
        'median_rate': percentiles.get('50.0'),
        'std_deviation': round(stats.get('std_deviation', 0), 2),
        'percentiles': {'p10': percentiles.get('10.0'), 'p25': percentiles.get('25.0'),
                        'p75': percentiles.get('75.0'), 'p90': percentiles.get('90.0')},
        'outlier_bounds': {'lower_2sigma': stats.get('std_deviation_bounds', {}).get('lower'),
                           'upper_2sigma': stats.get('std_deviation_bounds', {}).get('upper')},
        'education_breakdown': {b['key']: b['doc_count'] for b in ed_counts},
        'filters_applied': filters
    }
```

**When presenting results, include:** sample size, min/max/avg/median, P25-P75 range, std dev, filters used, and reminder these are ceiling rates.

### Price Reasonableness Check

```python
def price_reasonableness(labor_category, proposed_rate, education=None, experience_range=None, business_size=None):
    """Evaluate a proposed rate against GSA ceiling rate distribution."""
    benchmark = igce_benchmark(labor_category, education,
        experience_range[0] if experience_range else None,
        experience_range[1] if experience_range else None, business_size)
    if benchmark['total_comparable_rates'] == 0:
        return {'status': 'NO_DATA', 'message': 'No comparable rates found.'}
    avg, std, median = benchmark['avg_rate'], benchmark['std_deviation'], benchmark['median_rate']
    p25, p75 = benchmark['percentiles'].get('p25'), benchmark['percentiles'].get('p75')
    z_score = round((proposed_rate - avg) / std, 2) if std > 0 else 0
    iqr_position = None
    if p25 and p75:
        if proposed_rate < p25: iqr_position = "below P25"
        elif proposed_rate <= p75: iqr_position = "within IQR (P25-P75)"
        else: iqr_position = "above P75"
    return {**benchmark, 'proposed_rate': proposed_rate, 'z_score': z_score,
        'vs_median': "below" if proposed_rate < median else "above",
        'iqr_position': iqr_position,
        'delta_from_avg': round(proposed_rate - avg, 2),
        'delta_from_avg_pct': round(((proposed_rate - avg) / avg) * 100, 1) if avg > 0 else None}
```

### Vendor Rate Card

```python
def vendor_rate_card(vendor_keyword, page_size=500):
    """Get all ceiling rates for a vendor. Discovers exact name first."""
    discovery = suggest_contains("vendor_name", vendor_keyword)
    if not discovery['suggestions']:
        return {'error': f'No vendor found matching "{vendor_keyword}".'}
    exact_name = discovery['suggestions'][0]['value']
    result = exact_search("vendor_name", exact_name, page_size=page_size, ordering="labor_category", sort="asc")
    rates = [{'labor_category': h['_source']['labor_category'], 'rate': h['_source']['current_price'],
              'education': h['_source']['education_level'], 'experience': h['_source']['min_years_experience'],
              'sin': h['_source']['sin'], 'contract': h['_source']['idv_piid']}
             for h in result.get('hits', {}).get('hits', [])]
    return {'vendor': exact_name, 'total_categories': result['hits']['total']['value'], 'rates': rates}
```

### Multi-Category IGCE Builder

```python
import time

def build_igce(labor_categories, education=None, experience_range=None, business_size=None):
    """Build IGCE benchmarks for multiple labor categories."""
    igce = {}
    for cat in labor_categories:
        try:
            igce[cat] = igce_benchmark(cat, education=education,
                min_exp=experience_range[0] if experience_range else None,
                max_exp=experience_range[1] if experience_range else None,
                business_size=business_size)
        except Exception as e:
            igce[cat] = {'error': str(e)}
        time.sleep(0.3)
    return igce
```

### SIN-Based Market Analysis

```python
def sin_analysis(sin_code, page_size=100):
    """Get rate distribution for a specific SIN."""
    result = filtered_browse(filters=[f"sin:{sin_code}"], page_size=page_size)
    aggs = result.get('aggregations', {})
    stats = aggs.get('wage_stats', {})
    percentiles = aggs.get('histogram_percentiles', {}).get('values', {})
    ed_counts = aggs.get('education_level_counts', {}).get('buckets', [])
    biz_buckets = aggs.get('business_size', {}).get('buckets', [])
    return {'sin': sin_code, 'total_rates': stats.get('count', 0),
        'rate_stats': {'min': stats.get('min'), 'max': stats.get('max'),
            'avg': round(stats.get('avg', 0), 2), 'median': percentiles.get('50.0'),
            'std_dev': round(stats.get('std_deviation', 0), 2),
            'p25': percentiles.get('25.0'), 'p75': percentiles.get('75.0'),
            'p10': percentiles.get('10.0'), 'p90': percentiles.get('90.0')},
        'education_breakdown': {b['key']: b['doc_count'] for b in ed_counts},
        'business_size_breakdown': {b['key']: b['doc_count'] for b in biz_buckets}}
```

---

## 3. Common SINs for Professional Services

| SIN | Description |
|-----|-------------|
| 54151S | IT Professional Services |
| 541611 | Management and Financial Consulting |
| 541715 | Engineering Research and Development |
| 541330ENG | Engineering Services |
| 541519 | Other Computer Related Services |
| 541690 | Other Scientific and Technical Consulting |
| 561210FAC | Facilities Maintenance and Management |
| 541511 | Custom Computer Programming |
| 541512 | Computer Systems Design |
| 541513 | Computer Facilities Management |
| 541610 | Management Consulting |
| 611430 | Training |

---

## 4. Pagination

Max `page_size` = 500. Always include `page` and `page_size`.

```python
def paginate_all(keyword, filters=None, page_size=500):
    """Retrieve all results by paginating."""
    all_hits, page = [], 1
    while True:
        result = keyword_search(keyword, page=page, page_size=page_size, filters=filters)
        hits = result.get('hits', {}).get('hits', [])
        all_hits.extend(hits)
        total_info = result['hits']['total']
        total = (result.get('aggregations', {}).get('wage_stats', {}).get('count', total_info['value'])
                 if total_info['relation'] == 'gte' else total_info['value'])
        if len(all_hits) >= total or not hits: break
        page += 1
        time.sleep(0.3)
    return all_hits, result.get('aggregations', {})
```

---

## 5. Troubleshooting

| Problem | Cause | Fix |
|---------|-------|-----|
| 0 results for known labor category | Using exact match with inexact title | Use `keyword=` or `suggest-contains` first |
| 0 results for known vendor | Name variation | Use `suggest-contains=vendor_name:partial` to discover exact string |
| Inconsistent education values | Vendor PPT data quality | Use `education_level_counts` aggregation |
| `hits.total.relation` = "gte" | >10,000 results | Use `wage_stats.count` for true total; add filters to narrow |
| Suggest-contains returns empty | 1-char search term | Minimum 2 characters |
| Stats seem wrong | Outliers skewing averages | Use `exclude` parameter or rely on median/percentiles |
| CSV starts with junk rows | Metadata header before data | Skip to line starting with "Contract #," |


---

*MIT © James Jenrette / 1102tools. Source: github.com/1102tools/federal-contracting-skills*