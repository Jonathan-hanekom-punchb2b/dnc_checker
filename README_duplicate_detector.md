# HubSpot Duplicate Company Detector

This tool helps identify potential duplicate companies in HubSpot exports using intelligent domain matching and fuzzy name comparison algorithms.

## Quick Start - Duplicate Detection

### 1. Export Companies from HubSpot
- Export all companies from HubSpot as CSV
- Ensure the CSV includes columns: `Company Name`, `Company Domain Name`
- Save the file as `hubspot_companies.csv` in the project folder

### 2. Run Duplicate Detection
```bash
# With default file names
python duplicate_detector.py

# With custom file names
python duplicate_detector.py --input my_companies.csv --output results.csv
```

### 3. Review Results
- Upload the output CSV to Google Drive
- Open in Google Sheets
- Filter by `duplicate_flag = "Yes"` to see potential duplicates
- Review flagged companies and manually merge in HubSpot

## Output Columns

The script adds these columns to your original data:

| Column | Description | Example |
|--------|-------------|---------|
| `duplicate_flag` | Yes/No indicator | `Yes` |
| `confidence_score` | Match confidence (0-100%) | `95` |
| `cluster_id` | Groups related duplicates | `CLUSTER_001` |
| `potential_matches` | List of similar companies | `Acme Corp (acme.co.uk) [92%]` |
| `match_reason` | Why flagged as duplicate | `Same base domain: acme + Similar names (88%)` |
| `review_priority` | Recommended review order | `High` |

## Understanding Match Confidence

### High Priority (90-100%)
- Very likely duplicates - start here
- Exact domain matches with similar names
- Same base domain (e.g., bbc.com vs bbc.co.uk)

### Medium Priority (70-89%)
- Probable duplicates - review carefully
- Similar domains with similar names
- May need manual verification

### Low Priority (50-69%)
- Possible duplicates - spot check
- Fuzzy matches requiring human judgment
- Higher chance of false positives

## Duplicate Detection Algorithm

The system uses multi-factor matching:

1. **Domain Analysis**
   - Handles country TLDs (`.com` vs `.co.uk`)
   - Removes subdomains (`www`, `shop`, etc.)
   - Extracts base company identifier

2. **Name Matching**
   - Reuses existing company name cleaning logic
   - Fuzzy matching with token sorting
   - Removes common suffixes (Inc, LLC, Corp, etc.)

3. **Combined Scoring**
   - Weighted combination of domain + name similarity
   - Domain matching weighted higher (60%) than name (40%)
   - Special bonuses for exact domain matches

## Cluster Grouping

Related duplicates are grouped into clusters:
- `CLUSTER_001`: Companies A, B, C are all similar to each other
- `CLUSTER_002`: Companies D, E are similar to each other
- Helps identify complex duplicate relationships

## Files Created

- `hubspot_companies_with_duplicates.csv` - Main results file
- `hubspot_companies_with_duplicates_summary.txt` - Analysis report

## Example Workflow

1. **Export** → Download companies from HubSpot
2. **Detect** → `python duplicate_detector.py`
3. **Review** → Open results in Google Sheets
4. **Filter** → Show only `duplicate_flag = "Yes"` 
5. **Prioritize** → Start with `review_priority = "High"`
6. **Merge** → Use HubSpot UI to merge confirmed duplicates

## Common Duplicate Patterns Detected

- **Domain Variations**: `company.com` vs `company.co.uk`
- **Subdomain Differences**: `www.company.com` vs `shop.company.com`
- **Name Variations**: `Acme Inc` vs `Acme Corporation`
- **Typos**: `Gogle Inc` vs `Google Inc`
- **Abbreviations**: `IBM Corp` vs `International Business Machines`

## Tips for Best Results

1. **Clean Your Export**: Remove test companies before running
2. **Review High Priority First**: These are most likely true duplicates
3. **Check Business Context**: Same company, different divisions may be intentional
4. **Verify Before Merging**: Always confirm in HubSpot before merging
