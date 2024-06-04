from flask import Flask, request, jsonify
import base64
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'fileProcess'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

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
        return jsonify({'message': 'File received and saved successfully', 'file_path': file_path})
    else:
        return jsonify({'message': f'Chunk {chunk_index + 1} of {total_chunks} received successfully'})
    


    ##XỬ LÝ CHO TEST5

@app.route('/upload/completed', methods=['GET'])
def upload_completed():
    # This endpoint can be used to signal the backend that the upload is complete.
    return jsonify({'message': 'All chunks received and file saved successfully'})

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
