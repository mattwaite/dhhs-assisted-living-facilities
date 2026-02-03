# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This project extracts Nebraska Assisted Living Facility (ALF) data from monthly DHHS PDF rosters and converts them to CSV format. The source PDF ("ALF Roster.pdf") is published by Nebraska DHHS and contains ~278 facility records.

## Commands

**Run extraction:**
```bash
python extract_alf_roster.py                    # Uses default "ALF Roster.pdf" → "alf_roster.csv"
python extract_alf_roster.py input.pdf -o out.csv --skip-pages 2
python extract_alf_roster.py input.pdf -o out.csv --date 2025-01-15  # Include roster date
```

**Run tests:**
```bash
pytest                                          # Run all tests
pytest test_extract_alf_roster.py -v           # Verbose output
pytest test_extract_alf_roster.py::TestParsePageText -v  # Single test class
```

**Dependencies:**
```bash
pip install pdfplumber pytest
```

## Architecture

Single-module extraction pipeline in `extract_alf_roster.py`:

1. `extract_facilities_from_pdf()` - Opens PDF, iterates pages (skipping cover/summary pages), calls parser
2. `parse_page_text()` - Regex-based parser that identifies facility records by the location header pattern: `TOWN (COUNTY) - ZIPCODE ALF SERVICES`
3. `facilities_to_csv()` - Writes extracted dictionaries to CSV

The parser handles multi-line records where each facility's data (name, address, phone, licensee, administrator, beds, services) spans several lines until the next location header.

## Data Fields

Extracted per facility: roster_date, town, county, zip_code, facility_name, address, phone, fax, licensee, administrator, facility_type, license_number (ALF###), total_beds, services, accreditation, care_of_address

## Testing Notes

- Tests require "ALF Roster.pdf" in the repo root (tests skip gracefully if missing)
- `TestParsePageText` contains unit tests with synthetic data that run without the PDF
- Data quality tests expect ~90% fill rates for core fields due to PDF parsing challenges

## Automated Monthly Updates

A GitHub Actions workflow (`.github/workflows/update-roster.yml`) runs on the 15th of each month to:
1. Download the latest PDF from Nebraska DHHS
2. Save it to `pdfs/alf_roster_YYYY-MM-DD.pdf`
3. Parse and export to `data/alf_roster_YYYY-MM-DD.csv`
4. Commit and push changes

The workflow can also be triggered manually via the GitHub Actions UI.

## Directory Structure

- `data/` - Versioned CSV output files (tracked in git)
- `pdfs/` - Archived PDF downloads (tracked in git)
- Root `ALF Roster.pdf` and `alf_roster.csv` are gitignored for local development
