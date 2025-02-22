import csv
import os
import time

import pandas as pd
from malwareClassification import MalwareClassification
from preprocess import Preprocess

"""
Set the parameters
"""
# input path
DATASET_DIR = "Dataset"
SAMPLE_FOLDER = "malware"
DATA_DESCRIPTION = "dataset.csv"
SELECTED_FAMILY = "selected.csv"
COLOR_MAP = "APIColorMappingRule.json"
# output path: preprocess
JSON_PATH = "json"
CSV_PATH = "csv"
NPY_PATH = "npy"
GRAPH_PATH = "graph"
# output path: malware classification
MODEL_DIR = "model"
# api token
API_TOKEN = "API_TOKEN"  # replace with your own API token
# dynamic analysis wait time (sec)
BASE_TIME = 100  # at least wait for BASE_TIME sec
REQUEST_INTERVAL = 2  # then check if it is finished every REQUEST_INTERVAL sec
MAX_WAIT_TIME = 300  # if wait over MAX_WAIT_TIME sec, skip
# balance the number of the sample in every family
NUM_OF_EACH_FAMILY = 10
# hyperparameters
batch_size = 8
learning_rate = 1e-3
train_ratio = 0.8
epochs = 10

"""
Preprocess: Dynamic analysis and generate image
"""
preprocess = Preprocess(
    DATASET_DIR,
    SAMPLE_FOLDER,
    DATA_DESCRIPTION,
    COLOR_MAP,
    JSON_PATH,
    CSV_PATH,
    NPY_PATH,
    GRAPH_PATH,
    API_TOKEN,
    BASE_TIME,
    REQUEST_INTERVAL,
    MAX_WAIT_TIME,
    NUM_OF_EACH_FAMILY,
)
# create the output directories
preprocess.mkdir()
# dynamic analysis
preprocess.dynamic_analysis()
# generate image
preprocess.generate_image()


"""
Malware Classification: Train the model
"""
# mkdir for model
os.makedirs(MODEL_DIR, exist_ok=True)
# set the path
t = time.localtime()
MODEL_PATH = os.path.join(MODEL_DIR, time.strftime("%Y%m%d_%H%M", t))
LOG_PATH = os.path.join(MODEL_PATH, "log.txt")
############################################
# TODO: wait for reorganize
malwareClassification = MalwareClassification(
    GRAPH_PATH, MODEL_PATH, LOG_PATH, batch_size, learning_rate
)
# read selected families
selected = pd.read_csv(os.path.join(DATASET_DIR, SELECTED_FAMILY))
with open(os.path.join(DATASET_DIR, DATA_DESCRIPTION), "r", newline="") as csvfile:
    rows = csv.reader(csvfile)
    next(rows)  # skip header
    for row in rows:
        if row[1] not in selected["family"].values:  # skip unwanted families
            continue
        # create a dictionary with family name as key and path as value
        malwareClassification.label_file[row[0]] = os.path.join(GRAPH_PATH, row[1])
# create directories for each family
for i in malwareClassification.label_file.keys():
    os.makedirs(malwareClassification.label_file[i], exist_ok=True)
# move graphs to family folders
"""from util_for_connect_two_projects import move_graph_to_family_folder
move_graph_to_family_folder(os.path.join(DATASET_DIR, DATA_DESCRIPTION), GRAPH_PATH)"""
malwareClassification.setModel(train_ratio)
malwareClassification.trainModel(epochs)
