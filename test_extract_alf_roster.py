"""
Tests for Nebraska ALF Roster PDF extraction.

These tests verify that:
1. Data can be extracted from the PDF
2. Required columns are populated
3. Data quality meets expectations
"""

import pytest
from pathlib import Path
from extract_alf_roster import (
    extract_facilities_from_pdf,
    parse_page_text,
    facilities_to_csv
)


# Path to the test PDF
PDF_PATH = Path(__file__).parent / "ALF Roster.pdf"


class TestDataExtraction:
    """Tests for the PDF data extraction functionality."""

    @pytest.fixture(scope="class")
    def facilities(self):
        """Extract facilities once for all tests in this class."""
        if not PDF_PATH.exists():
            pytest.skip(f"PDF file not found: {PDF_PATH}")
        return extract_facilities_from_pdf(str(PDF_PATH), skip_pages=2)

    def test_facilities_extracted(self, facilities):
        """Test that facilities are extracted from the PDF."""
        assert len(facilities) > 0, "No facilities were extracted from the PDF"

    def test_expected_facility_count(self, facilities):
        """Test that we extract approximately the expected number of facilities."""
        # The PDF indicates 278 total facilities
        expected_count = 278
        tolerance = 0.1  # Allow 10% variance due to parsing challenges
        min_count = int(expected_count * (1 - tolerance))

        assert len(facilities) >= min_count, (
            f"Expected at least {min_count} facilities, got {len(facilities)}"
        )


class TestRequiredColumns:
    """Tests that verify required columns are populated."""

    @pytest.fixture(scope="class")
    def facilities(self):
        """Extract facilities once for all tests in this class."""
        if not PDF_PATH.exists():
            pytest.skip(f"PDF file not found: {PDF_PATH}")
        return extract_facilities_from_pdf(str(PDF_PATH), skip_pages=2)

    def test_facility_name_populated(self, facilities):
        """Test that facility_name is populated for all records."""
        empty_names = [f for f in facilities if not f.get('facility_name')]
        assert len(empty_names) == 0, (
            f"{len(empty_names)} facilities have empty facility_name"
        )

    def test_town_populated(self, facilities):
        """Test that town is populated for most records."""
        empty_towns = [f for f in facilities if not f.get('town')]
        fill_rate = (len(facilities) - len(empty_towns)) / len(facilities)
        assert fill_rate >= 0.9, (
            f"Town fill rate is {fill_rate:.1%}, expected at least 90%"
        )

    def test_zip_code_populated(self, facilities):
        """Test that zip_code is populated for most records."""
        empty_zips = [f for f in facilities if not f.get('zip_code')]
        fill_rate = (len(facilities) - len(empty_zips)) / len(facilities)
        assert fill_rate >= 0.9, (
            f"Zip code fill rate is {fill_rate:.1%}, expected at least 90%"
        )

    def test_license_number_populated(self, facilities):
        """Test that license_number is populated for most records."""
        empty_licenses = [f for f in facilities if not f.get('license_number')]
        fill_rate = (len(facilities) - len(empty_licenses)) / len(facilities)
        assert fill_rate >= 0.8, (
            f"License number fill rate is {fill_rate:.1%}, expected at least 80%"
        )

    def test_total_beds_populated(self, facilities):
        """Test that total_beds is populated for most records."""
        empty_beds = [f for f in facilities if not f.get('total_beds')]
        fill_rate = (len(facilities) - len(empty_beds)) / len(facilities)
        assert fill_rate >= 0.8, (
            f"Total beds fill rate is {fill_rate:.1%}, expected at least 80%"
        )

    def test_phone_populated(self, facilities):
        """Test that phone is populated for most records."""
        empty_phones = [f for f in facilities if not f.get('phone')]
        fill_rate = (len(facilities) - len(empty_phones)) / len(facilities)
        assert fill_rate >= 0.7, (
            f"Phone fill rate is {fill_rate:.1%}, expected at least 70%"
        )


