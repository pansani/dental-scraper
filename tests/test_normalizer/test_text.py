import pytest

from dental_scraper.normalization.text import (
    clean_text,
    extract_quantity,
    normalize_text,
    remove_quantity_from_name,
)


class TestCleanText:
    def test_strip_whitespace(self):
        assert clean_text("  hello  ") == "hello"
        assert clean_text("\thello\n") == "hello"

    def test_normalize_spaces(self):
        assert clean_text("hello   world") == "hello world"

    def test_empty_input(self):
        assert clean_text("") == ""
        assert clean_text(None) == ""


class TestNormalizeText:
    def test_lowercase(self):
        assert normalize_text("Hello World") == "hello world"

    def test_remove_accents(self):
        assert normalize_text("Anestésico") == "anestesico"
        assert normalize_text("Proteção") == "protecao"

    def test_remove_punctuation(self):
        assert normalize_text("hello, world!") == "hello world"

    def test_combined(self):
        assert normalize_text("  Olá, Mundo!  ") == "ola mundo"


class TestExtractQuantity:
    def test_quantity_with_un(self):
        qty, _ = extract_quantity("Luvas c/100 un")
        assert qty == 100

    def test_quantity_with_unidades(self):
        qty, _ = extract_quantity("Gaze 500 unidades")
        assert qty == 500

    def test_quantity_with_pcs(self):
        qty, _ = extract_quantity("Sugador 40pcs")
        assert qty == 40

    def test_no_quantity(self):
        qty, _ = extract_quantity("Resina Z350")
        assert qty == 1

    def test_quantity_too_large(self):
        qty, _ = extract_quantity("Código 999999")
        assert qty == 1


class TestRemoveQuantityFromName:
    def test_remove_quantity(self):
        result = remove_quantity_from_name("Luvas c/100 un", 100)
        assert "100" not in result

    def test_no_removal_when_qty_1(self):
        result = remove_quantity_from_name("Resina Z350", 1)
        assert result == "Resina Z350"
