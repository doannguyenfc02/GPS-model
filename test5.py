#test5.py

import matlab.engine
import os
import sys

# Khởi động MATLAB engine
eng = matlab.engine.start_matlab()
print("MATLAB engine started successfully")

# Thêm thư mục chứa hàm 'myspectrogram' vào MATLAB path
eng.addpath('D:/DATN/spectrogram', nargout=0)

# Lấy các tham số từ dòng lệnh
file_name = "fileProcess/uploaded_file.bin"
num_images = int(sys.argv[1])
fs = float(sys.argv[2])
time = float(sys.argv[3])
window_time_sec = 0.1
Nwindow = time / window_time_sec
idxms = 1

# Tạo thư mục đầu ra
folder = "spectrogram_3"
os.makedirs(folder, exist_ok=True)

# Chạy mã MATLAB trong Python
eng.eval(f"clear all; close all; fileName = '{file_name}';", nargout=0)
eng.eval(f"fid = fopen(fileName,'rb');", nargout=0)
eng.eval(f"numImages = {num_images};", nargout=0)
eng.eval(f"fs = {fs};", nargout=0)
eng.eval(f"time = {time};", nargout=0)
eng.eval(f"idxms = {idxms};", nargout=0)
eng.eval("window_time_sec = 0.1;", nargout=0)
eng.eval("Nwindow = time / window_time_sec;", nargout=0)
eng.eval(f"[filepath,name,ext] = fileparts(fileName);", nargout=0)
eng.eval(f"folder = '{folder}';", nargout=0)
eng.eval("mkdir(folder);", nargout=0)

# Tạo chuỗi mã MATLAB hoàn chỉnh và gửi vào hàm eval
matlab_code = f"""
for idx = 1:{num_images}
    type='int16';
    type_size=1;
    fseek(fid,((idx-1)+{idxms}*window_time_sec)*2*type_size*{fs},'bof');
    N = {fs}*0.001*2;
    tmp = fread(fid, N, 'int16');
    tmp = tmp - mean(tmp);
    data = tmp(1:2:end) + 1i*tmp(2:2:end);
    M = 128;
    g = hann(M, 'periodic');
    L = 96;
    Ndft = 512;
    [sp, fp, tp] = myspectrogram(data, Ndft, {fs}, 0.995);
    fg = mesh(tp, fp, abs(sp).^2);
    title(sprintf('%d', idx));
    view(2), axis tight;
    xlabel('Time [s]');
    ylabel('Frequency [Hz]');
    saveas(fg, fullfile(folder, sprintf('%d.png', idx)));
end
fclose(fid);
"""

# Thực thi chuỗi mã MATLAB
eng.eval(matlab_code, nargout=0)

# Đóng MATLAB engine
eng.quit()
print("MATLAB engine closed successfully")
