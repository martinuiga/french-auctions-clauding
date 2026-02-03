import pytest
from decimal import Decimal
from datetime import date
from src.parser import AuctionParser


class TestAuctionParser:

    def test_parse_number_integer(self):
        parser = AuctionParser()
        assert parser._parse_number(100) == Decimal("100")

    def test_parse_number_float(self):
        parser = AuctionParser()
        assert parser._parse_number(100.50) == Decimal("100.5")

    def test_parse_number_string(self):
        parser = AuctionParser()
        assert parser._parse_number("1,234") == Decimal("1234")

    def test_parse_number_none(self):
        parser = AuctionParser()
        assert parser._parse_number(None) is None

    def test_parse_number_dash(self):
        parser = AuctionParser()
        assert parser._parse_number("-") is None

    def test_match_region(self):
        parser = AuctionParser()
        assert parser._match_region("Bretagne") == "Bretagne"
        assert parser._match_region("Île-de-France") == "Île-de-France"
        assert parser._match_region("Unknown") is None

    def test_match_technology(self):
        parser = AuctionParser()
        assert parser._match_technology("Wind") == "Wind"
        assert parser._match_technology("Solar Power") == "Solar"
        assert parser._match_technology("Unknown") is None

    def test_source_file_tracking(self):
        parser = AuctionParser(source_file="test.xlsx")
        assert parser.source_file == "test.xlsx"
