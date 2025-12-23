import pytest

from dental_scraper.normalization.units import extract_unit_from_name, normalize_unit


class TestNormalizeUnit:
    def test_exact_match(self):
        assert normalize_unit("unidade") == "unidade"
        assert normalize_unit("caixa") == "caixa"

    def test_alias_match(self):
        assert normalize_unit("un") == "unidade"
        assert normalize_unit("und") == "unidade"
        assert normalize_unit("pcs") == "unidade"
        assert normalize_unit("cx") == "caixa"
        assert normalize_unit("pct") == "pacote"

    def test_case_insensitive(self):
        assert normalize_unit("UN") == "unidade"
        assert normalize_unit("CX") == "caixa"

    def test_default_to_unidade(self):
        assert normalize_unit("") == "unidade"
        assert normalize_unit(None) == "unidade"
        assert normalize_unit("unknown") == "unidade"


class TestExtractUnitFromName:
    def test_caixa_in_name(self):
        assert extract_unit_from_name("Luvas Caixa c/100") == "caixa"
        assert extract_unit_from_name("Anestésico cx 50") == "caixa"

    def test_pacote_in_name(self):
        assert extract_unit_from_name("Gaze Pacote 500un") == "pacote"

    def test_kit_in_name(self):
        assert extract_unit_from_name("Kit Clareamento") == "kit"

    def test_default_unidade(self):
        assert extract_unit_from_name("Resina Z350") == "unidade"
