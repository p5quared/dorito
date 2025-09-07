import csv
import os
from typing import Dict, Any, List
from shared.interfaces import DataWriter


class CSVDataWriter(DataWriter):
    """Writer that outputs data to CSV files"""
    def __init__(self, filename: str, fieldnames: List[str]):
        self._filename = filename
        self._fieldnames = fieldnames
        self._header_written = False

    def write(self, data: Dict[str, Any]) -> None:
        if not data:
            return

        cleaned_data = data.copy()
        if "body" in cleaned_data and cleaned_data["body"]:
            cleaned_data["body"] = self._clean_text_for_csv(cleaned_data["body"])

        with open(self._filename, "a", newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self._fieldnames)
            
            if not self._header_written:
                writer.writeheader()
                self._header_written = True
            
            writer.writerow(cleaned_data)

    def _clean_text_for_csv(self, text: str) -> str:
        """Clean text for CSV output"""
        return text.replace("\n", " ").replace("\r", " ").replace(",", " ").strip()
