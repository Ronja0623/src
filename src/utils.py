import pandas as pd


def is_Proccessed(processed_list, file):
    """
    Check if the file is processed.
    """
    file_name = file.split(".")[0]
    return file_name in processed_list


def load_label_info(description_path, name_column="name", label_column="label"):
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
