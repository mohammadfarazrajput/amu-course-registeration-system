import json
import os


class JSONWriter:

    @staticmethod
    def write(data: list, output_path: str):
        """
        Writes list of dictionaries to a JSON file.
        Creates folder automatically if not present.
        """

        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        print(f"JSON written to: {output_path}")
