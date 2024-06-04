from flask import Flask, request, jsonify
import base64
import os
import subprocess
import json
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
    try:
        data = request.json
        file_data = data['fileData']
        chunk_index = data['chunkIndex']
        total_chunks = data['totalChunks']  # Ensure this is the correct field name
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
            try:
                # Run the MATLAB script after receiving all chunks
                result = subprocess.run(
                    ['python', 'test5.py', str(num_images), str(fs), str(time)], 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8'
                )
                logger.info(f"MATLAB script output: {result.stdout}")
                logger.error(f"MATLAB script error (if any): {result.stderr}")
                
                # Run the prediction script after MATLAB script completes
                classification_result = subprocess.run(
                    ['python', 'predict2_2.py'], 
                    check=True, 
                    capture_output=True, 
                    text=True,
                    encoding='utf-8'
                )
                logger.info(f"Prediction script output: {classification_result.stdout}")
                logger.error(f"Prediction script error (if any): {classification_result.stderr}")
                
                # Parse the classification output
                try:
                    classification_output = [json.loads(line) for line in classification_result.stdout.strip().split('\n') if line]
                except json.JSONDecodeError as e:
                    logger.error(f"JSONDecodeError: {str(e)}")
                    classification_output = [{'error': 'Failed to decode JSON', 'details': str(e)}]
                
                return jsonify({
                    'message': 'File received and processed successfully',
                    'file_path': file_path,
                    'classification_output': classification_output
                })
            except subprocess.CalledProcessError as e:
                logger.error(f"Error while processing the file: {e.stderr}")
                return jsonify({'message': 'Error occurred while processing the file', 'error': e.stderr}), 500
        else:
            return jsonify({'message': f'Chunk {chunk_index + 1} of {total_chunks} received successfully'})
    except KeyError as e:
        logger.error(f"Missing key in request data: {str(e)}")
        return jsonify({'message': 'Unexpected error occurred', 'error': f"Missing key in request data: {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return jsonify({'message': 'Unexpected error occurred', 'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
