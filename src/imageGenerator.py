import csv
import os

import ujson

class ImageGenerator:
    def __init__(self, input_dir, output_dir):
        self.input_dir = input_dir
        self.output_dir = output_dir

    def extract_feature(self, input_dir, output_dir, file_name):
        """
        Extract behavior as feature and save as a csv file
        """
        input_file_path = os.path.join(input_dir, f"{file_name}.json")
        output_file_path = os.path.join(output_dir, f"{file_name}.csv")
        with open(input_file_path, "r") as input, open(output_file_path, "w") as output:
            # setup the reader
            report = ujson.load(input)
            # define field names
            field_name = ["process_index", "call_category", "call_api", "call_time"]
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
                                "process_index": i,
                                "call_category": call["category"],
                                "call_api": call["api"],
                                "call_time": call["time"],
                            }
                        )
                    except KeyError as e:
                        print("Error calling structure:", e)
