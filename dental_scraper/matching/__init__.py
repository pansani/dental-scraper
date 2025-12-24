from .engine import MatchingEngine
from .index import MatchIndex
from .models import Match, MatchResult, Product, ProductMatch
from .similarity import compute_similarity, exact_match, fuzzy_match

__all__ = [
    "MatchingEngine",
    "MatchIndex",
    "Match",
    "MatchResult",
    "Product",
    "ProductMatch",
    "compute_similarity",
    "exact_match",
    "fuzzy_match",
]
