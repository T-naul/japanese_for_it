from dataclasses import dataclass
import uuid
from apps.content.models import Grammar, Vocabulary


@dataclass
class MatchResult:
    matched_id: uuid.UUID
    confidence: float
    matched_by: str


class ContentMatcher:
    def __init__(self):
        self._vocab_cache: dict[tuple[str, str], MatchResult | None] = {}
        self._grammar_cache: dict[str, MatchResult | None] = {}

    def match_vocabulary(self, candidate: dict) -> MatchResult | None:
        surface = (candidate.get("surface") or "").strip()
        reading = (candidate.get("reading") or "").strip()

        if not surface and not reading:
            return None

        cache_key = (surface, reading)
        if cache_key in self._vocab_cache:
            return self._vocab_cache[cache_key]

        res = None

        # Priority 1: Exact kanji + exact reading
        if surface and reading:
            vocab = Vocabulary.objects.filter(kanji=surface, hiragana=reading).first()
            if vocab:
                res = MatchResult(
                    matched_id=vocab.id,
                    confidence=1.0,
                    matched_by="exact_kanji_and_reading",
                )

        # Priority 2: Exact kanji
        if not res and surface:
            vocab = Vocabulary.objects.filter(kanji=surface).first()
            if vocab:
                res = MatchResult(
                    matched_id=vocab.id,
                    confidence=0.85,
                    matched_by="exact_kanji",
                )

        # Priority 3: Exact reading / kana match
        if not res and reading:
            vocab = Vocabulary.objects.filter(hiragana=reading).first()
            if vocab:
                res = MatchResult(
                    matched_id=vocab.id,
                    confidence=0.9,
                    matched_by="exact_hiragana",
                )
        elif not res and surface:
            vocab = Vocabulary.objects.filter(hiragana=surface).first()
            if vocab:
                res = MatchResult(
                    matched_id=vocab.id,
                    confidence=0.9,
                    matched_by="surface_matches_hiragana",
                )

        self._vocab_cache[cache_key] = res
        return res

    def match_grammar(self, candidate: dict) -> MatchResult | None:
        pattern = (candidate.get("pattern") or "").strip()
        if not pattern:
            return None

        if pattern in self._grammar_cache:
            return self._grammar_cache[pattern]

        res = None
        # 1. Exact match
        gram = Grammar.objects.filter(pattern=pattern).first()
        if gram:
            res = MatchResult(
                matched_id=gram.id,
                confidence=1.0,
                matched_by="exact_pattern",
            )
        else:
            # 2. Normalized pattern match
            norm = pattern.strip("~～ ")
            candidates_to_try = [
                f"~{norm}",
                f"～{norm}",
                f"~{norm}~",
                f"～{norm}～",
                norm,
            ]
            gram = Grammar.objects.filter(pattern__in=candidates_to_try).first()
            if gram:
                res = MatchResult(
                    matched_id=gram.id,
                    confidence=0.9,
                    matched_by="normalized_pattern",
                )

        self._grammar_cache[pattern] = res
        return res
