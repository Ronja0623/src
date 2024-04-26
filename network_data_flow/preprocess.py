import pandas as pd

class Preprocess:
    def __init__(self) -> None:
        pass

    def load_label_info(self, description_path, name_column="name", label_column="label"):
        """
        Get a dictionary saving label information.
        """
        try:
            df = pd.read_csv(description_path)
            label_info = dict(zip(df[name_column], df[label_column]))
            return label_info
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None