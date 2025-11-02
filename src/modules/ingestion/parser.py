"""
CSV Parser for UAM data ingestion.
"""

import pandas as pd
from pathlib import Path
from typing import Tuple
from ...interfaces.errors import ValidationError, ProcessingError
from ...interfaces.ports import Clock


class CSVParser:
    """
    Parses UAM CSV files.

    Example:
        parser = CSVParser(clock=SystemClock())
        df, is_full = parser.parse("uam_data.csv")
    """

    def __init__(self, clock):
        self.clock = clock

    def parse(self, filepath: str) -> Tuple[pd.DataFrame, bool]:
        """
        Parse CSV file and detect if full or incremental load.

        Returns:
            (DataFrame, is_full_load)
        """
        try:
            filepath = Path(filepath)
            if not filepath.exists():
                raise ValidationError(
                    message=f"CSV file not found: {filepath}",
                    context={"filepath": str(filepath)}
                )

            df = pd.read_csv(filepath)
            is_full = self._detect_full_load(df)
            return df, is_full

        except Exception as e:
            raise ProcessingError(
                message=f"CSV parsing failed: {str(e)}",
                context={"filepath": str(filepath)}
            )

    def _detect_full_load(self, df: pd.DataFrame) -> bool:
        """Detect if this is full or incremental load."""
        # Heuristic: if we have >100 apps, likely full load
        if "app_id" in df.columns:
            return len(df["app_id"].unique()) > 100
        return True
