import csv
import os

import cv2
import numpy as np
import pandas as pd
import ujson
from utils import hex_to_rgb


class ImageGenerator:
    def __init__(
        self, input_dir, output_csv_dir, output_npy_dir, output_graph_dir, color_map
    ):
        """
        Initialize the parameters
        """
        self.input_dir = input_dir
        self.output_csv_dir = output_csv_dir
        self.output_npy_dir = output_npy_dir
        self.output_graph_dir = output_graph_dir
        self.color_map = color_map
        self.category = [
            "networking",
            "register",
            "service",
            "file",
            "hardware",
            "message",
            "process",
            "system",
            "Shellcode",
            "Keylogging",
            "Obfuscation",
            "password dumping",
            "anti-debugging",
            "handle manipulation",
            "high risk",
            "other",
        ]

    def extract_feature(self, file_name):
        """
        Extract behavior as feature and save as a csv file
        """
        input_file_path = os.path.join(self.input_dir, f"{file_name}.json")
        output_file_path = os.path.join(self.output_csv_dir, f"{file_name}.csv")
        with open(input_file_path, "r", encoding="utf-8") as input, open(
            output_file_path, "w", newline=""
        ) as output:
            # setup the reader
            report = ujson.load(input)
            # define field names
            field_name = ["category", "time"]
            # setup the writer
            writer = csv.DictWriter(output, fieldnames=field_name)
            # writer the header
            writer.writeheader()
            # iterate over the processes
            for i, process in enumerate(report["behavior"]["processes"]):
                # iterate over the calls within a process
                for call in process["calls"]:
                    try:
                        # write the call details to the CSV
                        writer.writerow(
                            {
                                "category": call["category"],
                                "time": call["time"],
                            }
                        )
                    except KeyError as e:
                        print("Error calling structure:", e)

    def get_category(self, category):
        """
        Get the category of the call
        """
        category_dict = {
            "networking": "networking",
            "register": "register",
            "service": "service",
            "file": "file",
            "hardware": "hardware",
            "message": "message",
            "process": "process",
            "thread": "thread",
            "system": "system",
            "Shellcode": "Shellcode",
            "Keylogging": "Keylogging",
            "Obfuscation": "Obfuscation",
            "password dumping": "password dumping",
            "hash": "password dumping",
            "anti-debugging": "anti-debugging",
            "reversing": "anti-debugging",
            "handle manipulation": "handle manipulation",
            "high risk": "high risk",
        }
        if category in category_dict:
            return self.category.index(category)
        return "other"

    def generate_vector_array(self, file_name):
        df = pd.read_csv(
            os.path.join(self.output_csv_dir, f"{file_name}.csv"), encoding="utf-8"
        )
        start_time = df["time"].min()
        end_time = df["time"].max()
        # create an array of bin edges with 16 equal intervals between start and end time
        time_bins = np.linspace(
            start_time, end_time, num=17
        )  # 16 intervals + 1 for the end point
        # assign each time entry to a time bin
        df["time_bin"] = (
            np.digitize(df["time"], bins=time_bins) - 1
        )  # adjust to get zero-based indexing
        # ensure the categories are categorical for efficiency
        df["category"] = df["category"].astype("category")
        # create a mapping from category to index
        category_to_index = {cat: idx for idx, cat in enumerate(self.category)}
        # initialize the image data array
        feature_array = np.zeros((16, len(self.category)))
        # group by time_bin and category, then count the occurrences
        grouped = df.groupby(["time_bin", "category"]).size().unstack(fill_value=0)
        # reindex the DataFrame to ensure it has 16 rows, representing each time interval
        grouped = grouped.reindex(range(16), fill_value=0)
        # assign the counts to the appropriate places in the image_data array
        for cat in grouped.columns:
            cat_idx = category_to_index.get(cat)
            if cat_idx is not None:
                feature_array[:, cat_idx] = grouped[cat].values
        np.save(os.path.join(self.output_npy_dir, f"{file_name}.npy"), feature_array)

    def get_color(self, type, num):
        """
        Get the color of the call category
        # TODO: Accelerate with numpy
        """
        if num == 0:
            color = "#FFFFFF"
        else:
            with open(self.color_map, "r") as f:
                color_map = ujson.load(f)
                for key in reversed(color_map[type]):
                    if num > int(key):
                        color = color_map[type][key]
                        break
        return hex_to_rgb(color)

    def generate_image(self, file_name):
        """
        Generate the image from the feature array
        """
        input_file_path = os.path.join(self.output_npy_dir, f"{file_name}.npy")
        output_file_path = os.path.join(self.output_graph_dir, f"{file_name}.png")
        feature_array = np.load(input_file_path)
        image_data = np.zeros((16, 16, 3), dtype=np.uint8)
        for i in range(16):
            for j in range(16):
                image_data[i, j] = self.get_color(self.category[j], feature_array[i, j])
        # resize image from 16x16 to 224x224 (16x14=224)
        resized_image = np.repeat(np.repeat(image_data, 14, axis=0), 14, axis=1)
        cv2.imwrite(output_file_path, resized_image)
