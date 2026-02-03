"""
Nebraska Assisted Living Facility Roster PDF Extractor

Extracts facility data from the Nebraska ALF Roster PDF and outputs to CSV.
"""

import re
import csv
from pathlib import Path
from typing import List, Dict, Optional

try:
    import pdfplumber
except ImportError:
    raise ImportError("Please install pdfplumber: pip install pdfplumber")


def extract_facilities_from_pdf(pdf_path: str, skip_pages: int = 2, roster_date: Optional[str] = None) -> List[Dict]:
    """
    Extract assisted living facility records from the Nebraska ALF Roster PDF.

    Args:
        pdf_path: Path to the PDF file
        skip_pages: Number of pages to skip at the beginning (default 2)
        roster_date: Date string (YYYY-MM-DD) to include in each record

    Returns:
        List of dictionaries containing facility data
    """
    facilities = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            # Skip the first N pages (cover and summary)
            if page_num < skip_pages:
                continue

            text = page.extract_text()
            if not text:
                continue

            # Parse facilities from this page
            page_facilities = parse_page_text(text, roster_date)
            facilities.extend(page_facilities)

    return facilities


def parse_page_text(text: str, roster_date: Optional[str] = None) -> List[Dict]:
    """
    Parse a page of text to extract facility records.

    Each facility record follows a pattern starting with:
    TOWN (COUNTY) - ZIPCODE ALF SERVICES

    Args:
        text: The text content of a PDF page
        roster_date: Optional date string (YYYY-MM-DD) to include in each record
    """
    facilities = []
    lines = text.split('\n')

    # Pattern to identify the start of a facility record
    # Format: TOWN (COUNTY) - ZIPCODE ALF [SERVICES]
    location_pattern = re.compile(
        r'^([A-Z][A-Z\'\s]+?)\s*\(([A-Z\s]+)\)\s*-\s*(\d{5})\s+ALF\s*(.*)?$'
    )

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Check if this line starts a new facility record
        match = location_pattern.match(line)
        if match:
            # Found start of a facility record
            facility = {
                'town': match.group(1).strip(),
                'county': match.group(2).strip(),
                'zip_code': match.group(3).strip(),
                'facility_name': '',
                'address': '',
                'phone': '',
                'fax': '',
                'licensee': '',
                'administrator': '',
                'facility_type': 'ALF',
                'license_number': '',
                'total_beds': '',
                'services': match.group(4).strip() if match.group(4) else '',
                'accreditation': '',
                'care_of_address': '',
                'roster_date': roster_date or ''
            }

            i += 1

            # Continue parsing subsequent lines until next facility or end
            while i < len(lines):
                next_line = lines[i].strip()

                # Check if this is the start of a new facility
                if location_pattern.match(next_line):
                    break

                # Skip header lines
                if 'ASSISTED LIVING FACILITY ROSTER' in next_line:
                    i += 1
                    continue
                if next_line.startswith('TOWN') and 'Zip Code' in next_line:
                    i += 1
                    continue
                if next_line.startswith('Name of Facility'):
                    i += 1
                    continue
                if next_line.startswith('Administration'):
                    i += 1
                    continue

                # Parse "Total Lic - XX" line
                beds_match = re.search(r'Total\s+Lic\s*-\s*(\d+)', next_line)
                if beds_match:
                    facility['total_beds'] = beds_match.group(1)
                    # Check for additional services on same line
                    remainder = re.sub(r'Total\s+Lic\s*-\s*\d+', '', next_line).strip()
                    if remainder and 'NURSING' in remainder or 'ALZHEIMER' in remainder or 'MEMORY' in remainder:
                        if facility['services']:
                            facility['services'] += '; ' + remainder
                        else:
                            facility['services'] = remainder
                    i += 1
                    continue

                # Parse facility name + license number line
                license_match = re.search(r'(ALF\d{3})', next_line)
                if license_match and not facility['license_number']:
                    facility['license_number'] = license_match.group(1)
                    # Facility name is everything before the license number
                    name_part = next_line.split(license_match.group(1))[0].strip()
                    if name_part and not facility['facility_name']:
                        facility['facility_name'] = name_part
                    i += 1
                    continue

                # Parse phone/fax line
                phone_match = re.search(r'\((\d{3})\)\s*(\d{3})-(\d{4})', next_line)
                if phone_match and not facility['phone']:
                    facility['phone'] = f"({phone_match.group(1)}) {phone_match.group(2)}-{phone_match.group(3)}"
                    fax_match = re.search(r'FAX:\s*\((\d{3})\)\s*(\d{3})-(\d{4})', next_line)
                    if fax_match:
                        facility['fax'] = f"({fax_match.group(1)}) {fax_match.group(2)}-{fax_match.group(3)}"
                    i += 1
                    continue

                # Parse administrator line
                if 'ADMINISTRATOR' in next_line.upper():
                    admin_match = re.match(r'^([^,]+),\s*(ADMINISTRATOR|PROVISIONAL ADM)', next_line, re.IGNORECASE)
                    if admin_match:
                        facility['administrator'] = admin_match.group(1).strip()
                    i += 1
                    continue

                # Parse c/o address
                if next_line.lower().startswith('c/o:'):
                    facility['care_of_address'] = next_line[4:].strip()
                    i += 1
                    continue

                # Parse services that might appear on their own line
                if any(svc in next_line for svc in ['AGED/DISABLED', 'ALZHEIMER', 'MEMORY CARE', 'COMPLEX NURSING']):
                    if facility['services']:
                        facility['services'] += '; ' + next_line
                    else:
                        facility['services'] = next_line
                    i += 1
                    continue

                # Parse accreditation
                if next_line == 'CARF':
                    facility['accreditation'] = next_line
                    i += 1
                    continue

                # Parse address (has numbers or street keywords)
                if (re.search(r'^\d+\s+\w+|BOX\s+\d+', next_line, re.IGNORECASE) or
                    re.search(r'STREET|AVENUE|AVE|DRIVE|DR|ROAD|RD|LANE|LN|COURT|CT|CIRCLE|PLAZA|BLVD|WAY|PKWY', next_line, re.IGNORECASE)):
                    if not facility['address']:
                        facility['address'] = next_line
                    i += 1
                    continue

                # Parse licensee (remaining non-empty lines before admin)
                if (next_line and
                    not facility['licensee'] and
                    not next_line.startswith('Page ') and
                    not re.match(r'^\d+$', next_line) and
                    len(next_line) > 3):
                    # Could be licensee or facility name if we don't have it yet
                    if not facility['facility_name']:
                        facility['facility_name'] = next_line
                    else:
                        facility['licensee'] = next_line
                    i += 1
                    continue

                i += 1

            # Add the facility if we have at least a name
            if facility.get('facility_name') or facility.get('license_number'):
                facilities.append(facility)
        else:
            i += 1

    return facilities


