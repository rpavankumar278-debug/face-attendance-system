import os
import pickle
import threading
import queue
import face_recognition

# Queue to stream progress during training
progress_queue = queue.Queue()

def train_model(upload_folder, progress_queue):
    known_encodings = []
    known_names = []

    # Get all faculty folders (assumed to be faculty ID folders)
    faculty_folders = [f for f in os.listdir(upload_folder) if os.path.isdir(os.path.join(upload_folder, f))]
    total_folders = len(faculty_folders)
    processed = 0

    for faculty_folder in faculty_folders:
        folder_path = os.path.join(upload_folder, faculty_folder)
        for filename in os.listdir(folder_path):
            if filename.endswith('.jpg'):
                image_path = os.path.join(folder_path, filename)
                try:
                    # Load image and get face encodings
                    image = face_recognition.load_image_file(image_path)
                    encodings = face_recognition.face_encodings(image)

                    if encodings:
                        known_encodings.append(encodings[0])
                        known_names.append(faculty_folder)
                except Exception as e:
                    progress_queue.put(f"Error on {filename}")

        processed += 1
        progress = int((processed / total_folders) * 100)
        progress_queue.put(f"Progress: {progress}%")

    # Save model as pickle file
    with open('face_recognition_model.pkl', 'wb') as f:
        pickle.dump((known_encodings, known_names), f)

    progress_queue.put("Training Complete")

def start_training(upload_folder, progress_queue):
    threading.Thread(target=train_model, args=(upload_folder, progress_queue)).start()
