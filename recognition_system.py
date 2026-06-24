import cv2
import os
import csv
import sys

# =====================================
# EXE / PYTHON PATH HANDLING
# =====================================

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DATASET_PATH = os.path.join(BASE_DIR, "dataset")
CSV_PATH = os.path.join(
    BASE_DIR,
    "metadata",
    "parts_info.csv"
)

# =====================================
# IN-MEMORY DATASET CACHE (OPTIMIZATION)
# =====================================

DATASET_CACHE = []
DATASET_CACHE_LOADED = False

def preload_dataset(force=False):
    """Loads all dataset images, resizes them, extracts ORB features, and caches them in memory.
    This speeds up subsequent recognize_part calls by up to 50x.
    """
    global DATASET_CACHE, DATASET_CACHE_LOADED
    if DATASET_CACHE_LOADED and not force:
        return

    DATASET_CACHE = []
    
    if not os.path.exists(DATASET_PATH):
        print(f"Warning: Dataset folder not found at {DATASET_PATH}")
        return

    print(f"Preloading HCA Spare Parts dataset from: {DATASET_PATH}")
    orb = cv2.ORB_create(500)
    loaded_count = 0

    for part_folder in os.listdir(DATASET_PATH):
        folder_path = os.path.join(DATASET_PATH, part_folder)
        if not os.path.isdir(folder_path):
            continue

        for image_name in os.listdir(folder_path):
            image_path = os.path.join(folder_path, image_name)
            img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue

            img = cv2.resize(img, (800, 600))
            kp, des = orb.detectAndCompute(img, None)
            if des is None:
                continue

            DATASET_CACHE.append({
                "part": part_folder,
                "des": des
            })
            loaded_count += 1

    DATASET_CACHE_LOADED = True
    print(f"Successfully cached descriptors for {loaded_count} images in {len(os.listdir(DATASET_PATH))} part categories.")


# =====================================
# MAIN RECOGNITION FUNCTION
# =====================================

def recognize_part(test_image_path):

    # Load test image
    test_img = cv2.imread(
        test_image_path,
        cv2.IMREAD_GRAYSCALE
    )

    if test_img is None:

        return {
            "part": "Unknown",
            "matches": 0,
            "confidence": 0,
            "details": None
        }

    test_img = cv2.resize(
        test_img,
        (800, 600)
    )

    # ORB Detector
    orb = cv2.ORB_create(500)

    kp1, des1 = orb.detectAndCompute(
        test_img,
        None
    )

    if des1 is None or len(des1) == 0:

        return {
            "part": "Unknown",
            "matches": 0,
            "confidence": 0,
            "details": None
        }

    best_match_count = 0
    best_part = "Unknown"

    # Ensure dataset is preloaded if not done already
    if not DATASET_CACHE_LOADED:
        preload_dataset()

    # =====================================
    # COMPARE WITH DATASET (OPTIMIZED CACHE PREFERRED)
    # =====================================

    if DATASET_CACHE:
        # Match using memory-cached descriptors
        for entry in DATASET_CACHE:
            des2 = entry["des"]
            bf = cv2.BFMatcher(
                cv2.NORM_HAMMING,
                crossCheck=True
            )
            try:
                matches = bf.match(des1, des2)
                match_count = len(matches)
                if match_count > best_match_count:
                    best_match_count = match_count
                    best_part = entry["part"]
            except Exception as e:
                # Handle potential mismatch in descriptor dimensions/types gracefully
                print(f"BFMatcher Error: {e}")
                continue
    else:
        # Fallback to slow disk comparison if cache failed or is empty
        if not os.path.exists(DATASET_PATH):
            print("Dataset folder not found:")
            print(DATASET_PATH)
            return {
                "part": "Unknown",
                "matches": 0,
                "confidence": 0,
                "details": None
            }

        for part_folder in os.listdir(DATASET_PATH):
            folder_path = os.path.join(
                DATASET_PATH,
                part_folder
            )
            if not os.path.isdir(folder_path):
                continue

            folder_best = 0
            for image_name in os.listdir(folder_path):
                image_path = os.path.join(
                    folder_path,
                    image_name
                )
                img = cv2.imread(
                    image_path,
                    cv2.IMREAD_GRAYSCALE
                )
                if img is None:
                    continue

                img = cv2.resize(
                    img,
                    (800, 600)
                )

                kp2, des2 = orb.detectAndCompute(
                    img,
                    None
                )
                if des2 is None:
                    continue

                bf = cv2.BFMatcher(
                    cv2.NORM_HAMMING,
                    crossCheck=True
                )
                matches = bf.match(
                    des1,
                    des2
                )
                match_count = len(matches)
                if match_count > folder_best:
                    folder_best = match_count

            if folder_best > best_match_count:
                best_match_count = folder_best
                best_part = part_folder

    # =====================================
    # CONFIDENCE CALCULATION
    # =====================================

    confidence = (
        best_match_count / 500
    ) * 100

    if confidence > 100:
        confidence = 100

    # Reject weak matches
    if best_match_count < 40:

        best_part = "Unknown"
        confidence = 0

    # =====================================
    # LOAD METADATA
    # =====================================

    details = None

    if best_part != "Unknown":

        try:

            if os.path.exists(CSV_PATH):

                with open(
                    CSV_PATH,
                    "r",
                    encoding="utf-8-sig"
                ) as file:

                    reader = csv.DictReader(file)

                    for row in reader:

                        if row["Part_Name"] == best_part:

                            details = row
                            break

            else:

                print("CSV not found:")
                print(CSV_PATH)

        except Exception as e:

            print("CSV Error:", e)

    # =====================================
    # RETURN RESULT
    # =====================================

    return {

        "part": best_part,
        "matches": best_match_count,
        "confidence": round(confidence, 2),
        "details": details

    }


# =====================================
# TERMINAL TESTING
# =====================================

if __name__ == "__main__":

    test_image = os.path.join(
        BASE_DIR,
        "test_images",
        "camera_capture.jpg"
    )

    result = recognize_part(
        test_image
    )

    print("\nBEST MATCH:")
    print(result["part"])

    print("\nMATCH COUNT:")
    print(result["matches"])

    print("\nCONFIDENCE:")
    print(result["confidence"], "%")

    if result["details"]:

        d = result["details"]

        print("\nPART DETAILS")

        print("Part Name:", d.get("Part_Name", "N/A"))
        print("Part Code:", d.get("Part Code", "N/A"))
        print("Source PDF:", d.get("Source PDF", "N/A"))
        print("Total Images:", d.get("Total Images", "N/A"))
        print("Machine Used In:", d.get("Machine Used In", "N/A"))
        print("Category:", d.get("Category", "N/A"))
        print("Rack Location:", d.get("Rack Location", "N/A"))
        print("Bin Number:", d.get("Bin Number", "N/A"))
        print("Commonly Sold:", d.get("Commonly Sold", "N/A"))
        print("Remarks:", d.get("Remarks", "N/A"))