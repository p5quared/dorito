import csv
import os
from typing import Dict, Any, List
from shared.interfaces import DataWriter


# Writer interface is now in shared.interfaces as DataWriter


class CSVDataWriter(DataWriter):
    """Writer that outputs data to CSV files"""

    def __init__(self, filename: str, buffer_size: int, fieldnames: List[str]):
        self._filename = filename
        self._fieldnames = fieldnames
        self._buffer_size = buffer_size
        self._buffer: List[Dict[str, Any]] = []

    def write(self, data: Dict[str, Any]) -> None:
        """Write data to buffer, flush if buffer is full"""
        if not data:  # Skip empty data
            return

        self._buffer.append(data.copy())  # Make a copy to avoid mutations
        if len(self._buffer) >= self._buffer_size:
            self.flush()

    def flush(self) -> None:
        """Flush buffered data to CSV file"""
        if not self._buffer:
            return

        file_exists = os.path.exists(self._filename)
        mode = "a" if file_exists else "w"

        with open(self._filename, mode, newline="") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=self._fieldnames)

            if not file_exists:
                writer.writeheader()

            for item in self._buffer:
                # Clean body text for CSV compatibility
                if "body" in item and item["body"]:
                    item["body"] = self._clean_text_for_csv(item["body"])
                writer.writerow(item)

        self._buffer.clear()

    def _clean_text_for_csv(self, text: str) -> str:
        """Clean text for CSV output"""
        return text.replace("\n", " ").replace("\r", " ").replace(",", " ").strip()


# Legacy class for backward compatibility
class LocalCSVWriter(CSVDataWriter):
    """Deprecated - use CSVDataWriter instead"""

    def __init__(self, fname: str, buffer_size: int, fieldnames: List[str]):
        super().__init__(fname, buffer_size, fieldnames)
        self.fname = fname  # Legacy property
        self.fieldnames = fieldnames  # Legacy property
        self.buffer_size = buffer_size  # Legacy property
        self.buffer = self._buffer  # Legacy property alias
