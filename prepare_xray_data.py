import os
import random
import shutil

SOURCE_DIR = "data/COVID-19_Radiography_Dataset"
TARGET_DIR = "data/xray_data"

CLASSES = {
    "COVID": "COVID",
    "Normal": "NORMAL",
    "Lung_Opacity": "PNEUMONIA",
    "Viral Pneumonia": "PNEUMONIA"
}

SPLIT = {
    "train": 0.7,
    "val": 0.15,
    "test": 0.15
}

os.makedirs(TARGET_DIR, exist_ok=True)

for split in SPLIT:
    for cls in ["COVID", "NORMAL", "PNEUMONIA"]:
        os.makedirs(os.path.join(TARGET_DIR, split, cls), exist_ok=True)

def split_and_copy(images, src_dir, target_class):
    random.shuffle(images)
    n = len(images)
    train_end = int(n * SPLIT["train"])
    val_end = train_end + int(n * SPLIT["val"])

    splits = {
        "train": images[:train_end],
        "val": images[train_end:val_end],
        "test": images[val_end:]
    }

    for split, files in splits.items():
        for file in files:
            src = os.path.join(src_dir, file)
            dst = os.path.join(TARGET_DIR, split, target_class, file)
            shutil.copy(src, dst)

for src_folder, target_class in CLASSES.items():
    images_dir = os.path.join(SOURCE_DIR, src_folder, "images")

    if not os.path.exists(images_dir):
        continue

    images = os.listdir(images_dir)
    split_and_copy(images, images_dir, target_class)

print("✅ Dataset successfully prepared for CNN training")
