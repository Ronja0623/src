import os
import time

import requests
import ujson


class DynamicAnalysis:
    def __init__(self, API_TOKEN):
        self.HEADERS = {"Authorization": f"Bearer {API_TOKEN}"}

    def get_analysis_report_id(
        self, dir_path, file_name, url="http://localhost:8090/tasks/create/file"
    ):
        """
        Submit malware and then get report id
        """
        input_file_path = os.path.join(dir_path, file_name)
        with open(input_file_path, mode="rb") as sample:
            files = {"file": ("temp_file_name", sample)}
            # POST
            r = requests.post(url, headers=self.HEADERS, files=files)
            time.sleep(1)
            # get task_id (report id)
            if "task_id" in r.json():
                return r.json()["task_id"]
            else:
                return -1

    def save_report(
        self,
        dir_path,
        file_name,
        task_id,
        url="http://localhost:8090/tasks/report/",
    ):
        """
        Get report and save as json file
        """
        output_file_path = os.path.join(dir_path, file_name + ".json")
        # GET
        try:
            response = requests.get(url + str(task_id), headers=self.HEADERS)
            if response.status_code != 200:
                return response.status_code
            response.raise_for_status()
            with open(output_file_path, "w") as json_file:
                report = ujson.loads(response.text)
                ujson.dump(report, json_file)
        except requests.exceptions.RequestException as e:
            print("Error fetching report:", e)
            return -1
        except ujson.JSONDecodeError as e:
            print("Error decoding JSON response:", e)
            return -2
        return 200


def clear_report_log(headers, check_range, url="http://localhost:8090/tasks/delete/"):
    """
    Clear all report log after processing.

    # TODO: Wait to fix, cannot delete log now.
    """
    clear_count = 0
    if check_range < 1:
        check_range = 1000
    for task_id in range(check_range):
        try:
            response = requests.get(url + str(task_id), headers=headers)
            if response.status_code == 200:
                clear_count += 1
        except Exception as e:
            print("An exception occurred:", type(e))
    print(f"Successfully clear {clear_count} log.")
