import cv2
import numpy as np
import os
from tensorflow.keras.models import load_model
import base64
import json
import sys
import io

# Thay đổi mã hóa mặc định sang UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

def crop_image(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if contours:
        max_area = 0
        max_rect = (0, 0, 0, 0)  # x, y, w, h
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            if area > max_area:
                max_area = area
                max_rect = (x, y, w, h)
        x, y, w, h = max_rect
        return img[y:y+h, x:x+w]
    else:
        return img

def process_and_predict(image_path, model):
    try:
        img = cv2.imread(image_path)
        if img is not None:
            cropped_img = crop_image(img)
            resized_img = cv2.resize(cropped_img, (150, 150))
            img_array = np.expand_dims(resized_img, axis=0) / 255.0
            prediction = model.predict(img_array)
            return np.argmax(prediction, axis=1)[0]
        else:
            print(f"Could not read image: {image_path}")
            return None
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return None

def main():
    try:
        # Load the model
        model_path = 'model/my_image_classification_model.h5'
        model = load_model(model_path)
        print("Model loaded successfully.")
    except Exception as e:
        print(f"Error loading model: {e}")
        return

    # Define class labels
    class_labels = ['DME', 'NB', 'NoJam', 'SingleAM', 'SingleChirp', 'SingleFM']

    # Path to the images
    directory = 'spectrogram_3'

    # Process each image in the directory and store predictions
    predictions = []
    for filename in os.listdir(directory):
        if filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg'):
            image_path = os.path.join(directory, filename)
            predicted_class_index = process_and_predict(image_path, model)
            if predicted_class_index is not None:
                predicted_class = class_labels[predicted_class_index]
                with open(image_path, "rb") as image_file:
                    encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
                predictions.append({
                    'image': filename,
                    'class': predicted_class,
                    'base64': encoded_string
                })
            else:
                print(f"Prediction failed for image: {filename}")

    # Ensure predictions are printed as JSON even if no predictions were made
    print("--- JSON OUTPUT START ---")
    print(json.dumps(predictions, ensure_ascii=False))
    print("--- JSON OUTPUT END ---")

if __name__ == '__main__':
    main()
