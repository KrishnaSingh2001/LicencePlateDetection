import numpy as np
import pandas as pd
import streamlit as st
from ultralytics import YOLO
import cv2
import pytesseract
from pytesseract import Output
import os
import re
import shutil
import tempfile

st.set_page_config(
    page_title="YOLO Car License Plate Image and Video Processing",
    page_icon=":car:",
    initial_sidebar_state="expanded",
)
st.title('YOLO Car License Plate :red[Image and Video Processing]')

pytesseract.pytesseract.tesseract_cmd = None

# Search for tesseract binary in path
@st.cache_resource
def find_tesseract_binary() -> str:
    return shutil.which("tesseract")

# Set tesseract binary path
pytesseract.pytesseract.tesseract_cmd = find_tesseract_binary()
if not pytesseract.pytesseract.tesseract_cmd:
    st.error("Tesseract binary not found in PATH. Please install Tesseract.")

# Allow users to upload images or videos
uploaded_file = st.file_uploader("Upload an Image or Video", type=["jpg", "jpeg", "png", "bmp", "mp4", "avi", "mov", "mkv"])

def remove_non_alphanum(text):
    return re.sub(r'[^a-zA-Z0-9]', ' ', text)

# Load YOLO model
try:
    model = YOLO('best.pt')
except Exception as e:
    st.error(f"Error loading YOLO model: {e}")

def predict_and_save_image(path_test_car: str, output_image_path: str) -> str:
    """
    Predicts and saves the bounding boxes on the given test image using the trained YOLO model.

    Parameters:
    path_test_car (str): Path to the test image file.
    output_image_path (str): Path to save the output image file.

    Returns:
    str: The path to the saved output image file.
    """
    try:
        results = model.predict(path_test_car, device='cpu')
        image = cv2.imread(path_test_car)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        gray_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        license_text = ""

        for result in results:
            for box in result.boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                confidence = box.conf[0]
                cv2.rectangle(image, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(image, f'{confidence*100:.1f}%', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 178, 102), 2, cv2.LINE_AA)
                roi = gray_image[y1:y2, x1:x2]

                # Preprocess the ROI for better OCR results
                roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                # Enhance contrast (optional)
                roi = cv2.equalizeHist(roi)

                # Perform OCR on the cropped and preprocessed image
                text = pytesseract.image_to_string(roi, lang='eng', config='--oem 3 --psm 7')
                text = remove_non_alphanum(text)

                # Append to license_text if not empty
                if text.strip():
                    license_text += text + " "

                # Commenting out license plate text display
                # cv2.putText(image, f'{text}', (x1 , y1 + 2 * (y2 - y1)),
                #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (51, 255, 255), 2, cv2.LINE_AA)

        # Display the extracted license plate number
        # if license_text:
        #     st.code(f"License Number: {license_text.strip()}", language='text')
        # else:
        #     st.warning("No license plate number detected.")

        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        # Ensure the directory exists before saving
        os.makedirs(os.path.dirname(output_image_path), exist_ok=True)
        # Save the image
        cv2.imwrite(output_image_path, image)
        return output_image_path
    except Exception as e:
        st.error(f"Error processing image: {e}")
        return None

def predict_and_plot_video(video_path: str, output_path: str) -> str:
    """
    Predicts and saves the bounding boxes on the given test video using the trained YOLO model.

    Parameters:
    video_path (str): Path to the test video file.
    output_path (str): Path to save the output video file.

    Returns:
    str: The path to the saved output video file.
    """
    try:
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            st.error(f"Error opening video file: {video_path}")
            return None
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = int(cap.get(cv2.CAP_PROP_FPS))

        fourcc = cv2.VideoWriter_fourcc(*'h264')

        output_dir = os.path.dirname(output_path)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        out = cv2.VideoWriter(output_path, fourcc, fps, (frame_width, frame_height))
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            results = model.predict(rgb_frame, device='cpu')
            license_text = ""

            for result in results:
                for box in result.boxes:
                    x1, y1, x2, y2 = map(int, box.xyxy[0])
                    confidence = box.conf[0]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    cv2.putText(frame, f'{confidence*100:.1f}%', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 178, 102), 2, cv2.LINE_AA)
                    roi = gray_frame[y1:y2, x1:x2]

                    # Preprocess the ROI for better OCR results
                    roi = cv2.threshold(roi, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
                    # Enhance contrast (optional)
                    roi = cv2.equalizeHist(roi)

                    # Perform OCR on the cropped and preprocessed image
                    text = pytesseract.image_to_string(roi, lang='eng', config='--oem 3 --psm 7')
                    text = remove_non_alphanum(text)

                    # Append to license_text if not empty
                    if text.strip():
                        license_text += text + " "

                    # Commenting out license plate text display
                    # cv2.putText(frame, f'{text}', (x1 , y1 + 2 * (y2 - y1)),
                    #             cv2.FONT_HERSHEY_SIMPLEX, 0.7, (51, 255, 255), 2, cv2.LINE_AA)

            out.write(frame)
        cap.release()
        out.release()

        # Display the extracted license plate number
        # if license_text:
        #     st.code(f"License Number: {license_text.strip()}", language='text')
        # else:
        #     st.warning("No license plate number detected.")
        
        return output_path
       
    except Exception as e:
        st.error(f"Error processing video: {e}")
        return None

def process_media(input_path: str, output_path: str) -> str:
    """
    Processes the uploaded media file (image or video) and returns the path to the saved output file.
    
    Parameters:
        input_path (str): Path to the input media file.
        output_path (str): Path to save the output media file.
    
    Returns:
        str: The path to the saved output media file.
    """
    file_extension = os.path.splitext(input_path)[1].lower()
    if file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
        return predict_and_plot_video(input_path, output_path)
       
    elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
        return predict_and_save_image(input_path, output_path)
       
    else:
        st.error(f"Unsupported file type: {file_extension}")
        return None

temp_directory = 'temp'
if not os.path.exists(temp_directory):
    os.makedirs(temp_directory)

if st.button("Proceed"):
    if uploaded_file is not None:
        input_path = os.path.join("temp", uploaded_file.name)
        output_path = os.path.join("temp", f"output_{uploaded_file.name}")
        try:
            with open(input_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            with st.spinner('Processing...'):
                processed_file = process_media(input_path, output_path)

            if processed_file:
                st.success('Processing complete.')
                file_extension = os.path.splitext(processed_file)[1].lower()

                if file_extension in ['.jpg', '.jpeg', '.png', '.bmp']:
                    st.image(processed_file, caption="Processed Image", use_column_width=True)
                elif file_extension in ['.mp4', '.avi', '.mov', '.mkv']:
                    st.video(processed_file)

                # Offer file download
                with open(processed_file, "rb") as f:
                    st.download_button(
                        label="Download Processed File",
                        data=f,
                        file_name=os.path.basename(processed_file),
                        mime="video/mp4" if file_extension in ['.mp4', '.avi', '.mov', '.mkv'] else "image/jpeg"
                    )
        except Exception as e:
            st.error(f"Error processing file: {e}")
        finally:
            # Clean up temporary files
            if os.path.exists(input_path):
                os.remove(input_path)
            if os.path.exists(output_path):
                os.remove(output_path)
    else:
        st.warning("Please upload a file before proceeding.")