def facilities_to_csv(facilities: List[Dict], output_path: str) -> None:
    """
    Write facility data to a CSV file.
    """
    if not facilities:
        raise ValueError("No facilities to write")

    fieldnames = [
        'roster_date', 'town', 'county', 'zip_code', 'facility_name', 'address',
        'phone', 'fax', 'licensee', 'administrator', 'facility_type',
        'license_number', 'total_beds', 'services', 'accreditation',
        'care_of_address'
    ]

    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(facilities)


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description='Extract Nebraska ALF Roster data from PDF to CSV'
    )
    parser.add_argument(
        'pdf_path',
        nargs='?',
        default='ALF Roster.pdf',
        help='Path to the PDF file (default: ALF Roster.pdf)'
    )
    parser.add_argument(
        '-o', '--output',
        default='alf_roster.csv',
        help='Output CSV file path (default: alf_roster.csv)'
    )
    parser.add_argument(
        '--skip-pages',
        type=int,
        default=2,
        help='Number of pages to skip at the beginning (default: 2)'
    )
    parser.add_argument(
        '--date',
        type=str,
        default=None,
        help='Roster date in YYYY-MM-DD format (included in output as roster_date column)'
    )

    args = parser.parse_args()

    print(f"Extracting facilities from: {args.pdf_path}")
    facilities = extract_facilities_from_pdf(args.pdf_path, args.skip_pages, args.date)
    print(f"Found {len(facilities)} facilities")

    facilities_to_csv(facilities, args.output)
    print(f"Output written to: {args.output}")


if __name__ == '__main__':
    main()
