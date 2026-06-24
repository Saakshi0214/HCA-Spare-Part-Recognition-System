# HCA-Spare-Part-Recognition-System
## Overview

The HCA Spare Part Recognition System is an image-based recognition system developed using Python, OpenCV, and Flask. The system identifies industrial sewing machine spare parts by comparing uploaded or captured images with a dataset using ORB (Oriented FAST and Rotated BRIEF) feature matching and displays the corresponding metadata.

## Features

* Image Upload
* Camera Capture
* ORB Feature-Based Recognition
* Metadata Retrieval
* Graphical User Interface
* Web Interface using Flask

## Technologies Used

* Python 3.x
* OpenCV
* Flask
* Pillow
* NumPy
* Tkinter

## Folder Structure

```text
HCA/
│
├── assets/
├── dataset/
├── metadata/
├── static/
├── templates/
├── test_images/
├── app.py
├── gui.py
├── recognition_system.py
├── requirements.txt
├── Procfile
├── README.md
```

## Prerequisites

* Python 3.10 or higher
* Git

## Clone the Repository

```bash
git clone <repository-link>
cd HCA
```

## Create Virtual Environment

```bash
python -m venv venv
```

Activate the virtual environment:

Windows:

```bash
venv\Scripts\activate
```

Linux/Mac:

```bash
source venv/bin/activate
```

## Install Dependencies

```bash
pip install -r requirements.txt
```

## Run the Application

### Desktop GUI

```bash
python gui.py
```

### Flask Web Application

```bash
python app.py
```

Open your browser and visit:

```text
http://127.0.0.1:5000
```

## Dataset

The dataset consists of multiple images of industrial sewing machine spare parts organized into folders. Metadata corresponding to each part is stored in `metadata/parts_info.csv`.

## How the System Works

1. User uploads an image or captures an image using a webcam.
2. ORB features are extracted from the input image.
3. Features are matched against images stored in the dataset.
4. The best matching spare part is selected.
5. Metadata corresponding to the identified part is retrieved from the CSV file.
6. Results are displayed through the GUI or web interface.

## Dependencies

The project requires:

* Flask
* OpenCV-Python
* Pillow
* NumPy

These dependencies are listed in `requirements.txt`.

## Environment Variables

This project does not use any environment variables or API keys.

## Database Setup

No database is required. Metadata is stored in CSV format inside the `metadata` folder.

## Author

Hari Chand Anand & Co.

## License

This project was developed for educational and internship purposes.
