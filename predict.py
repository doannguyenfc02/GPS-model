from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO
import binascii
import os
import cv2
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing import image

app = Flask(__name__)

# Đường dẫn đến mô hình
model_path = 'model/my_image_classification_model.h5'

# Tải mô hình
model = load_model(model_path)

# Định nghĩa nhãn của lớp
class_labels = ['DME', 'NB', 'NoJam', 'SingleAM', 'SingleChirp', 'SingleFM']

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

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        # Nhận dữ liệu JSON từ yêu cầu
        data = request.json

        # Kiểm tra xem trường 'file' có tồn tại không
        if 'file' not in data:
            return jsonify({'error': 'Missing "file" field'}), 400

        # Chuỗi hex từ dữ liệu JSON
        hex_string = data['file']

        # Chuyển đổi chuỗi hex thành bytes
        byte_data = binascii.unhexlify(hex_string)

        # Chuyển đổi bytes thành hình ảnh
        image_pil = Image.open(BytesIO(byte_data))

        # Đảm bảo thư mục tồn tại
        output_dir = 'output_img'
        os.makedirs(output_dir, exist_ok=True)

        # Lưu hình ảnh thành tệp BMP
        output_path = os.path.join(output_dir, 'res24052.bmp')
        image_pil.save(output_path, format='BMP')

        # Xử lý và cắt ảnh
        cropped_image = crop_image(output_path)
        cropped_image_path = os.path.join(output_dir, 'cropped_imgtest.bmp')
        cv2.imwrite(cropped_image_path, cropped_image)

        # Tiền xử lý ảnh để dự đoán
        img = image.load_img(cropped_image_path, target_size=(150, 150))
        img_array = image.img_to_array(img)
        img_array = np.expand_dims(img_array, axis=0) / 255.0

        # Dự đoán
        predictions = model.predict(img_array)

        # Lấy ra nhãn dự đoán với xác suất cao nhất
        predicted_class = np.argmax(predictions, axis=1)

        # Trả kết quả phân loại về phản hồi
        return jsonify({'predicted_class': class_labels[predicted_class[0]]}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
