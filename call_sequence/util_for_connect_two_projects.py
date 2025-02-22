import os
import shutil

from utils import load_label_info


def move_graph_to_family_folder(data_description, graph_path):
    """
    Move the graph to the family folder.
    """
    label_info = load_label_info(data_description)
    for family in label_info.values():
        family_folder = os.path.join(graph_path, family)
        os.makedirs(family_folder, exist_ok=True)

    for file in os.listdir(graph_path):
        if file.endswith(".png"):
            file_name = os.path.splitext(file)[0]
            file_name = file_name + ".exe"
            family = label_info[file_name.split("_")[0]]
            shutil.move(
                os.path.join(graph_path, file), os.path.join(graph_path, family, file)
            )

    print("Graphs are moved to the family folder.")
