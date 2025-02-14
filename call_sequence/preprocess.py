import os
import time
from collections import defaultdict

from apiCalling import DynamicAnalysis, clear_report_log
from imageGenerator import ImageGenerator
from utils import is_Proccessed, load_label_info


class Preprocess:
    def __init__(
        self,
        dataset_dir,
        sample_folder,
        data_description,
        color_map,
        json_path,
        csv_path,
        npy_path,
        graph_path,
        api_token,
        base_time,
        request_interval,
        max_wait_time,
        num_of_each_family,
    ):
        """
        Initialize the parameters
        """
        # input path
        self.DATASET_DIR = dataset_dir
        self.SAMPLE_FOLDER = sample_folder
        self.DATA_DESCRIPTION = data_description
        self.COLOR_MAP = color_map
        # output path
        self.JSON_PATH = json_path
        self.CSV_PATH = csv_path
        self.NPY_PATH = npy_path
        self.GRAPH_PATH = graph_path
        # api token
        self.API_TOKEN = api_token
        # dynamic analysis wait time (sec)
        self.BASE_TIME = base_time
        self.REQUEST_INTERVAL = request_interval
        self.MAX_WAIT_TIME = max_wait_time
        # balance the number of the sample in every family
        self.NUM_OF_EACH_FAMILY = num_of_each_family
        # load data description
        self.label_info = load_label_info(
            os.path.join(self.DATASET_DIR, self.DATA_DESCRIPTION)
        )

    def mkdir(self):
        """
        Create the output directories
        """
        os.makedirs(self.JSON_PATH, exist_ok=True)
        os.makedirs(self.CSV_PATH, exist_ok=True)
        os.makedirs(self.NPY_PATH, exist_ok=True)
        os.makedirs(self.GRAPH_PATH, exist_ok=True)

    def dynamic_analysis(self):
        """
        Perform dynamic analysis on the malware samples
        """
        if self.label_info is None:
            print("Data description was not loaded correctly.")
            return
        malware_dir_path = os.path.join(self.DATASET_DIR, self.DATA_DESCRIPTION)
        file_list = os.listdir(malware_dir_path)
        processed_list = os.listdir(self.JSON_PATH)
        processed_list = [
            os.path.splitext(file_name)[0] for file_name in processed_list
        ]
        processed_count = defaultdict(int)
        dynamic_analysis = DynamicAnalysis(self.API_TOKEN)
        for file in file_list:
            label = self.label_info.get(file)
            if not label:
                print("The file is not recorded in data description.")
                continue
            if processed_count[label] > self.NUM_OF_EACH_FAMILY:
                continue
            file_name = os.path.splitext(file)[0]
            if is_Proccessed(processed_list, file_name):
                processed_count[label] += 1
                continue
            task_id = dynamic_analysis.get_analysis_report_id(malware_dir_path, file)
            if task_id < 0:
                print("The file is not processed successfully.")
                continue
            time.sleep(self.BASE_TIME)
            wait_time_counter = self.BASE_TIME
            while wait_time_counter < self.MAX_WAIT_TIME:
                status_code = dynamic_analysis.save_report(
                    self.JSON_PATH, file_name, task_id
                )
                if status_code == 200:
                    break
                time.sleep(self.REQUEST_INTERVAL)
                wait_time_counter += self.REQUEST_INTERVAL

    def generate_image(self):
        """
        Generate the image from the dynamic analysis report
        """
        # extract the feature from the report
        file_list = os.listdir(self.JSON_PATH)
        processed_list = os.listdir(self.CSV_PATH)
        processed_list = [
            os.path.splitext(file_name)[0] for file_name in processed_list
        ]
        image_generator = ImageGenerator(
            self.JSON_PATH,
            self.CSV_PATH,
            self.NPY_PATH,
            self.GRAPH_PATH,
            self.COLOR_MAP,
        )
        for file in file_list:
            file_name = os.path.splitext(file)[0]
            if is_Proccessed(processed_list, file_name):
                continue
            image_generator.extract_feature(file_name)
        # get feature value of each category
        file_list = os.listdir(self.CSV_PATH)
        processed_list = os.listdir(self.NPY_PATH)
        processed_list = [
            os.path.splitext(file_name)[0] for file_name in processed_list
        ]
        for file in file_list:
            file_name = os.path.splitext(file)[0]
            if is_Proccessed(processed_list, file_name):
                continue
            image_generator.generate_vector_array(file_name)
        # generate the image
        file_list = os.listdir(self.NPY_PATH)
        processed_list = os.listdir(self.GRAPH_PATH)
        processed_list = [
            os.path.splitext(file_name)[0] for file_name in processed_list
        ]
        for file in file_list:
            file_name = os.path.splitext(file)[0]
            """if is_Proccessed(processed_list, file_name):
                continue"""
            image_generator.generate_image(file_name)
