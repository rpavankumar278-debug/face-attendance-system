import base64
import cv2
import numpy as np
import face_recognition
import os
from flask import jsonify

# Accept three parameters: faculty_folder, existing_images, image_data
def capture_image(faculty_folder, existing_images, image_data):
    try:
        if existing_images >= 20:
            return jsonify({"status": "error", "message": "Maximum image limit reached. Please proceed to train the model."}), 400

        # Decode image data from base64
        header, encoded = image_data.split(",", 1)
        image_bytes = base64.b64decode(encoded)

        np_array = np.frombuffer(image_bytes, dtype=np.uint8)
        image = cv2.imdecode(np_array, cv2.IMREAD_COLOR)

        rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        boxes = face_recognition.face_locations(rgb, model="hog")

        if not boxes:
            return jsonify({"status": "error", "message": "No face detected"}), 400

        # Save image with proper naming convention
        filename = f"{existing_images}.jpg"
        image_path = os.path.join(faculty_folder, filename)
        cv2.imwrite(image_path, image)
        existing_images += 1

        return jsonify({
            "status": "success",
            "message": f"Saved {filename}",
            "count": existing_images
        })

    except Exception as e:
        return jsonify({"status": "error", "message": f"An error occurred: {str(e)}"}), 500
