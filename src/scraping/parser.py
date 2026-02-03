import re
from datetime import date
from decimal import Decimal, InvalidOperation
from io import BytesIO
from typing import Optional

import pandas as pd

from config.logging import logger
from src.scraping.enums import Technology, Region


MONTH_NAMES = {
    "january": 1, "february": 2, "march": 3, "april": 4,
    "may": 5, "june": 6, "july": 7, "august": 8,
    "september": 9, "october": 10, "november": 11, "december": 12,
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


class AuctionParser:

    def __init__(self, source_file: str = ""):
        self.source_file = source_file

    def parse_excel(self, file_content: bytes) -> list[dict]:
        try:
            xlsx = pd.ExcelFile(BytesIO(file_content))
        except Exception as e:
            logger.error(f"Error loading Excel file: {e}")
            return []

        records = []
        for sheet_name in xlsx.sheet_names:
            records.extend(self._parse_sheet(xlsx, sheet_name))

        return records

    def _parse_sheet(self, xlsx: pd.ExcelFile, sheet_name: str) -> list[dict]:
        df = pd.read_excel(xlsx, sheet_name=sheet_name, header=None)

        if df.empty:
            return []

        header_info = self._find_headers(df)
        if not header_info:
            return []

        header_row = header_info["row"]
        df.columns = df.iloc[header_row]
        df = df.iloc[header_row + 1:].reset_index(drop=True)

        auction_date = self._extract_date(df, sheet_name)
        records = []

        for _, row in df.iterrows():
            record = self._parse_row(row, header_info, auction_date)
            if record:
                records.append(record)

        return records

    def _find_headers(self, df: pd.DataFrame) -> Optional[dict]:
        for row_idx in range(min(50, len(df))):
            row_text = " ".join(str(v).lower() for v in df.iloc[row_idx] if pd.notna(v))

            if "volume" in row_text and any(kw in row_text for kw in {"offered", "allocated", "auctionned", "sold"}):
                headers = {"row": row_idx}

                for col_idx, val in enumerate(df.iloc[row_idx]):
                    if pd.isna(val):
                        continue
                    val_lower = str(val).lower()

                    if "offered" in val_lower or "auctionned" in val_lower:
                        headers["volume_offered"] = df.columns[col_idx] if row_idx > 0 else col_idx
                        headers["volume_offered_idx"] = col_idx
                    elif "allocated" in val_lower or "sold" in val_lower:
                        headers["volume_allocated"] = df.columns[col_idx] if row_idx > 0 else col_idx
                        headers["volume_allocated_idx"] = col_idx
                    elif "price" in val_lower or "average" in val_lower:
                        headers["price"] = df.columns[col_idx] if row_idx > 0 else col_idx
                        headers["price_idx"] = col_idx

                return headers

        return None

    def _parse_row(self, row: pd.Series, headers: dict, auction_date: Optional[date]) -> Optional[dict]:
        first_val = row.iloc[0] if len(row) > 0 else None
        if pd.isna(first_val) or not str(first_val).strip():
            return None

        first_cell = str(first_val)
        region = Region.from_string(first_cell)
        technology = Technology.from_string(first_cell)

        if not technology and len(row) > 1:
            second_val = row.iloc[1]
            if pd.notna(second_val):
                technology = Technology.from_string(str(second_val))

        if not region and not technology:
            return None

        vol_offered = self._get_column_value(row, headers, "volume_offered_idx")
        vol_allocated = self._get_column_value(row, headers, "volume_allocated_idx")

        if vol_offered is None and vol_allocated is None:
            return None

        return {
            "auction_date": auction_date or date.today(),
            "region": region.value if region else "All Regions",
            "technology": technology.value if technology else "All Technologies",
            "volume_offered_mwh": vol_offered,
            "volume_allocated_mwh": vol_allocated,
            "weighted_avg_price_eur": self._get_column_value(row, headers, "price_idx"),
            "source_file": self.source_file,
        }

    def _get_column_value(self, row: pd.Series, headers: dict, key: str) -> Optional[Decimal]:
        if key not in headers:
            return None
        idx = headers[key]
        if idx >= len(row):
            return None
        return self._parse_number(row.iloc[idx])

    def _extract_date(self, df: pd.DataFrame, sheet_name: str) -> Optional[date]:
        text = sheet_name.lower() + " "

        for row_idx in range(min(10, len(df))):
            for col_idx in range(min(5, len(df.columns))):
                val = df.iloc[row_idx, col_idx]
                if pd.notna(val):
                    text += str(val).lower() + " "

        for month_name, month_num in MONTH_NAMES.items():
            if month_name in text:
                year_match = re.search(r"20\d{2}", text)
                if year_match:
                    return date(int(year_match.group()), month_num, 1)

        return None

    @staticmethod
    def _parse_number(value) -> Optional[Decimal]:
        if value is None or pd.isna(value):
            return None

        if isinstance(value, (int, float)):
            return Decimal(str(value))

        try:
            cleaned = str(value).replace(",", "").replace(" ", "").strip()
            if cleaned in ("", "-", "n/a", "N/A"):
                return None
            return Decimal(cleaned)
        except (InvalidOperation, ValueError):
            return None
