"""Suitability assessment domain - works with military_medicine.db."""

from __future__ import annotations

import re
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher

# Typographic apostrophes in the source documents vs the plain one people type (м’язів / м'язів)
_APOSTROPHES = str.maketrans({"’": "'", "ʼ": "'", "`": "'"})


def normalize_text(text: str | None) -> str:
    """Lowercase (Cyrillic too, unlike SQLite LOWER) and unify apostrophes for search."""
    return (text or "").lower().translate(_APOSTROPHES)


# ===== Word-level matching (disease + severity, e.g. "астма середньої тяжкості") =====

# How people describe severity -> words used in point descriptions.
# In each synonym, the part before "|" is what a word in the text must start with
# (so "значн|і" also matches "значними"); the whole word is how it is shown to the user.
_SEVERITY_SYNONYMS = {
    "тяжк": ("тяжк|ий", "значн|і", "виражен|і", "різко"),
    "важк": ("тяжк|ий", "значн|і", "виражен|і", "різко"),
    "сильн": ("значн|і", "виражен|і", "різко"),
    "значн": ("значн|і", "виражен|і", "різко", "тяжк|ий"),
    "виражен": ("виражен|і", "значн|і", "різко"),
    "середн": ("середн|ій", "помірн|і"),
    "помірн": ("помірн|і", "середн|ій"),
    "легк": ("легк|ий", "незначн|і"),
    "незначн": ("незначн|і", "легк|ий"),
    "рідк": ("рідк|і", "поодинок|і"),
    "част": ("част|і",),
}
# Everyday names -> words used in the documents. Only for names the documents do not use
# themselves (the search already finds "інсульт", "інфаркт", "епілепсія" and the like).
_DISEASE_SYNONYMS = {
    "рак": ("рак", "злоякісн|і", "карцином|а"),
    "онколог": ("онколог|ія", "злоякісн|і", "карцином|а", "рак"),
    "лейкоз": ("лейкоз", "лейкемі|я", "кровотворн|ої", "лімфом|а"),
    "лейкемі": ("лейкемі|я", "лейкоз", "кровотворн|ої", "лімфом|а"),
    "алкогол": ("алкогол|ь",),
    "наркоман": ("наркотичн|і", "психоактивн|і", "опіоїд|и"),
    "наркотик": ("наркотичн|і", "психоактивн|і", "опіоїд|и"),
    "щитовид": ("щитоподібн|а",),
    "камен": ("сечокам'ян|а", "холецист|ит"),  # with "нирки" / "жовчні" it narrows down
    "камін": ("сечокам'ян|а", "холецист|ит"),
    "нирк": ("нирк|и", "нефр|ит"),
    "чмт": ("черепн|о", "контузі|я", "струс"),
    "всд": ("вегетативн|а", "дистоні|я"),
    "меніск": ("внутрішньосуглобов|і",),
    "дальтон": ("кольоровідчутт|я",),
    "ковід": ("коронавірус",),
    "covid": ("коронавірус",),
    "грибок": ("мікоз", "грибк|ові"),
    "гайморит": ("синусит",),
    "радикуліт": ("радикулопаті|я",),
    "зір": ("зор|у", "зоров|ий"),
    "рук": ("кист|і", "кінцівк|и"),
    "ног": ("стоп|а", "гомілк|а", "стегн|о", "кінцівк|и"),
}
# Stages are written as Roman numerals ("II стадії")
_STAGE_NUMBERS = {
    "1": "i", "2": "ii", "3": "iii", "4": "iv", "перш": "i", "друг": "ii", "трет": "iii",
}
# Words that describe how a disease shows, not which disease it is ("значні порушення функцій")
_DESCRIPTOR_PREFIXES = ("поруш", "функц", "напад", "перебіг", "прогрес", "загостр", "уражен")
_STOP_WORDS = {"з", "із", "зі", "і", "й", "та", "в", "у", "на", "ступеня", "ступінь", "стадії",
               "стадія", "форма", "форми", "хвороба"}
