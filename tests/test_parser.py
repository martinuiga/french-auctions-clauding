import pytest
from decimal import Decimal
from datetime import date
from unittest.mock import MagicMock
import pandas as pd

from src.scraping.parser import AuctionParser, MONTH_NAMES
from src.scraping.enums import Technology, Region


class TestParseNumber:

    def test_parse_number_integer(self):
        result = AuctionParser._parse_number(100)
        assert result == Decimal("100")

    def test_parse_number_float(self):
        result = AuctionParser._parse_number(100.50)
        assert result == Decimal("100.5")

    def test_parse_number_string_with_comma(self):
        result = AuctionParser._parse_number("1,234")
        assert result == Decimal("1234")

    def test_parse_number_string_with_spaces(self):
        result = AuctionParser._parse_number("1 234")
        assert result == Decimal("1234")

    def test_parse_number_none(self):
        result = AuctionParser._parse_number(None)
        assert result is None

    def test_parse_number_dash(self):
        result = AuctionParser._parse_number("-")
        assert result is None

    def test_parse_number_na(self):
        result = AuctionParser._parse_number("n/a")
        assert result is None

    def test_parse_number_NA_uppercase(self):
        result = AuctionParser._parse_number("N/A")
        assert result is None

    def test_parse_number_empty_string(self):
        result = AuctionParser._parse_number("")
        assert result is None

    def test_parse_number_pandas_nan(self):
        result = AuctionParser._parse_number(pd.NA)
        assert result is None

    def test_parse_number_invalid_string(self):
        result = AuctionParser._parse_number("invalid")
        assert result is None


class TestTechnology:

    def test_technology_wind(self):
        assert Technology.from_string("Wind") == Technology.WIND

    def test_technology_eolien(self):
        assert Technology.from_string("Eolien") == Technology.WIND

    def test_technology_eolien_onshore(self):
        assert Technology.from_string("Eolien onshore") == Technology.WIND

    def test_technology_solar(self):
        assert Technology.from_string("Solar") == Technology.SOLAR

    def test_technology_solaire(self):
        assert Technology.from_string("Solaire") == Technology.SOLAR

    def test_technology_hydro(self):
        assert Technology.from_string("Hydro") == Technology.HYDRO

    def test_technology_hydraulique(self):
        assert Technology.from_string("Hydraulique") == Technology.HYDRO

    def test_technology_thermal(self):
        assert Technology.from_string("Thermal") == Technology.THERMAL

    def test_technology_thermique(self):
        assert Technology.from_string("Thermique") == Technology.THERMAL

    def test_technology_case_insensitive(self):
        assert Technology.from_string("SOLAR") == Technology.SOLAR
        assert Technology.from_string("solar") == Technology.SOLAR

    def test_technology_unknown(self):
        assert Technology.from_string("Unknown") is None

    def test_technology_partial_match(self):
        assert Technology.from_string("Solar Power Plant") == Technology.SOLAR


class TestRegion:

    def test_region_bretagne(self):
        assert Region.from_string("Bretagne") == Region.BRETAGNE

    def test_region_ile_de_france(self):
        assert Region.from_string("Île-de-France") == Region.ILE_DE_FRANCE

    def test_region_normandie(self):
        assert Region.from_string("Normandie") == Region.NORMANDIE

    def test_region_occitanie(self):
        assert Region.from_string("Occitanie") == Region.OCCITANIE

    def test_region_case_insensitive(self):
        assert Region.from_string("bretagne") == Region.BRETAGNE

    def test_region_unknown(self):
        assert Region.from_string("Unknown Region") is None

    def test_region_partial_match(self):
        assert Region.from_string("Region Bretagne Area") == Region.BRETAGNE


class TestAuctionParser:

    def test_source_file_tracking(self):
        parser = AuctionParser(source_file="test.xlsx")
        assert parser.source_file == "test.xlsx"

    def test_source_file_default_empty(self):
        parser = AuctionParser()
        assert parser.source_file == ""


class TestExtractDate:

    def test_extract_date_from_sheet_name(self):
        parser = AuctionParser()
        df = pd.DataFrame([[None]])
        result = parser._extract_date(df, "January 2024")
        assert result == date(2024, 1, 1)

    def test_extract_date_abbreviated_month(self):
        parser = AuctionParser()
        df = pd.DataFrame([[None]])
        result = parser._extract_date(df, "Mar 2023")
        assert result == date(2023, 3, 1)

    def test_extract_date_from_cell_content(self):
        parser = AuctionParser()
        df = pd.DataFrame([["Auction Results December 2022"]])
        result = parser._extract_date(df, "Sheet1")
        assert result == date(2022, 12, 1)

    def test_extract_date_no_date_found(self):
        parser = AuctionParser()
        df = pd.DataFrame([["No date here"]])
        result = parser._extract_date(df, "Sheet1")
        assert result is None

    def test_extract_date_no_year(self):
        parser = AuctionParser()
        df = pd.DataFrame([["January only"]])
        result = parser._extract_date(df, "Sheet1")
        assert result is None


class TestMonthNames:

    def test_all_full_months_present(self):
        full_months = ["january", "february", "march", "april", "may", "june",
                       "july", "august", "september", "october", "november", "december"]
        for month in full_months:
            assert month in MONTH_NAMES

    def test_abbreviated_months_present(self):
        abbrev = ["jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "oct", "nov", "dec"]
        for month in abbrev:
            assert month in MONTH_NAMES

    def test_month_values_correct(self):
        assert MONTH_NAMES["january"] == 1
        assert MONTH_NAMES["june"] == 6
        assert MONTH_NAMES["december"] == 12


class TestFindHeaders:

    def test_find_headers_with_volume_offered(self):
        parser = AuctionParser()
        df = pd.DataFrame([
            ["Region", "Volume Offered", "Volume Allocated", "Price"],
            ["Bretagne", 100, 80, 50.5]
        ])
        result = parser._find_headers(df)
        assert result is not None
        assert result["row"] == 0
        assert "volume_offered_idx" in result
        assert "volume_allocated_idx" in result

    def test_find_headers_with_auctionned(self):
        parser = AuctionParser()
        df = pd.DataFrame([
            ["Region", "Volume Auctionned", "Volume Sold"],
            ["Bretagne", 100, 80]
        ])
        result = parser._find_headers(df)
        assert result is not None

    def test_find_headers_no_volume_column(self):
        parser = AuctionParser()
        df = pd.DataFrame([
            ["Region", "Name", "Value"],
            ["Bretagne", "Test", 100]
        ])
        result = parser._find_headers(df)
        assert result is None

    def test_find_headers_in_later_row(self):
        parser = AuctionParser()
        df = pd.DataFrame([
            ["Title Row", None, None],
            ["Subtitle", None, None],
            ["Region", "Volume Offered", "Volume Allocated"],
            ["Bretagne", 100, 80]
        ])
        result = parser._find_headers(df)
        assert result is not None
        assert result["row"] == 2
