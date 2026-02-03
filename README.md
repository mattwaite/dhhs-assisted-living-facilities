# Nebraska Assisted Living Facilities

A repository tracking assisted living facilities in Nebraska, parsed from monthly DHHS rosters.

## About the Data

Nebraska DHHS publishes a [PDF roster of licensed Assisted Living Facilities](https://dhhs.ne.gov/licensure/Documents/ALF%20Roster.pdf) that is updated monthly. This repository automatically downloads and parses that PDF into machine-readable CSV format.

### Data Fields

| Field | Description |
|-------|-------------|
| `roster_date` | Date the roster was published (YYYY-MM-DD) |
| `town` | City where facility is located |
| `county` | Nebraska county |
| `zip_code` | 5-digit ZIP code |
| `facility_name` | Name of the assisted living facility |
| `address` | Street address |
| `phone` | Phone number |
| `fax` | Fax number |
| `licensee` | Licensed operator/organization |
| `administrator` | Facility administrator |
| `facility_type` | License type (ALF) |
| `license_number` | State license number (ALF###) |
| `total_beds` | Total licensed beds |
| `services` | Services offered (e.g., AGED/DISABLED, MED WVR, CER) |
| `accreditation` | Accreditation status |
| `care_of_address` | Mailing address if different |

## Using the Data

### Download Latest CSV

The most recent data is available in the `data/` directory:

```
data/alf_roster_YYYY-MM-DD.csv
```

### Direct Link

You can access the raw CSV directly via GitHub:

```
https://raw.githubusercontent.com/mattwaite/dhhs-assisted-living-facilities/main/data/alf_roster_YYYY-MM-DD.csv
```

## Automated Updates

A GitHub Actions workflow runs on the 15th of each month to:

1. Download the latest PDF from Nebraska DHHS
2. Parse facility data using `pdfplumber`
3. Validate extraction with automated tests
4. Commit the new PDF and CSV to the repository

The workflow can also be triggered manually from the Actions tab.

## Local Development

### Requirements

- Python 3.11+
- pdfplumber
- pytest (for testing)

### Installation

```bash
pip install pdfplumber pytest
```

### Running the Extractor

```bash
# Basic usage
python extract_alf_roster.py "ALF Roster.pdf"

# With options
python extract_alf_roster.py input.pdf -o output.csv --skip-pages 2 --date 2025-01-15
```

### Running Tests

```bash
pytest test_extract_alf_roster.py -v
```

Tests validate:
- Expected facility count (~278 facilities)
- Required field population rates
- Data format validation (ZIP codes, license numbers, phone numbers)

## Project Structure

```
.
├── data/                    # Versioned CSV output files
├── pdfs/                    # Archived PDF downloads
├── extract_alf_roster.py    # Main extraction script
├── test_extract_alf_roster.py  # Validation tests
└── .github/workflows/       # Automated monthly update workflow
```

## Data Source

Nebraska Department of Health and Human Services
Division of Public Health - Licensure Unit
https://dhhs.ne.gov/Pages/Assisted-Living-Facilities.aspx

## License

MIT License - see [LICENSE](LICENSE)