_WORD = re.compile(r"[\w']+")


@dataclass(frozen=True)
class _Term:
    """One query word: matches a text word that starts with any prefix (or equals any exact)."""
    prefixes: tuple[str, ...] = ()
    exact: tuple[str, ...] = ()
    is_severity: bool = False  # severity or stage word, not part of the disease name
    synonyms: tuple[str, ...] = ()  # other words searched for it, to show the user
    synonym_prefixes: tuple[str, ...] = ()  # what each of those synonyms matches, same order

    def found_in(self, words: list[str]) -> bool:
        return any(self.matches(w) for w in words)

    def matches(self, word: str) -> bool:
        """word must already be normalized (see normalize_text).

        A short prefix only takes a short ending, so "рак" matches "раку" but not
        "ракетного" or "раковини".
        """
        if word in self.exact:
            return True
        return any(
            word.startswith(prefix) and (len(prefix) >= 4 or len(word) <= len(prefix) + 2)
            for prefix in self.prefixes
        )


def _stem(word: str) -> str:
    """Crude Ukrainian stem: drop the ending so "астми" matches "астма"."""
    if len(word) <= 4 or word[-1] not in "аеєиіїоуюяьй":
        # Ends in a consonant ("склероз", "перелом"): the word is the stem already, and
        # cutting it would match other words ("склеро" -> "склеродермія")
        return word
    if len(word) <= 7:
        return word[:-1]  # "виразка" -> "виразк", not "вираз" (which also starts "виразно")
    return word[:-2]


def _stems(word: str) -> tuple[str, ...]:
    """Stem, plus one without the vowel that drops out in other forms:
    "шлунок" -> "шлунка", "грибок" -> "грибка", "рубець" -> "рубця"."""
    stems = [_stem(word)]
    if len(word) >= 5 and word.endswith("ець"):
        stems.append(word[:-3] + "ц")
    elif len(word) >= 5 and word[-2] in "оеє" and word[-1] not in "аеєиіїоуюяь":
        stems.append(word[:-2] + word[-1])
    return tuple(stems)


def _words(text: str | None) -> list[str]:
    return _WORD.findall(normalize_text(text))


def _synonym_term(word: str, synonyms: tuple[str, ...], is_severity: bool) -> _Term:
    """Term for a word with synonyms; the ones the user did not type are kept for display."""
    prefixes = tuple(s.split("|")[0] for s in synonyms)
    shown = [
        (s.replace("|", ""), prefix)
        for s, prefix in zip(synonyms, prefixes, strict=True)
        if not word.startswith(prefix)
    ]
    return _Term(
        prefixes=prefixes,
        is_severity=is_severity,
        synonyms=tuple(s for s, _ in shown),
        synonym_prefixes=tuple(p for _, p in shown),
    )


def query_terms(query: str) -> list[_Term]:
    """Split a search query into terms, with severity synonyms and stage numbers."""
    terms = []
    for word in _words(query):
        if word in _STOP_WORDS:
            continue
        # "2" or "другої" is a stage, but "46" or "дріб" is not
        stage = next(
            (roman for key, roman in _STAGE_NUMBERS.items()
             if (word == key if key.isdigit() else word.startswith(key))),
            None,
        )
        if stage:
            terms.append(_Term(
                exact=(stage,), is_severity=True,
                synonyms=(stage.upper(),), synonym_prefixes=(stage,),
            ))
            continue
        if word.startswith(("тяжкіст", "тяжкост", "важкіст", "важкост")):
            # The noun from "ступінь тяжкості" / "середньої тяжкості", not "тяжка"
            terms.append(_Term(prefixes=("тяжк", "важк"), is_severity=True))
            continue
        synonyms = next(
            (alts for key, alts in _SEVERITY_SYNONYMS.items() if word.startswith(key)), None
        )
        if synonyms:
            terms.append(_synonym_term(word, synonyms, is_severity=True))
            continue
        # A short key only takes a short ending: "рак" -> "раку", not "ракета"
        disease = next(
            (alts for key, alts in _DISEASE_SYNONYMS.items() if word.startswith(key)
             and (len(key) >= 4 or len(word) <= len(key) + 2)),
            None,
        )
        if disease:
            terms.append(_synonym_term(word, disease, is_severity=False))
        else:
            terms.append(
                _Term(prefixes=_stems(word), is_severity=word.startswith(_DESCRIPTOR_PREFIXES))
            )
    return terms


