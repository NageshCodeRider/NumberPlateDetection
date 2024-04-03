import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import os
import threading
import time
import pytesseract
import csv
import winsound

# Initialize global variables
video_writer = None
recording_start_time = None
recording_stopped = True
update_camera = True
cap = cv2.VideoCapture(0)

def detect_number_plate(frame):
    try:
        # Convert the image to gray scale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Use OpenCV's Haar feature-based cascade classifiers to detect number plate
        number_plate_cascade = cv2.CascadeClassifier('indian_number_plate.xml')
        number_plates = number_plate_cascade.detectMultiScale(gray, 1.3, 7)

        # Initialize an empty list to store detected license plate numbers
        detected_license_plates = []

        for (x, y, w, h) in number_plates:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)  # Draw green rectangle
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]

            # Use Tesseract to perform OCR on the detected number plate region
            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(roi_color, config='--psm 11')

            # Append the detected license plate number to the list
            detected_license_plates.append(text.strip())

            # Draw the detected number text near the license plate region
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # Print the detected license plate numbers
        for plate_number in detected_license_plates:
            print("Detected Number Plate:", plate_number)

        return frame, detected_license_plates
    except Exception as e:
        print("Error:", e)
        return frame, []

def check_detected_number(detected_numbers, csv_files):
    try:
        for csv_file in csv_files:
            if os.path.exists(csv_file):
                with open(csv_file, 'r') as file:
                    reader = csv.reader(file)
                    for row in reader:
                        if row[0] in detected_numbers:
                            print("Number found in database:", row)
                            return row
            else:
                print("CSV file not found:", csv_file)
    except Exception as e:
        print("Error checking number in CSV:", e)
    return None

def capture_image():
    global update_camera
    ret, frame = cap.read()
    if ret:
        timestamp = time.strftime("%Y%m%d%H%M%S")
        image_path = os.path.join("gallery", f"captured_image_{timestamp}.jpg")
        cv2.imwrite(image_path, frame)
        show_image(image_path)
        detected_frame, detected_numbers = detect_number_plate(frame)
        print("Detected Numbers:", detected_numbers)
        csv_files = ['Student_Data.csv', 'Teacher_Data.csv']
        detected_info = check_detected_number(detected_numbers, csv_files)
        if detected_info:
            print("Detected Information:", detected_info)
            winsound.Beep(1000, 500)  # Beep sound
        update_camera = True

def start_recording():
    global video_writer, recording_start_time, recording_stopped, update_camera
    if not video_writer:
        timestamp = time.strftime("%Y%m%d%H%M%S")
        video_path = os.path.join("gallery", f"recorded_video_{timestamp}.mp4")
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        video_writer = cv2.VideoWriter(video_path, fourcc, 20.0, (640, 480))
        recording_start_time = time.time()
        recording_stopped = False
        record_button.config(state=tk.DISABLED)
        stop_button.config(state=tk.NORMAL)
        recording_thread = threading.Thread(target=record_and_display)
        recording_thread.start()

def stop_recording():
    global video_writer, recording_stopped
    if video_writer:
        video_writer.release()
        recording_stopped = True
        record_button.config(state=tk.NORMAL)
        stop_button.config(state=tk.DISABLED)

def record_and_display():
    global recording_stopped, update_camera
    while video_writer and not recording_stopped:
        ret, frame = cap.read()
        if ret:
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            elapsed_time = time.time() - recording_start_time
            timestamp = f"Time Elapsed: {int(elapsed_time)}s"
            cv2.putText(frame, timestamp, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
            img = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=img)
            if update_camera:
                camera_feed.config(image=photo)
                camera_feed.image = photo
            
            # Detect and recognize the number plates in the captured frame
            frame_with_number_plate, detected_license_plates = detect_number_plate(frame)
            # Convert the frame with number plate to PhotoImage
            img_with_number_plate = Image.fromarray(frame_with_number_plate)
            photo_with_number_plate = ImageTk.PhotoImage(image=img_with_number_plate)
            # Update the camera feed with the frame containing the number plate
            if update_camera:
                camera_feed.config(image=photo_with_number_plate)
                camera_feed.image = photo_with_number_plate

            # Check detected numbers against the CSV databases
            csv_files = ['Student_Data.csv', 'Teacher_Data.csv']
            detected_info = check_detected_number(detected_license_plates, csv_files)
            if detected_info:
                print("Detected Information:", detected_info)
                winsound.Beep(1000, 500)  # Beep sound

            time.sleep(0.05)

def show_image(image_path):
    try:
        image = Image.open(image_path)
        photo = ImageTk.PhotoImage(image=image)
        camera_feed.config(image=photo)
        camera_feed.image = photo
    except Exception as e:
        print(e)

# Initialize tkinter window
root = tk.Tk()
root.title("Camera Application")

# Create a frame for camera feed
camera_frame = tk.Frame(root)
camera_frame.pack(padx=10, pady=10)

# Create label for camera feed
camera_feed = tk.Label(camera_frame)
camera_feed.pack()

# Create buttons for capturing and recording
button_frame = tk.Frame(root)
button_frame.pack(padx=10, pady=5)

capture_button = tk.Button(button_frame, text="Capture", command=capture_image)
capture_button.grid(row=0, column=0, padx=5)

record_button = tk.Button(button_frame, text="Record", command=start_recording)
record_button.grid(row=0, column=1, padx=5)

stop_button = tk.Button(button_frame, text="Stop", command=stop_recording, state=tk.DISABLED)
stop_button.grid(row=0, column=2, padx=5)

# Run the tkinter event loop
root.mainloop()