class TestDataQuality:
    """Tests for data quality and format validation."""

    @pytest.fixture(scope="class")
    def facilities(self):
        """Extract facilities once for all tests in this class."""
        if not PDF_PATH.exists():
            pytest.skip(f"PDF file not found: {PDF_PATH}")
        return extract_facilities_from_pdf(str(PDF_PATH), skip_pages=2)

    def test_zip_code_format(self, facilities):
        """Test that zip codes are in valid 5-digit format."""
        invalid_zips = []
        for f in facilities:
            zip_code = f.get('zip_code', '')
            if zip_code and not zip_code.isdigit():
                invalid_zips.append(zip_code)
            elif zip_code and len(zip_code) != 5:
                invalid_zips.append(zip_code)

        assert len(invalid_zips) == 0, (
            f"Found {len(invalid_zips)} invalid zip codes: {invalid_zips[:5]}"
        )

    def test_license_number_format(self, facilities):
        """Test that license numbers follow the ALF### pattern."""
        import re
        pattern = re.compile(r'^ALF\d{3}$')

        invalid_licenses = []
        for f in facilities:
            license_num = f.get('license_number', '')
            if license_num and not pattern.match(license_num):
                invalid_licenses.append(license_num)

        # Allow some invalid due to parsing challenges
        error_rate = len(invalid_licenses) / len(facilities)
        assert error_rate < 0.1, (
            f"Found {len(invalid_licenses)} invalid license numbers ({error_rate:.1%})"
        )

    def test_total_beds_numeric(self, facilities):
        """Test that total_beds values are numeric."""
        non_numeric = []
        for f in facilities:
            beds = f.get('total_beds', '')
            if beds and not beds.isdigit():
                non_numeric.append(beds)

        assert len(non_numeric) == 0, (
            f"Found {len(non_numeric)} non-numeric bed counts: {non_numeric[:5]}"
        )

    def test_phone_format(self, facilities):
        """Test that phone numbers are in expected format."""
        import re
        pattern = re.compile(r'^\(\d{3}\)\s*\d{3}-\d{4}$')

        invalid_phones = []
        for f in facilities:
            phone = f.get('phone', '')
            if phone and not pattern.match(phone):
                invalid_phones.append(phone)

        # Allow some variance in phone formats
        if facilities:
            phones_with_data = [f for f in facilities if f.get('phone')]
            if phones_with_data:
                error_rate = len(invalid_phones) / len(phones_with_data)
                assert error_rate < 0.2, (
                    f"Found {len(invalid_phones)} invalid phone formats ({error_rate:.1%})"
                )

    def test_facility_type_is_alf(self, facilities):
        """Test that facility_type is ALF for all records."""
        non_alf = [f for f in facilities if f.get('facility_type') and f['facility_type'] != 'ALF']
        assert len(non_alf) == 0, (
            f"Found {len(non_alf)} facilities with non-ALF type"
        )


class TestColumnFillRates:
    """Generate a report of fill rates for all columns."""

    @pytest.fixture(scope="class")
    def facilities(self):
        """Extract facilities once for all tests in this class."""
        if not PDF_PATH.exists():
            pytest.skip(f"PDF file not found: {PDF_PATH}")
        return extract_facilities_from_pdf(str(PDF_PATH), skip_pages=2)

    def test_print_fill_rates(self, facilities):
        """Print fill rates for all columns (informational test)."""
        columns = [
            'town', 'county', 'zip_code', 'facility_name', 'address',
            'phone', 'fax', 'licensee', 'administrator', 'facility_type',
            'license_number', 'total_beds', 'services', 'accreditation',
            'care_of_address'
        ]

        print("\n" + "=" * 50)
        print("Column Fill Rates")
        print("=" * 50)

        total = len(facilities)
        for col in columns:
            filled = sum(1 for f in facilities if f.get(col))
            rate = (filled / total * 100) if total > 0 else 0
            print(f"{col:20s}: {filled:4d}/{total:4d} ({rate:5.1f}%)")

        print("=" * 50)

        # This test always passes - it's for reporting purposes
        assert True


