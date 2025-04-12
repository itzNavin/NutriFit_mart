import cv2
import os

def decode_barcode_opencv(image_path):
    if not os.path.exists(image_path):
        print(f"Error: The file {image_path} does not exist.")
        return None
    
    image = cv2.imread(image_path)
    if image is None:
        print(f"Error: Unable to read the image at {image_path}.")
        return None
    
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        if not hasattr(cv2, 'barcode'):
            print("Error: OpenCV build does not support barcode module")
            return None
            
        detector = cv2.barcode.BarcodeDetector()
        ok, decoded_info, _, _ = detector.detectAndDecode(gray)
        
        if ok and decoded_info:
            return decoded_info
        else:
            print("No barcode detected in the image.")
            return None
    except Exception as e:
        print(f"Error during barcode detection: {e}")
        return None