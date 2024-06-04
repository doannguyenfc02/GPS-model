def image_to_hex_text(image_path, output_file):
    try:
        with open(image_path, "rb") as image_file:
            # Đọc nội dung của ảnh
            image_content = image_file.read()

            # Chuyển đổi nội dung sang định dạng hex
            hex_content = image_content.hex()

            # Lưu nội dung hex vào tệp văn bản
            with open(output_file, "w") as output:
                output.write(hex_content)
            
            print(f"Chuyển đổi thành công và lưu vào {output_file}")
    except Exception as e:
        print(f"Lỗi: {e}")

# Gọi hàm với tên file ảnh và tên file output văn bản
image_to_hex_text("img_input/SingleFM.bmp", "hexa/SingleFM.txt")
