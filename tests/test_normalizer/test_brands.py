import pytest

from dental_scraper.normalization.brands import extract_brand_from_name, normalize_brand


class TestNormalizeBrand:
    def test_exact_match(self):
        assert normalize_brand("3M") == "3m"
        assert normalize_brand("Dentsply") == "dentsply"

    def test_alias_match(self):
        assert normalize_brand("3M Oral Care") == "3m"
        assert normalize_brand("3M ESPE") == "3m"
        assert normalize_brand("Dentsply Sirona") == "dentsply"

    def test_case_insensitive(self):
        assert normalize_brand("3M ORAL CARE") == "3m"
        assert normalize_brand("dentsply sirona") == "dentsply"

    def test_with_accents(self):
        assert normalize_brand("Colténe") == "coltene"

    def test_unknown_brand(self):
        assert normalize_brand("Unknown Brand") == "Unknown Brand"

    def test_empty_input(self):
        assert normalize_brand("") == ""
        assert normalize_brand(None) == ""


class TestExtractBrandFromName:
    def test_brand_in_name(self):
        assert extract_brand_from_name("Resina 3M Filtek Z350") == "3m"
        assert extract_brand_from_name("Anestésico Dentsply Citanest") == "dentsply"

    def test_no_brand_in_name(self):
        assert extract_brand_from_name("Luvas de Procedimento") is None

    def test_empty_name(self):
        assert extract_brand_from_name("") is None
