import cv2
import numpy as np
import os
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image
import base64
import json
import sys
import io
import logging

# Thay đổi mã hóa mặc định sang UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def crop_image(image_path):
    image = cv2.imread(image_path)
    # Chuyển đổi ảnh sang màu xám
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Ngưỡng ảnh để lấy khu vực phi trắng
    _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY_INV)
    # Tìm contours
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    # Tìm bounding box lớn nhất
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
        return image[y:y+h, x:x+w]
    else:
        return image  # Trả lại ảnh gốc nếu không tìm thấy contours

def classify_images(folder_path, model_path):
    try:
        model = load_model(model_path)
        class_labels = ['DME', 'NB', 'NoJam', 'SingleAM', 'SingleChirp', 'SingleFM']
        results = []

        for filename in os.listdir(folder_path):
            if filename.endswith(".png"):
                logger.info(f"Processing file: {filename}")
                image_path = os.path.join(folder_path, filename)
                cropped_image = crop_image(image_path)

                # Tiền xử lý ảnh để dự đoán mà không lưu vào đĩa
                resized_image = cv2.resize(cropped_image, (150, 150))
                img_array = image.img_to_array(resized_image)
                img_array = np.expand_dims(img_array, axis=0) / 255.0

                # Dự đoán
                predictions = model.predict(img_array)
                predicted_class = np.argmax(predictions, axis=1)
                logger.info(f"Predicted class for {filename}: {class_labels[predicted_class[0]]}")

                # Mã hóa ảnh cropped trực tiếp từ bộ nhớ
                _, buffer = cv2.imencode('.png', cropped_image)
                encoded_string = base64.b64encode(buffer).decode('utf-8')

                results.append({
                    'image_name': filename,
                    'predicted_class': class_labels[predicted_class[0]],
                    'image_base64': encoded_string
                })
        
        if not results:
            logger.error("No results found after classification")
            print(json.dumps({'error': 'No results found'}, ensure_ascii=False))
        else:
            for result in results:
                print(json.dumps(result, ensure_ascii=False))
    except Exception as e:
        logger.error(f"Error during classification: {str(e)}")
        print(json.dumps({'error': str(e)}, ensure_ascii=False))

if __name__ == "__main__":
    folder_path = 'spectrogram_3'
    model_path = 'model/my_image_classification_model.h5'
    classify_images(folder_path, model_path)
