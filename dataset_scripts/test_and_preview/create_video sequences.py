import os
import cv2
import numpy as np
import torch
from tqdm import tqdm
from ultralytics import YOLO
from ultralytics.utils.plotting import Annotator

from classification_experiments.combined_model import CzechRailwayLightModel




def get_jpg_files(path):
    """
    The function `get_jpg_files` retrieves a list of all JPG and JPEG files within a specified directory
    and its subdirectories.

    :param path: The `get_jpg_files` function you provided is designed to retrieve a list of all JPG and
    JPEG files within a specified directory and its subdirectories. To use this function, you need to
    provide the `path` parameter, which should be the directory path where you want to search for JPG
    and
    :return: The function `get_jpg_files(path)` returns a list of full file paths for all the JPG/JPEG
    files found in the specified directory `path` and its subdirectories.
    """
    jpg_files = []

    # Walk through directory and subdirectories
    for root, dirs, files in os.walk(path):
        # Find all jpg/jpeg files in current directory
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg')):
                # Create full file path and add to list
                full_path = os.path.join(root, file)
                jpg_files.append(full_path)

    return jpg_files


# Load YOLOv5 model
model_combined = CzechRailwayLightModel(
    detection_net_path="../../classification_experiments/czech_railway_light_detection_backbone/detection_backbone/weights/best.pt",
    classification_net_path="../../classification_experiments/czech_railway_lights_net.pt"
                               )

# Load YOLO model
model_yolo = YOLO("../../experiment_results/yolo/CRL_extended_v2/60_lr001_0_yolov8n.pt_0.5/weights/best.pt")

# Open video file
video_path = "../../reconstructed/videos/"
times_path = "../../reconstructed/preview"

device = torch.device("cpu")

model_combined.yolo_model.to(device)
model_combined.classification_head.to(device)


def detect_yolo():
    out.write(model_yolo(frame, conf=0.65, iou=0.55, verbose=False)[0].plot())

def detect_combined():
    results, classes = model_combined(frame, conf=0.65, iou=0.55, verbose=False)
    for result in results:
        annotator = Annotator(frame, line_width=2)
        boxes = result.boxes
        for cls, box in zip(classes, boxes):
                b = box.xyxy[0]  # get box coordinates in (left, top, right, bottom) format
                c = cls

                annotator.box_label(b, model_combined.names[int(c)])
    out.write(frame)

to_process = {}
for j in os.listdir(times_path):
    to_process[j] = sorted([float(i[i.rfind("/")+1:].replace("_clean.jpg", "")) for i in get_jpg_files(times_path + "/" + j) if "_clean.jpg" in i])
    try:
        cap = cv2.VideoCapture(video_path + j + ".mp4")
        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        # Define the codec and create VideoWriter object
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        out = cv2.VideoWriter(j + '.mp4', fourcc, fps, (frame_width, frame_height))

        while cap.isOpened():
            for i in tqdm(to_process[j]):

                frame_number = int(fps * (i - 1))
                cap.set(cv2.CAP_PROP_POS_FRAMES,
                        frame_number)

                for _ in range(int(cap.get(cv2.CAP_PROP_POS_FRAMES)), int(np.ceil(cap.get(cv2.CAP_PROP_POS_FRAMES) + fps))):
                    ret, frame = cap.read()
                    detect_yolo()
                    # detect_combined()
            cap.release()
            out.release()
    except Exception as e:
        raise e

