"""Suitability assessment domain - works with military_medicine.db."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


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
