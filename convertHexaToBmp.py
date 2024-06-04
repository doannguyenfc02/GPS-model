from flask import Flask, request, jsonify
from PIL import Image
from io import BytesIO
import binascii
import os

app = Flask(__name__)

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
        image = Image.open(BytesIO(byte_data))

        # Đảm bảo thư mục tồn tại
        output_dir = 'output_img'
        os.makedirs(output_dir, exist_ok=True)

        # Lưu hình ảnh thành tệp BMP
        output_path = os.path.join(output_dir, 'res24052.bmp')
        image.save(output_path, format='BMP')

        return jsonify({'message': f'Image uploaded successfully and saved as {output_path}'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
