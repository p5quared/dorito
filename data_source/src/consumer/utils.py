import csv
import os

class Writer:
    def __init__(self) -> None:
        pass

    def write(self, data):
        raise NotImplementedError("Subclasses must implement this method")

    def flush(self):
        raise NotImplementedError("Subclasses must implement this method")



class LocalCSVWriter(Writer):
    def __init__(self, fname: str, buffer_size: int, fieldnames: list[str]):
        super().__init__()
        self.fname = fname
        self.fieldnames = fieldnames
        self.buffer_size = buffer_size
        self.buffer = []

    def write(self, data):
        self.buffer.append(data)
        if len(self.buffer) > self.buffer_size:
            self.flush()

    def flush(self):
        if os.path.exists(self.fname):
            with open(self.fname, "a") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)
                for item in self.buffer:
                    item["body"] = item["body"].replace("\n", " ").replace("\r", " ").replace(",", " ")
                    writer.writerow(item)
        else:
            with open(self.fname, "w") as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=self.fieldnames)
                writer.writeheader()
                for item in self.buffer:
                    item["body"] = item["body"].replace("\n", " ").replace("\r", " ").replace(",", " ")
                    writer.writerow(item)
        self.buffer = []
