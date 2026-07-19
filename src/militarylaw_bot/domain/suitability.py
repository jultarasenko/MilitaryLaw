"""Suitability assessment domain - works with military_medicine.db."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional
from difflib import SequenceMatcher


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

    def _similarity_score(self, text: str, keyword: str) -> float:
        """Calculate similarity score between text and keyword (0.0 to 1.0)."""
        if not text or not keyword:
            return 0.0
        text_lower = text.lower()
        keyword_lower = keyword.lower()
        return SequenceMatcher(None, text_lower, keyword_lower).ratio()

    def _contains_fuzzy(self, text: str, keyword: str, threshold: float = 0.8) -> bool:
        """Check if text contains keyword with fuzzy matching (handles typos). Threshold 0.8 = 80% match."""
        if not text or not keyword:
            return False

        text_lower = text.lower()
        keyword_lower = keyword.lower()

        # Exact match (case-insensitive)
        if keyword_lower in text_lower:
            return True

        # Fuzzy match on whole text
        if self._similarity_score(text, keyword) >= threshold:
            return True

        # Try fuzzy match on words
        words = text_lower.split()
        for word in words:
            if self._similarity_score(word, keyword_lower) >= threshold:
                return True

        return False

    def search_by_keyword(self, keyword: str) -> list[Article]:
        """Search across all fields with fuzzy matching for typos and case-insensitive.

        Searches in: article keywords, group titles, and point descriptions.
        """
        conn = self._get_conn()
        cursor = conn.cursor()
        keyword_pattern = f"%{keyword}%"

        # First do exact search (fast)
        cursor.execute("""
            SELECT DISTINCT a.article_number, a.included_keywords, a.group_number
            FROM articles a
            LEFT JOIN appendix2_groups g ON a.group_number = g.group_number
            LEFT JOIN article_points ap ON a.article_number = ap.article_number
            WHERE LOWER(a.included_keywords) LIKE LOWER(?)
               OR LOWER(g.title) LIKE LOWER(?)
               OR LOWER(ap.description) LIKE LOWER(?)
            ORDER BY a.article_number
        """, (keyword_pattern, keyword_pattern, keyword_pattern))

        exact_results = cursor.fetchall()
        articles_dict = {}

        # Add exact matches
        for row in exact_results:
            articles_dict[row["article_number"]] = Article(
                number=row["article_number"],
                keywords=row["included_keywords"],
                group_number=row["group_number"],
            )

        # If few results, try fuzzy matching
        if len(articles_dict) < 5:
            cursor.execute("""
                SELECT DISTINCT a.article_number, a.included_keywords, a.group_number,
                       COALESCE(a.included_keywords, '') as keywords_text,
                       COALESCE(g.title, '') as group_title,
                       COALESCE(ap.description, '') as point_desc
                FROM articles a
                LEFT JOIN appendix2_groups g ON a.group_number = g.group_number
                LEFT JOIN article_points ap ON a.article_number = ap.article_number
            """)

            for row in cursor.fetchall():
                if row["article_number"] in articles_dict:
                    continue  # Already have this from exact match

                # Check fuzzy match
                if (self._contains_fuzzy(row["keywords_text"], keyword) or
                    self._contains_fuzzy(row["group_title"], keyword) or
                    self._contains_fuzzy(row["point_desc"], keyword)):
                    articles_dict[row["article_number"]] = Article(
                        number=row["article_number"],
                        keywords=row["included_keywords"],
                        group_number=row["group_number"],
                    )

        conn.close()

        # Sort by article number
        return sorted(articles_dict.values(), key=lambda a: int(a.number) if a.number.isdigit() else 999)

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
