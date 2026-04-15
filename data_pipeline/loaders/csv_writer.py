import pandas as pd
import os


class CSVWriter:

    @staticmethod
    def write(data, output_path):
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df = pd.DataFrame(data)
        df.to_csv(output_path, index=False)
