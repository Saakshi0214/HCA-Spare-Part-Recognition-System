import cv2
import os
import csv
import sys
import numpy as np

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
# IMAGE PREPROCESSING HELPER
# =====================================

def preprocess_image(img):
    """Resizes an image while preserving aspect ratio, ensuring the maximum dimension is 800."""
    h, w = img.shape[:2]
    max_dim = 800
    if h > w:
        new_h = max_dim
        new_w = int(w * (max_dim / h))
    else:
        new_w = max_dim
        new_h = int(h * (max_dim / w))
    return cv2.resize(img, (new_w, new_h))

# =====================================
# GEOMETRIC HOMOGRAPHY VERIFICATION
# =====================================

def verify_homography(M, w, h):
    """Verifies if the homography matrix represents a physically plausible 2D projection.
    Projects the corners of the database image and checks if the projected polygon is convex and has a reasonable area.
    """
    if M is None:
        return False
    # Corners of the database image
    corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
    try:
        projected = cv2.perspectiveTransform(corners, M)
    except:
        return False
    # Check convexity
    if not cv2.isContourConvex(np.array(projected, dtype=np.int32)):
        return False
    # Check area of projected polygon
    area = cv2.contourArea(projected)
    original_area = w * h
    if area < 0.05 * original_area or area > 5.0 * original_area:
        return False
    # Check aspect ratio of projected bounding box
    rect = cv2.minAreaRect(projected)
    (cx, cy), (rw, rh), angle = rect
    if rw == 0 or rh == 0:
        return False
    aspect_ratio = max(rw / rh, rh / rw)
    if aspect_ratio > 6.0:
        return False
    return True

# =====================================
# IN-MEMORY DATASET CACHE (OPTIMIZATION)
# =====================================

DATASET_CACHE = []
DATASET_CACHE_LOADED = False

def preload_dataset(force=False):
    """Loads all dataset images, resizes them preserving aspect ratio, extracts ORB features, and caches them in memory.
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
    orb = cv2.ORB_create(1000)
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

            img = preprocess_image(img)
            
            # Threshold to find part (metal is darker than paper background)
            _, mask = cv2.threshold(img, 130, 255, cv2.THRESH_BINARY_INV)
            
            # Clean margins
            h, w = mask.shape
            margin_y = int(h * 0.10)
            margin_x = int(w * 0.10)
            mask[:margin_y, :] = 0
            mask[-margin_y:, :] = 0
            mask[:, :margin_x] = 0
            mask[:, -margin_x:] = 0
            
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            kp, des = orb.detectAndCompute(img, mask)
            if des is None:
                continue

            h, w = img.shape[:2]
            DATASET_CACHE.append({
                "part": part_folder,
                "des": des,
                "kp": kp,
                "w": w,
                "h": h
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

    test_img = preprocess_image(test_img)

    # ORB Detector
    orb = cv2.ORB_create(1000)

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
        # Match using memory-cached descriptors and verify geometry with RANSAC
        for entry in DATASET_CACHE:
            des2 = entry["des"]
            kp2 = entry["kp"]
            w2 = entry["w"]
            h2 = entry["h"]
            bf = cv2.BFMatcher(cv2.NORM_HAMMING)
            try:
                matches = bf.knnMatch(des1, des2, k=2)
                good_matches = []
                for m_n in matches:
                    if len(m_n) == 2:
                        m, n = m_n
                        if m.distance < 0.75 * n.distance:
                            good_matches.append(m)
                
                inliers = 0
                if len(good_matches) >= 8:
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                    if mask is not None:
                        if verify_homography(M, w2, h2):
                            inliers = int(np.sum(mask))
                
                if inliers > best_match_count:
                    best_match_count = inliers
                    best_part = entry["part"]
            except Exception as e:
                # Handle potential mismatch gracefully
                print(f"BFMatcher/RANSAC Error: {e}")
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

                img = preprocess_image(img)
                
                # Threshold to find part
                _, mask = cv2.threshold(img, 130, 255, cv2.THRESH_BINARY_INV)
                
                # Clean margins
                h, w = mask.shape
                margin_y = int(h * 0.10)
                margin_x = int(w * 0.10)
                mask[:margin_y, :] = 0
                mask[-margin_y:, :] = 0
                mask[:, :margin_x] = 0
                mask[:, -margin_x:] = 0
                
                kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
                mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

                kp2, des2 = orb.detectAndCompute(
                    img,
                    mask
                )
                if des2 is None:
                    continue

                bf = cv2.BFMatcher(cv2.NORM_HAMMING)
                matches = bf.knnMatch(des1, des2, k=2)
                good_matches = []
                for m_n in matches:
                    if len(m_n) == 2:
                        m, n = m_n
                        if m.distance < 0.75 * n.distance:
                            good_matches.append(m)
                            
                h2, w2 = img.shape[:2]
                inliers = 0
                if len(good_matches) >= 8:
                    src_pts = np.float32([kp1[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    dst_pts = np.float32([kp2[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)
                    try:
                        M, mask = cv2.findHomography(src_pts, dst_pts, cv2.RANSAC, 5.0)
                        if mask is not None:
                            if verify_homography(M, w2, h2):
                                inliers = int(np.sum(mask))
                    except:
                        pass
                
                if inliers > folder_best:
                    folder_best = inliers

            if folder_best > best_match_count:
                best_match_count = folder_best
                best_part = part_folder

    # =====================================
    # CONFIDENCE CALCULATION
    # =====================================

    # Reject weak matches
    if best_match_count < 12:

        best_part = "Unknown"
        confidence = 0.0
    else:
        confidence = (best_match_count / 30.0) * 100.0
        if confidence > 100.0:
            confidence = 100.0

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