class TestParsePageText:
    """Unit tests for the parse_page_text function."""

    def test_parse_sample_page(self):
        """Test parsing a sample page text."""
        sample_text = """ASSISTED LIVING FACILITY ROSTER Updated:8/15/2025 By City Page 2 of 50
TOWN (County) Zip Code
Name of Facility
Address
Phone Number Fac Type
Licensee License No No. and Type of
Administration Accreditation Beds Services
ADAMS (GAGE) - 68301 ALF AGED/DISABLED MED WVR CER
Total Lic - 35
GOLD CREST RETIREMENT CENTER ALF066
200 LEVI LANE
(402) 988-7115 FAX:(402) 988-2087
COFFMAN-LEVI CHARITABLE TRUST, INC
JENNIFER GRAFF, ADMINISTRATOR
AINSWORTH (BROWN) - 69210 ALF AGED/DISABLED MED WVR CER
Total Lic - 36
COTTONWOOD VILLA ALF046
450 SOUTH MAIN STREET
(402) 387-1000 FAX:(402) 387-1015
PRAIRIE INVESTORS, LLC
ANN FIALA, ADMINISTRATOR"""

        facilities = parse_page_text(sample_text)

        assert len(facilities) == 2, f"Expected 2 facilities, got {len(facilities)}"

        # Check first facility
        f1 = facilities[0]
        assert f1['town'] == 'ADAMS'
        assert f1['county'] == 'GAGE'
        assert f1['zip_code'] == '68301'
        assert f1['facility_name'] == 'GOLD CREST RETIREMENT CENTER'
        assert f1['license_number'] == 'ALF066'
        assert f1['total_beds'] == '35'
        assert f1['phone'] == '(402) 988-7115'
        assert f1['fax'] == '(402) 988-2087'

        # Check second facility
        f2 = facilities[1]
        assert f2['town'] == 'AINSWORTH'
        assert f2['county'] == 'BROWN'
        assert f2['zip_code'] == '69210'
        assert f2['facility_name'] == 'COTTONWOOD VILLA'
        assert f2['license_number'] == 'ALF046'
        assert f2['total_beds'] == '36'

    def test_parse_empty_text(self):
        """Test that empty text returns no facilities."""
        facilities = parse_page_text("")
        assert facilities == []

    def test_parse_header_only(self):
        """Test that header-only text returns no facilities."""
        header_text = """ASSISTED LIVING FACILITY ROSTER Updated:8/15/2025 By City Page 2 of 50
TOWN (County) Zip Code
Name of Facility
Address
Phone Number Fac Type
Licensee License No No. and Type of
Administration Accreditation Beds Services"""

        facilities = parse_page_text(header_text)
        assert facilities == []


class TestCSVOutput:
    """Tests for CSV output functionality."""

    @pytest.fixture(scope="class")
    def facilities(self):
        """Extract facilities once for all tests in this class."""
        if not PDF_PATH.exists():
            pytest.skip(f"PDF file not found: {PDF_PATH}")
        return extract_facilities_from_pdf(str(PDF_PATH), skip_pages=2)

    def test_csv_output(self, facilities, tmp_path):
        """Test that CSV output is created correctly."""
        output_path = tmp_path / "test_output.csv"
        facilities_to_csv(facilities, str(output_path))

        assert output_path.exists(), "CSV file was not created"

        # Read back and verify
        import csv
        with open(output_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        assert len(rows) == len(facilities), "Row count mismatch"

    def test_csv_has_headers(self, facilities, tmp_path):
        """Test that CSV has expected headers."""
        output_path = tmp_path / "test_output.csv"
        facilities_to_csv(facilities, str(output_path))

        with open(output_path, 'r', encoding='utf-8') as f:
            header = f.readline().strip()

        expected_columns = [
            'town', 'county', 'zip_code', 'facility_name', 'address',
            'phone', 'fax', 'licensee', 'administrator', 'facility_type',
            'license_number', 'total_beds', 'services', 'accreditation',
            'care_of_address'
        ]

        for col in expected_columns:
            assert col in header, f"Missing column: {col}"

    def test_empty_facilities_raises_error(self, tmp_path):
        """Test that empty facilities list raises an error."""
        output_path = tmp_path / "test_output.csv"
        with pytest.raises(ValueError):
            facilities_to_csv([], str(output_path))


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
