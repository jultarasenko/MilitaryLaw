#!/usr/bin/env python3
"""
Parse medical data v5 - Group mapping by name:
- Parse appendix2 first to get group names and numbers
- Map articles to groups by matching додаток1 content with appendix2_groups titles
- Extract point-level clarifications without text bleeding
- Extract military unit names from додаток3 instead of hardcoding
- Support both Latin (I,V,X) and Cyrillic (Х,ХI,ХII...) Roman numerals
"""

import sqlite3
import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional

DATA_DIR = Path(__file__).parent.parent / "data" / "suitability"
DB_PATH = DATA_DIR / "military_medicine.db"


class MedicalDataParser:
    def __init__(self):
        self.articles: Dict[str, Dict] = {}
        self.article_to_group: Dict[str, int] = {}
        self.appendix2_groups: Dict[int, Dict] = {}
        self.appendix2_articles: Dict[str, Dict] = {}
        self.appendix2_points: Dict[str, Dict] = {}
        self.appendix3: List[Dict] = []
        self.appendix3_health: List[Dict] = []
        self.military_units: Dict[int, str] = {}

        # Table number mappings: [table_numbers] per article/point
        self.table_mappings = {
            ('13', 'в'): [1],
            ('13', 'г'): [2],
            ('35', 'а'): [3],
            ('36', None): [4],
            ('38', 'а'): [5, 6],
            ('38', 'б'): [7, 8, 9],
            ('38', 'в'): [10],
            ('39', None): [11],
            ('40', 'в'): [12],
            ('46', None): [13],
            ('61', 'в'): [14],
            ('62', 'в'): [15],
            ('64', 'в'): [16],
            ('66', None): [17, 18, 19],
        }

    def map_articles_to_groups_by_name(self, text_file: Path) -> None:
        """Map articles to groups by matching додаток1 structure with appendix2_groups names."""
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Build reverse map: group_name → group_number from appendix2_groups
        # Extract key parts and ICD codes for matching
        group_patterns: List[Tuple[int, str, str]] = []
        for group_num, group_data in self.appendix2_groups.items():
            title = group_data['title']
            # Extract first key phrase before parenthesis
            key_phrase = title.split('(')[0].strip() if '(' in title else title
            normalized = ' '.join(key_phrase.split())

            # Extract ICD codes from title (e.g., "D50-D89")
            icd_codes = re.findall(r'\([А-Яa-z]\d{2}[^\)]*\)', title)
            group_patterns.append((group_num, normalized, ' '.join(icd_codes)))

        # Parse додаток1 and match groups by name using fuzzy matching
        current_group_num = 0
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check if this line starts a group
            if line and not line.startswith('Стаття') and not line.startswith('Включено'):
                # Combine current line with next lines to handle line breaks
                combined_lines = [line]
                j = i + 1
                while j < len(lines) and len('\n'.join(combined_lines)) < 200:
                    next_line = lines[j].strip()
                    if next_line.startswith('Стаття') or next_line.startswith('Включено'):
                        break
                    combined_lines.append(next_line)
                    j += 1

                combined = ' '.join(combined_lines)
                normalized_combined = ' '.join(combined.split())

                # Try to match group name using fuzzy matching
                for group_num, key_phrase, icd_codes in group_patterns:
                    # Extract first 2-3 key words from phrase for flexible matching
                    key_words = key_phrase.split()[:3]
                    # Remove punctuation from key words for matching
                    key_words_clean = [re.sub(r'[^\w]', '', word) for word in key_words]

                    # Check if all key words appear in the text (case-insensitive, without punctuation)
                    normalized_combined_clean = re.sub(r'[^\w\s]', '', normalized_combined)
                    all_words_found = all(word.lower() in normalized_combined_clean.lower() for word in key_words_clean if word)

                    if all_words_found and len(key_phrase) > 10:
                        current_group_num = group_num
                        break

            # Parse article
            if line.startswith('Стаття '):
                match = re.match(r'Стаття\s+(\d+(?:-[а-я])?)', line)
                if match:
                    article_num = match.group(1)
                    self.article_to_group[article_num] = current_group_num

            i += 1

    def parse_appendix1(self, text_file: Path) -> None:
        """Parse Додаток 1 with better keyword extraction."""
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        i = 0
        while i < len(lines):
            line = lines[i].strip()

            if line.startswith('Стаття '):
                match = re.match(r'Стаття\s+(\d+(?:-[а-я])?)', line)
                if match:
                    article_num = match.group(1)
                    article_start = i

                    article_end = len(lines)
                    for j in range(i + 1, len(lines)):
                        if lines[j].strip().startswith('Стаття '):
                            article_end = j
                            break

                    article_text = ''.join(lines[article_start:article_end])
                    self._parse_single_article(article_num, article_text)

            i += 1

    def _parse_single_article(self, article_num: str, text: str) -> None:
        """Parse single article with better keyword handling."""
        # Extract included keywords
        included_match = re.search(r'Включено:\s*(.*?)(?=\n[а-я]\)|$)', text, re.DOTALL)

        if included_match:
            included_text = included_match.group(1).strip()
        else:
            # For articles without "Включено:", extract description as keywords
            lines = text.split('\n')
            # Find first non-empty line after "Стаття X"
            included_text = ""
            for j, line in enumerate(lines):
                if line.strip().startswith('Включено:'):
                    break
                if line.strip() and not line.strip().startswith('Стаття'):
                    included_text = line.strip()
                    break

        # Extract points
        points = {}
        point_pattern = r'\n([а-я])\)\s+(.*?)(?=\n[а-я]\)|$)'

        has_points = False
        for match in re.finditer(point_pattern, text, re.DOTALL):
            has_points = True
            point_letter = match.group(1)
            point_full_text = match.group(2)

            conclusion = ""
            for keyword in ['Непридатні', 'Тимчасово', 'Придатні']:
                if keyword in point_full_text:
                    conc_match = re.search(rf'{keyword}[^\n]*(?:\n(?!Придатні|Непридатні|Тимчасово|[А-Я])[^\n]*)*', point_full_text)
                    if conc_match:
                        conclusion = conc_match.group(0).strip()
                        break

            description = re.sub(r'\n(Непридатні|Тимчасово|Придатні).*', '', point_full_text, flags=re.DOTALL).strip()

            points[point_letter] = {
                'description': description,
                'conclusion': conclusion
            }

        if not has_points:
            conclusion = ""
            description = ""

            for keyword in ['Непридатні', 'Тимчасово', 'Придатні']:
                if keyword in text:
                    conc_match = re.search(rf'{keyword}[^\n]*(?:\n(?!Придатні|Непридатні|Тимчасово|[А-Я])[^\n]*)*', text)
                    if conc_match:
                        conclusion = conc_match.group(0).strip()
                        break

            if conclusion:
                description_match = re.search(r'Включено:[^\n]*\n+(.*?)\n\n' + re.escape(conclusion), text, re.DOTALL)
                if description_match:
                    description = description_match.group(1).strip()
            else:
                description_match = re.search(r'Включено:[^\n]*\n+(.*?)(?=\n\n[А-Я]|$)', text, re.DOTALL)
                if description_match:
                    description = description_match.group(1).strip()

            points[''] = {
                'description': description,
                'conclusion': conclusion
            }

        group_num = self.article_to_group.get(article_num, 0)
        self.articles[article_num] = {
            'number': article_num,
            'included': included_text,
            'points': points,
            'group': group_num
        }

    def parse_appendix2(self, text_file: Path) -> None:
        """Parse Додаток 2 with Cyrillic Roman numeral support."""
        with open(text_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Extract groups with their details (line-by-line approach)
        i = 0
        while i < len(lines):
            line = lines[i].strip()

            # Check for group header
            match = re.match(r'^([IVXХі]+)\.\s+(.+?)$', line)
            if match:
                roman_str = match.group(1)
                title = match.group(2).strip()

                try:
                    group_num = self._roman_to_int(roman_str)

                    # Collect details until next group or article marker
                    details_lines = []
                    for j in range(i + 1, len(lines)):
                        next_line = lines[j].strip()

                        # Stop at next group or article
                        if re.match(r'^[IVXХі]+\.', next_line) or re.match(r'^\d+\.\s+Стаття', next_line):
                            break

                        if next_line:  # Skip empty lines at start
                            details_lines.append(lines[j].rstrip())

                    details_text = '\n'.join(details_lines).strip()
                    details_text = self._clean_details(details_text) if details_text else ''

                    self.appendix2_groups[group_num] = {
                        'roman': roman_str,
                        'title': title,
                        'details': details_text
                    }
                except:
                    pass

            i += 1

        # Extract article-level clarifications ("3. Стаття 3: ..." or "2. Стаття 2")
        # Join lines back for regex-based extraction
        text = ''.join(lines)
        article_pattern = r'(\d+)\.\s+Стаття\s+(\d+(?:-[а-я])?)\s*:?\s*(.*?)(?=\n[IVXХі]+\.|\d+\.\s+Стаття|\d+\)\s+до\s+пункту|$)'

        for match in re.finditer(article_pattern, text, re.DOTALL):
            article_num = match.group(2)
            details_text = match.group(3).strip()

            details_text = self._clean_details(details_text)
            if details_text:
                self.appendix2_articles[article_num] = {
                    'article_number': article_num,
                    'details': details_text
                }

        # Extract point-level clarifications - line-by-line approach
        lines = text.split('\n')
        current_article = None

        for i, line in enumerate(lines):
            # Track current article
            article_match = re.match(r'(\d+)\.\s+Стаття\s+(\d+(?:-[а-я])?)', line)
            if article_match:
                current_article = article_match.group(2)

            # Look for point marker
            point_match = re.match(r'(\d+\))\s+до\s+пункту\s+[«»""]?([а-я])[«»""]?\s*:?\s*(.*?)$', line)
            if point_match and current_article:
                point_letter = point_match.group(2)

                # Collect content from rest of marker line + following lines
                details_lines = []

                # First, add text from the marker line itself (after "належать")
                rest_of_line = point_match.group(3)
                if rest_of_line:
                    details_lines.append(rest_of_line)

                # Then collect from following lines until next point/article marker
                for j in range(i + 1, len(lines)):
                    next_line = lines[j]

                    # Stop at next point or article
                    if re.match(r'\d+\)\s+до\s+пункту', next_line) or re.match(r'\d+\.\s+Стаття', next_line):
                        break

                    details_lines.append(next_line)

                details_text = '\n'.join(details_lines).strip()
                details_text = self._clean_details(details_text)

                if details_text:
                    key = f"{current_article}#{point_letter}"
                    self.appendix2_points[key] = {
                        'article_number': current_article,
                        'point_letter': point_letter,
                        'details': details_text
                    }

    def _clean_details(self, text: str) -> str:
        """Clean details text."""
        # Remove "до пункту «X» належать" marker from start if present
        text = re.sub(r'^до\s+пункту\s+[«»""]?[а-я][«»""]?\s*(?::\s*)?належать\s*:?\s*', '', text, flags=re.IGNORECASE)

        # Remove leading "належать" from start of line (for cases like "2) до пункту б належать текст")
        text = re.sub(r'^належать\s+', '', text, flags=re.IGNORECASE)

        # Remove trailing "належать:" markers (for cases without colon after pункту)
        text = re.sub(r'належать:\s*\n+', '', text, flags=re.IGNORECASE)
        text = re.sub(r'^[:\-\.\,\;\s]+', '', text)
        text = re.sub(r'\n+\*+.*$', '', text, flags=re.DOTALL)
        text = re.sub(r'\[фото\s*\d*\]', '[PHOTO]', text, flags=re.IGNORECASE)

        # Extract tables as [PHOTO] reference
        if re.search(r'\|\s*-+\s*\|', text):  # Markdown table marker
            text = '[PHOTO]'

        return text.strip()

    def _roman_to_int(self, roman: str) -> int:
        """Convert Latin or Cyrillic Roman numerals to integer."""
        # Map both Latin and Cyrillic
        val_latin = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}
        val_cyrillic = {'І': 1, 'V': 5, 'Х': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}

        total = 0
        prev_val = 0

        for char in reversed(roman):
            if char in val_latin:
                char_val = val_latin[char]
            elif char in val_cyrillic:
                char_val = val_cyrillic[char]
            else:
                raise ValueError(f"Invalid Roman character: {char}")

            if char_val < prev_val:
                total -= char_val
            else:
                total += char_val
            prev_val = char_val

        return total

    def parse_appendix3(self, csv_file: Path) -> None:
        """Parse Додаток 3."""
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        # Extract military unit names from row 2 (index 2) - column headers
        if len(rows) > 2:
            header_row = rows[2]
            for col_idx in range(3, min(14, len(header_row))):
                unit_name = header_row[col_idx].strip()
                if unit_name:
                    # Convert multiline names to single line
                    unit_name = ' '.join(unit_name.split())
                    military_unit_column = col_idx - 2
                    self.military_units[military_unit_column] = unit_name

        # Parse health requirements from rows 5-17 (indices 4-16, including continuation rows)
        current_param = ""
        current_qualifier = ""

        for row_idx in range(4, min(18, len(rows))):
            row = rows[row_idx]
            if not row:
                continue

            col0 = row[0].strip() if len(row) > 0 else ""
            col1 = row[1].strip() if len(row) > 1 else ""
            col2 = row[2].strip() if len(row) > 2 else ""

            # Update current parameter if col0 has text (primary parameter line)
            if col0:
                if col0.startswith('Стаття') or col0.startswith('Включено'):
                    break
                current_param = ' '.join(col0.split())
                current_qualifier = ""

            # Update qualifier from col2 if present
            if col2:
                current_qualifier = ' '.join(col2.split())

            # Update parameter if col1 has continuation text (sub-parameter like "Аномальна трихромазія")
            if col1:
                current_param = ' '.join(col1.split())
                current_qualifier = ""

            # Build full parameter name
            param_name = current_param
            if current_qualifier:
                param_name = f"{current_param} {current_qualifier}"

            # Extract requirements from columns 3 onwards
            for col_idx in range(3, min(14, len(row))):
                requirement = row[col_idx].strip() if col_idx < len(row) else ""

                if requirement:
                    # Convert multiline requirements to single line
                    requirement = ' '.join(requirement.split())
                    military_unit_column = col_idx - 2

                    if param_name:
                        self.appendix3_health.append({
                            'health_parameter': param_name,
                            'military_unit_column': military_unit_column,
                            'requirement': requirement
                        })

        first_article_row = None
        for idx, row in enumerate(rows):
            if row and row[0].strip().startswith('Стаття'):
                first_article_row = idx
                break

        if first_article_row is None:
            return

        for row_idx in range(first_article_row, len(rows)):
            row = rows[row_idx]
            if not row or not row[0].strip():
                continue

            article_point = row[0].strip()
            if not article_point.startswith('Стаття'):
                continue

            match = re.match(r'Стаття\s+(\d+)(?:-([а-я]))?', article_point)
            if not match:
                continue

            article_num = match.group(1)
            point_letter = match.group(2) if match.group(2) else None

            for col_idx in range(3, min(14, len(row))):
                requirement = row[col_idx].strip() if col_idx < len(row) else ""

                if requirement:
                    requirement = requirement.replace('\n', ' ').strip()
                    military_unit_column = col_idx - 2

                    self.appendix3.append({
                        'article_number': article_num,
                        'point_letter': point_letter,
                        'military_unit_column': military_unit_column,
                        'requirement': requirement
                    })

    def create_database(self) -> None:
        """Create final database."""
        if DB_PATH.exists():
            DB_PATH.unlink()

        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE articles (
                article_number TEXT PRIMARY KEY,
                included_keywords TEXT,
                group_number INTEGER
            )
        ''')

        cursor.execute('''
            CREATE TABLE article_points (
                id INTEGER PRIMARY KEY,
                article_number TEXT NOT NULL,
                point_letter TEXT,
                description TEXT,
                conclusion TEXT,
                FOREIGN KEY(article_number) REFERENCES articles(article_number),
                UNIQUE(article_number, point_letter)
            )
        ''')

        cursor.execute('''
            CREATE TABLE appendix2_groups (
                group_number INTEGER PRIMARY KEY,
                roman_numeral TEXT NOT NULL,
                title TEXT NOT NULL,
                details TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE appendix2_articles (
                id INTEGER PRIMARY KEY,
                article_number TEXT NOT NULL UNIQUE,
                details TEXT,
                table_number TEXT,
                FOREIGN KEY(article_number) REFERENCES articles(article_number)
            )
        ''')

        cursor.execute('''
            CREATE TABLE appendix2_points (
                id INTEGER PRIMARY KEY,
                article_number TEXT NOT NULL,
                point_letter TEXT NOT NULL,
                details TEXT,
                table_number TEXT,
                FOREIGN KEY(article_number) REFERENCES articles(article_number),
                UNIQUE(article_number, point_letter)
            )
        ''')

        cursor.execute('''
            CREATE TABLE health_requirements (
                id INTEGER PRIMARY KEY,
                health_parameter TEXT NOT NULL,
                military_unit_column INTEGER,
                requirement TEXT,
                FOREIGN KEY(military_unit_column) REFERENCES military_units(column_number)
            )
        ''')

        cursor.execute('''
            CREATE TABLE military_units (
                column_number INTEGER PRIMARY KEY,
                name TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE appendix3_requirements (
                id INTEGER PRIMARY KEY,
                article_number TEXT NOT NULL,
                point_letter TEXT,
                military_unit_column INTEGER,
                requirement TEXT,
                FOREIGN KEY(article_number) REFERENCES articles(article_number),
                FOREIGN KEY(military_unit_column) REFERENCES military_units(column_number)
            )
        ''')

        # Insert military units
        for col_num, name in self.military_units.items():
            cursor.execute(
                'INSERT INTO military_units (column_number, name) VALUES (?, ?)',
                (col_num, name)
            )

        # Insert articles with group number
        for article_num in sorted(self.articles.keys(), key=self._sort_key):
            article_data = self.articles[article_num]
            cursor.execute(
                'INSERT INTO articles (article_number, included_keywords, group_number) VALUES (?, ?, ?)',
                (article_num, article_data['included'], article_data['group'])
            )

            # Insert points
            for point_letter in sorted(article_data['points'].keys()):
                point_data = article_data['points'][point_letter]
                cursor.execute(
                    'INSERT INTO article_points (article_number, point_letter, description, conclusion) VALUES (?, ?, ?, ?)',
                    (article_num, point_letter if point_letter else None, point_data['description'], point_data['conclusion'])
                )

        # Insert appendix2 groups
        for group_num, group_data in self.appendix2_groups.items():
            cursor.execute(
                'INSERT INTO appendix2_groups (group_number, roman_numeral, title, details) VALUES (?, ?, ?, ?)',
                (group_num, group_data['roman'], group_data['title'], group_data['details'])
            )

        # Insert appendix2 articles
        for article_num, data in self.appendix2_articles.items():
            table_numbers = self.table_mappings.get((article_num, None))
            table_number_str = ','.join(map(str, table_numbers)) if table_numbers else None
            cursor.execute(
                'INSERT INTO appendix2_articles (article_number, details, table_number) VALUES (?, ?, ?)',
                (article_num, data['details'], table_number_str)
            )

        # Insert appendix2 points
        for key, data in self.appendix2_points.items():
            article_num = data['article_number']
            point_letter = data['point_letter']
            table_numbers = self.table_mappings.get((article_num, point_letter))
            table_number_str = ','.join(map(str, table_numbers)) if table_numbers else None
            cursor.execute(
                'INSERT INTO appendix2_points (article_number, point_letter, details, table_number) VALUES (?, ?, ?, ?)',
                (article_num, point_letter, data['details'], table_number_str)
            )

        # Insert health requirements
        for health_req in self.appendix3_health:
            cursor.execute(
                'INSERT INTO health_requirements (health_parameter, military_unit_column, requirement) VALUES (?, ?, ?)',
                (health_req['health_parameter'], health_req['military_unit_column'], health_req['requirement'])
            )

        # Insert appendix3
        for req in self.appendix3:
            cursor.execute(
                'INSERT INTO appendix3_requirements (article_number, point_letter, military_unit_column, requirement) VALUES (?, ?, ?, ?)',
                (req['article_number'], req['point_letter'], req['military_unit_column'], req['requirement'])
            )

        conn.commit()
        conn.close()
        print(f"✓ Database v5 created: {DB_PATH}")
        print(f"✓ Articles: {len(self.articles)}")
        print(f"✓ Appendix 2 groups: {len(self.appendix2_groups)}")
        print(f"✓ Appendix 2 articles: {len(self.appendix2_articles)}")
        print(f"✓ Appendix 2 points: {len(self.appendix2_points)}")
        print(f"✓ Health requirements: {len(self.appendix3_health)}")
        print(f"✓ Appendix 3 requirements: {len(self.appendix3)}")

    def _sort_key(self, article_num: str) -> Tuple:
        """Sort article numbers naturally."""
        parts = article_num.split('-')
        num = int(parts[0])
        letter = parts[1] if len(parts) > 1 else ''
        return (num, letter)

    def run(self) -> None:
        """Execute full parsing pipeline."""
        print("Parsing medical data...")

        appendix1_txt = DATA_DIR / "додаток1.txt"
        appendix2_txt = DATA_DIR / "додаток2.txt"
        appendix3_csv = DATA_DIR / "додаток3.csv"

        if not appendix1_txt.exists() or not appendix2_txt.exists() or not appendix3_csv.exists():
            print("Error: Required files not found.")
            return

        print(f"Reading {appendix2_txt.name} (for group names)...")
        self.parse_appendix2(appendix2_txt)

        print(f"Mapping articles to groups using {appendix1_txt.name}...")
        self.map_articles_to_groups_by_name(appendix1_txt)

        print(f"Reading {appendix1_txt.name} (for article details)...")
        self.parse_appendix1(appendix1_txt)

        print(f"Reading {appendix3_csv.name}...")
        self.parse_appendix3(appendix3_csv)

        print("Creating database...")
        self.create_database()


if __name__ == "__main__":
    parser = MedicalDataParser()
    parser.run()
