import pandas as pd


def is_Proccessed(processed_list, file_name):
    """
    Check if the file is processed.
    """
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


def hex_to_rgb(hex_color):
    """
    Transform hex color to RGB color.
    """
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
