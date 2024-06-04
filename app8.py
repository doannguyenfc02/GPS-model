from flask import Flask, request, jsonify
import json
import subprocess
import base64
import os
import logging
import io
import sys

app = Flask(__name__)
UPLOAD_FOLDER = 'fileProcess'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Thay đổi mã hóa mặc định sang UTF-8
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

@app.route('/upload', methods=['POST'])
def upload_file():
    data = request.json
    file_data = data['fileData']
    chunk_index = data['chunkIndex']
    total_chunks = data['totalChunks']
    num_images = data['numImages']
    fs = data['fs']
    time = data['time']

    # Decode the base64 chunk data
    file_bytes = base64.b64decode(file_data)

    # Write chunk to file
    file_path = os.path.join(UPLOAD_FOLDER, 'uploaded_file.bin')
    mode = 'wb' if chunk_index == 0 else 'ab'
    with open(file_path, mode) as file:
        file.write(file_bytes)

    # Check if all chunks have been received
    if chunk_index == total_chunks - 1:
        return jsonify({'message': 'All chunks received and saved successfully', 'file_path': file_path})
    else:
        return jsonify({'message': f'Chunk {chunk_index + 1} of {total_chunks} received successfully'})

@app.route('/upload/completed', methods=['POST'])
def upload_completed():
    data = request.json
    num_images = data['numImages']
    fs = data['fs']
    time = data['time']

    # Gọi script MATLAB sau khi tất cả các chunks đã được tải lên
    try:
        result = subprocess.run(
            ['python', 'test4.py', str(num_images), str(fs), str(time)],
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8'
        )
        logger.info(f"MATLAB script output: {result.stdout}")
        logger.error(f"MATLAB script error (if any): {result.stderr}")

        # Kiểm tra thư mục đầu ra
        output_folder = 'spectrogram_3'
        output_files = os.listdir(output_folder)
        if len(output_files) >= num_images:
            logger.info("All expected output files are present.")
        else:
            logger.error(f"Expected {num_images} output files but found {len(output_files)}.")

        return jsonify({'message': 'Processing started'}), 202
    except subprocess.CalledProcessError as e:
        logger.error(f"Error while processing the file: {e.stderr}")
        return jsonify({'message': 'Error occurred while processing the file', 'error': e.stderr}), 500

@app.route('/predict', methods=['POST'])
def predict():
    data = request.get_json()
    # Execute the predict6.py script
    process = subprocess.Popen(['python', 'predict7.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()

    # Check the output of the script
    print("--- RAW OUTPUT START ---")
    print(stdout.decode('utf-8'))
    print("--- RAW OUTPUT END ---")
    print(f"Script stderr: {stderr.decode('utf-8')}")

    try:
        # Attempt to load the JSON output from the script
        output_str = stdout.decode('utf-8').strip()
        json_output_start = output_str.find("--- JSON OUTPUT START ---")
        json_output_end = output_str.find("--- JSON OUTPUT END ---")

        if json_output_start != -1 and json_output_end != -1:
            json_data = output_str[json_output_start + len("--- JSON OUTPUT START ---"):json_output_end].strip()
            predictions = json.loads(json_data)
        else:
            predictions = []
    except json.JSONDecodeError as e:
        # Log the error and return a 500 error response
        print(f"JSON decode error: {e}")
        return jsonify({'error': 'Failed to decode JSON from script output'}), 500

    return jsonify(predictions)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