def query_synonyms(query: str, words: list[str] | None = None) -> list[str]:
    """Synonyms the search also looked for, e.g. ["злоякісні", "карцинома"] for "рак".

    With words (of the articles shown), only the synonyms actually found among them, so
    "камені в нирках" does not list "холецистит".
    """
    shown: list[str] = []
    for term in query_terms(query):
        for synonym, prefix in zip(term.synonyms, term.synonym_prefixes, strict=True):
            if synonym in shown:
                continue
            if words is not None and not _Term(prefixes=(prefix,), exact=(prefix,)).found_in(words):
                continue
            shown.append(synonym)
    return shown


def _disease_words_in(query: str, texts: list[str]) -> list[str]:
    """Distinct words of the texts, as written, that match the disease part of the query."""
    disease = [term for term in query_terms(query) if not term.is_severity]
    found: list[str] = []
    seen: set[str] = set()
    for text in texts:
        for word in _WORD.findall((text or "").translate(_APOSTROPHES)):
            normalized = normalize_text(word)
            key = normalized[:7]  # one form per word: "склеродермія", not also "склеродермії"
            if key not in seen and any(term.matches(normalized) for term in disease):
                seen.add(key)
                found.append(word)
    return found


def word_matches_query(word: str, terms: list[_Term]) -> bool:
    """Whether a word of some text matches any query term (for highlighting)."""
    normalized = normalize_text(word)
    return any(term.matches(normalized) for term in terms)


@dataclass
class _ArticleText:
    """Words of one article, split by where they come from (for ranking search results)."""
    article: Article
    keywords: list[str]
    group: list[str]
    explanation: list[str]  # Додаток 2 explanation of the whole article
    points: dict[str, list[str]] = field(default_factory=dict)  # point letter -> words

    def all_words(self) -> list[str]:
        point_words = [w for words in self.points.values() for w in words]
        return self.keywords + self.group + self.explanation + point_words


@dataclass
class Article:
    """Article (Стаття) from Додаток 1."""
    number: str
    keywords: str
    group_number: int
    table_number: Optional[str] = None


@dataclass
class ArticlePoint:
    """Point (пункт а/б/в/г) for an article."""
    article_number: str
    point_letter: Optional[str]
    description: str
    conclusion: str
    table_number: Optional[str] = None


@dataclass
class AppendixGroup:
    """Group (розділ) from Додаток 2."""
    number: int
    roman_numeral: str
    title: str
    details: Optional[str] = None


@dataclass
class AppendixArticle:
    """Article-level clarification from Додаток 2."""
    article_number: str
    details: Optional[str] = None
    table_number: Optional[str] = None


@dataclass
class AppendixPoint:
    """Point-level clarification from Додаток 2."""
    article_number: str
    point_letter: str
    details: Optional[str] = None
    table_number: Optional[str] = None


@dataclass
class MilitaryUnit:
    """Military specialization from Додаток 3."""
    column_number: int
    name: str


@dataclass
class Requirement:
    """Physical/health requirement for article/point and military unit."""
    article_number: str
    point_letter: Optional[str]
    military_unit_column: int
    requirement: str


