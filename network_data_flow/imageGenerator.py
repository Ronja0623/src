import os

import cv2
import numpy as np


class ImageGenerator:
    def __init__(self, bytes_dir, graph_dir):
        # input path
        self.BYTES_DIR = bytes_dir
        # output path
        self.GRAPH_DIR = graph_dir

    def generate_graph(self, input_folder_name):
        input_dir_path = os.path.join(self.BYTES_DIR, input_folder_name)
        output_dir_path = os.path.join(self.GRAPH_DIR, input_folder_name)
        os.makedirs(output_dir_path, exist_ok=True)
        file_list = os.listdir(input_dir_path)
        for file_name in file_list:
            file_path = os.path.join(input_dir_path, file_name)
            file_name = os.path.splitext(file_name)[0]
            with open(file_path, "rb") as f:
                data = f.read()
            arr = np.frombuffer(data, dtype=np.uint8)
            image = arr.reshape(28, 28)
            image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)