class SuitabilityDB:
    """Interface to military_medicine.db for suitability assessment."""

    def __init__(self, db_path: str | Path):
        self.db_path = str(db_path)

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    # ===== Search / Lookup =====

    def search_articles_by_keyword(self, keyword: str) -> list[Article]:
        """Search articles by disease keyword (case-insensitive)."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT article_number, included_keywords, group_number
            FROM articles
            WHERE LOWER(included_keywords) LIKE LOWER(?)
            ORDER BY article_number
        """, (f"%{keyword}%",))

        articles = [
            Article(
                number=row["article_number"],
                keywords=row["included_keywords"],
                group_number=row["group_number"],
            )
            for row in cursor.fetchall()
        ]
        conn.close()
        return articles

    def search_by_keyword(self, keyword: str) -> list[Article]:
        """Find articles containing every word of the query, most relevant first.

        Looks in article keywords, group titles, article and point explanations from
        Додаток 2 (where diseases are often named) and point descriptions. Words match from their start with
        any ending and in any order ("середня астма", "склероз розсіяний"); severity words
        and lay names have synonyms. If nothing is found, retries allowing typos.
        """
        terms = query_terms(keyword)
        if not terms:
            return []
        parts = self._article_parts().values()
        found = [
            text.article for text in parts
            if all(term.found_in(text.all_words()) for term in terms)
        ]
        if not found:
            # Typos: "туберкулоз" -> "туберкульоз"
            query_words = [w for w in _words(keyword) if w not in _STOP_WORDS]
            found = [
                text.article for text in parts
                if all(self._fuzzy_found(w, text.all_words()) for w in query_words)
            ]
        return self._sort_by_relevance(keyword, found)

    def _fuzzy_found(self, query_word: str, words: list[str], threshold: float = 0.85) -> bool:
        """A word at least 85% similar, starting with the same two letters (typos rarely hit
        the start of a word, and this keeps out look-alikes such as "часта" for "астма" or
        "визначення" for "виснаження")."""
        return any(
            word[:2] == query_word[:2]
            and SequenceMatcher(None, word, query_word).ratio() >= threshold
            for word in words
        )

    def _article_parts(self) -> dict[str, _ArticleText]:
        """Every article with the words of its keywords, group title and each point."""
        conn = self._get_conn()
        rows = conn.execute("""
            SELECT a.article_number, a.included_keywords, a.group_number, g.title,
                   y.details AS article_details, ap.point_letter, ap.description, x.details
            FROM articles a
            LEFT JOIN appendix2_groups g ON a.group_number = g.group_number
            LEFT JOIN appendix2_articles y ON y.article_number = a.article_number
            LEFT JOIN article_points ap ON a.article_number = ap.article_number
            LEFT JOIN appendix2_points x
                ON x.article_number = ap.article_number AND x.point_letter = ap.point_letter
        """).fetchall()
        conn.close()
        parts: dict[str, _ArticleText] = {}
        for row in rows:
            number = row["article_number"]
            if number not in parts:
                parts[number] = _ArticleText(
                    article=Article(number, row["included_keywords"], row["group_number"]),
                    keywords=_words(row["included_keywords"]),
                    group=_words(row["title"]),
                    explanation=_words(row["article_details"]),
                )
            parts[number].points[row["point_letter"] or ""] = (
                _words(row["description"]) + _words(row["details"])
            )
        return parts

    def _sort_by_relevance(self, query: str, articles: list[Article]) -> list[Article]:
        """Most relevant first: query words in the article keywords count double, plus the
        best-matching point; ties keep the article order.

        So "Паркінсон" puts article 21 (Parkinson's is in its keywords) above article 38,
        where it is only mentioned in one point's explanation.
        """
        terms = query_terms(query)
        parts = self._article_parts()

        def score(article: Article) -> int:
            text = parts.get(article.number)
            if text is None:
                return 0
            in_keywords = sum(term.found_in(text.keywords + text.group) for term in terms)
            best_point = max(
                (sum(term.found_in(words) for term in terms) for words in text.points.values()),
                default=0,
            )
            return 2 * in_keywords + best_point

        def number(article: Article) -> int:
            return int(article.number) if article.number.isdigit() else 999

        return sorted(articles, key=lambda a: (-score(a), number(a)))

    def found_synonyms(self, query: str, article_numbers: list[str]) -> list[str]:
        """Synonyms of the query that occur in the given articles (see query_synonyms)."""
        parts = self._article_parts()
        words = [w for n in article_numbers if n in parts for w in parts[n].all_words()]
        return query_synonyms(query, words)

    def article_names_disease(self, query: str, article_number: str) -> bool:
        """Whether the article's keywords name the disease from the query.

        Only then the article is really about it. Otherwise the disease is merely mentioned
        in some point's explanation (e.g. "синдром паркінсонізму" among the consequences of
        a neuroinfection in article 20), and that point is not necessarily the right one.
        """
        disease = [term for term in query_terms(query) if not term.is_severity]
        article = self.get_article(article_number)
        if not disease or article is None:
            return False
        keywords = _words(article.keywords)
        return all(term.found_in(keywords) for term in disease)

    def mentioned_words(self, query: str, article_number: str, letters: list[str]) -> list[str]:
        """Words of the given points that match the disease part of the query, as written.

        E.g. "паркінсонізму" for the query "Паркінсон" in article 20, point а.
        """
        texts = []
        for letter in letters:
            point = next(
                (p for p in self.get_article_points(article_number) if p.point_letter == letter),
                None,
            )
            explanation = self.get_appendix2_point(article_number, letter)
            texts.append(point.description if point else "")
            texts.append(explanation.details if explanation else "")
        return _disease_words_in(query, texts)

    def explanation_mentioned_words(self, query: str, article_number: str) -> list[str]:
        """Same as mentioned_words, for the Додаток 2 explanation of the whole article."""
        explanation = self.get_appendix2_article(article_number)
        return _disease_words_in(query, [explanation.details if explanation else ""])

    def best_points(self, query: str, article_number: str) -> list[str]:
        """Point letters of the article that match the query best.

        Each query word found in a point's description or Додаток 2 explanation scores one.
        Returns the top-scoring letters, or [] if the query does not tell the points apart
        (no word found in any point, or all points score the same).
        """
        terms = query_terms(query)
        scores = {}
        for point in self.get_article_points(article_number):
            if not point.point_letter:
                continue
            explanation = self.get_appendix2_point(article_number, point.point_letter)
            words = _words(point.description) + _words(explanation.details if explanation else "")
            scores[point.point_letter] = sum(term.found_in(words) for term in terms)
        if not scores:
            return []
        best = max(scores.values())
        if best == 0 or min(scores.values()) == best:
            return []
        return [letter for letter, score in scores.items() if score == best]

    def get_groups(self) -> list[AppendixGroup]:
        """Get all groups from Додаток 2."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT group_number, roman_numeral, title, details
            FROM appendix2_groups
            ORDER BY group_number
        """)

        groups = [
            AppendixGroup(
                number=row["group_number"],
                roman_numeral=row["roman_numeral"],
                title=row["title"],
                details=row["details"],
            )
            for row in cursor.fetchall()
        ]
        conn.close()
        return groups

    def get_articles_by_group(self, group_number: int) -> list[Article]:
        """Get all articles in a group."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT article_number, included_keywords, group_number
            FROM articles
            WHERE group_number = ?
            ORDER BY article_number
        """, (group_number,))

        articles = [
            Article(
                number=row["article_number"],
                keywords=row["included_keywords"],
                group_number=row["group_number"],
            )
            for row in cursor.fetchall()
        ]
        conn.close()
        return articles

    def get_article(self, article_number: str) -> Optional[Article]:
        """Get a single article by number."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT article_number, included_keywords, group_number
            FROM articles
            WHERE article_number = ?
        """, (article_number,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return Article(
            number=row["article_number"],
            keywords=row["included_keywords"],
            group_number=row["group_number"],
        )

    # ===== Article Details =====

    def get_article_points(self, article_number: str) -> list[ArticlePoint]:
        """Get all points for an article."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT article_number, point_letter, description, conclusion
            FROM article_points
            WHERE article_number = ?
            ORDER BY COALESCE(point_letter, 'zzz')
        """, (article_number,))

        points = [
            ArticlePoint(
                article_number=row["article_number"],
                point_letter=row["point_letter"],
                description=row["description"],
                conclusion=row["conclusion"],
            )
            for row in cursor.fetchall()
        ]
        conn.close()
        return points

    def get_appendix2_article(self, article_number: str) -> Optional[AppendixArticle]:
        """Get article-level clarification from Додаток 2."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT article_number, details, table_number
            FROM appendix2_articles
            WHERE article_number = ?
        """, (article_number,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return AppendixArticle(
            article_number=row["article_number"],
            details=row["details"],
            table_number=row["table_number"],
        )

    def get_appendix2_point(
        self, article_number: str, point_letter: str
    ) -> Optional[AppendixPoint]:
        """Get point-level clarification from Додаток 2."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT article_number, point_letter, details, table_number
            FROM appendix2_points
            WHERE article_number = ? AND point_letter = ?
        """, (article_number, point_letter))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return AppendixPoint(
            article_number=row["article_number"],
            point_letter=row["point_letter"],
            details=row["details"],
            table_number=row["table_number"],
        )

    # ===== Military Units & Requirements =====

    def get_military_units(self) -> list[MilitaryUnit]:
        """Get all military units from Додаток 3."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT column_number, name
            FROM military_units
            ORDER BY column_number
        """)

        units = [
            MilitaryUnit(
                column_number=row["column_number"],
                name=row["name"],
            )
            for row in cursor.fetchall()
        ]
        conn.close()
        return units

    def has_requirements(self, article_number: str, point_letter: Optional[str] = None) -> bool:
        """Check if article/point has requirements in Додаток 3."""
        conn = self._get_conn()
        cursor = conn.cursor()

        if point_letter:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM appendix3_requirements
                WHERE article_number = ? AND point_letter = ?
            """, (article_number, point_letter))
        else:
            cursor.execute("""
                SELECT COUNT(*) as count
                FROM appendix3_requirements
                WHERE article_number = ? AND point_letter IS NULL
            """, (article_number,))

        count = cursor.fetchone()["count"]
        conn.close()
        return count > 0

    def get_requirements(
        self,
        article_number: str,
        point_letter: Optional[str],
        military_unit_columns: Optional[list[int]] = None,
    ) -> list[Requirement]:
        """Get requirements for article/point and military units."""
        conn = self._get_conn()
        cursor = conn.cursor()

        if point_letter:
            sql = """
                SELECT article_number, point_letter, military_unit_column, requirement
                FROM appendix3_requirements
                WHERE article_number = ? AND point_letter = ?
            """
            params = [article_number, point_letter]
        else:
            sql = """
                SELECT article_number, point_letter, military_unit_column, requirement
                FROM appendix3_requirements
                WHERE article_number = ? AND point_letter IS NULL
            """
            params = [article_number]

        if military_unit_columns:
            placeholders = ",".join("?" * len(military_unit_columns))
            sql += f" AND military_unit_column IN ({placeholders})"
            params.extend(military_unit_columns)

        sql += " ORDER BY military_unit_column"

        cursor.execute(sql, params)

        requirements = [
            Requirement(
                article_number=row["article_number"],
                point_letter=row["point_letter"],
                military_unit_column=row["military_unit_column"],
                requirement=row["requirement"],
            )
            for row in cursor.fetchall()
        ]
        conn.close()
        return requirements

    def get_health_requirements(self) -> dict[str, str]:
        """Get all health parameters and their thresholds."""
        conn = self._get_conn()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT DISTINCT health_parameter
            FROM health_requirements
            WHERE requirement IS NOT NULL
            ORDER BY health_parameter
        """)

        params = {}
        for row in cursor.fetchall():
            param = row["health_parameter"]
            # Map parameter names to relevance keywords
            param_lower = param.lower()
            if "зріст" in param_lower or "height" in param_lower:
                params["зріст"] = param
            elif "вага" in param_lower or "weight" in param_lower:
                params["вага"] = param
            elif "зір" in param_lower or "vision" in param_lower:
                params["зір"] = param
            elif "слух" in param_lower or "hearing" in param_lower:
                params["слух"] = param

        conn.close()
        return params
