import tkinter as tk
from tkinter import messagebox
import cv2
from PIL import Image, ImageTk
import os
import threading
import time
import pytesseract
import winsound
import mysql.connector

video_writer = None
recording_start_time = None
recording_stopped = True
update_camera = True
cap = cv2.VideoCapture(0)
camera_feed = None

def detect_number_plate(frame):
    try:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        number_plate_cascade = cv2.CascadeClassifier('indian_number_plate.xml')
        number_plates = number_plate_cascade.detectMultiScale(gray, 1.3, 7)
        detected_license_plates = []

        for (x, y, w, h) in number_plates:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            roi_gray = gray[y:y + h, x:x + w]
            roi_color = frame[y:y + h, x:x + w]

            pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
            text = pytesseract.image_to_string(roi_color, config='--psm 11')
            detected_license_plates.append(text.strip())

            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        for plate_number in detected_license_plates:
            print("Detected Number Plate:", plate_number)

        return frame, detected_license_plates
    except Exception as e:
        print("Error:", e)
        return frame, []

def check_detected_number(detected_numbers):
    detected_info = []
    
    try:
        # Connect to the MySQL database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",  # Enter your MySQL password here
            database="number-plate"
        )

        cursor = conn.cursor()

        for detected_number in detected_numbers:
            # Query the student table
            cursor.execute("SELECT * FROM student WHERE reg_number = %s", (detected_number,))
            student_result = cursor.fetchone()
            if student_result:
                display_data(student_result)
                #detected_info.append(student_result)

            # Query the teacher table
            cursor.execute("SELECT * FROM teacher WHERE reg_number = %s", (detected_number,))
            teacher_result = cursor.fetchone()
            if teacher_result:
                display_data(teacher_result)
                #detected_info.append(teacher_result)

    except mysql.connector.Error as e:
        print("Error checking number in MySQL:", e)

    finally:
        # Close the database connection
        if conn.is_connected():
            cursor.close()
            conn.close()

    return detected_info

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

        # Compare detected numbers with the database
        detected_info = check_detected_number(detected_numbers)
        if detected_info:
            print("Detected Information:", detected_info)
            winsound.Beep(1000, 500)
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
            
            # Convert frame to Tkinter compatible image
            img = Image.fromarray(frame)
            photo = ImageTk.PhotoImage(image=img)
            
            # Display frame in camera feed
            if update_camera:
                camera_feed.config(image=photo)
                camera_feed.image = photo
            
            # Detect number plates and display frame with detected number plates
            frame_with_number_plate, detected_license_plates = detect_number_plate(frame)
            img_with_number_plate = Image.fromarray(frame_with_number_plate)
            photo_with_number_plate = ImageTk.PhotoImage(image=img_with_number_plate)
            if update_camera:
                camera_feed.config(image=photo_with_number_plate)
                camera_feed.image = photo_with_number_plate
            
            # Check detected number plates against database
            if detected_license_plates:
                compare_with_database(detected_license_plates)
        # Wait for a short duration before processing the next frame
        time.sleep(0.05)

def compare_with_database(detected_license_plates):
    try:
        # Connect to the database
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="number-plate"
        )
        
        cursor = conn.cursor()

        # Query the student table for each detected license plate
        for plate_number in detected_license_plates:
            query = "SELECT * FROM student WHERE reg_number = %s"
            cursor.execute(query, (plate_number,))
            result = cursor.fetchone()
            if result:
                #print("Plate number found in student database:", result)
                display_data(result)
            else:
                # Query the teacher table if not found in student table
                query = "SELECT * FROM teacher WHERE reg_number = %s"
                cursor.execute(query, (plate_number,))
                result = cursor.fetchone()
                if result:
                    display_data(result)
        # Close database connection
        cursor.close()
        conn.close()
    except Exception as e:
        print("Error comparing with database:", e)
        
def display_data(data):
    # Display the retrieved data
    winsound.Beep(1000, 500)
    print("---------------------------")
    print("Reg Number:", data[0])
    print("Owner Name:", data[1])
    print("Licence Number:", data[2])
    print("Department:", data[3])
    print("Contact Number:", data[4])
    print("---------------------------")

def show_image(image_path):
    try:
        global camera_feed
        image = Image.open(image_path)
        photo = ImageTk.PhotoImage(image=image)
        camera_feed.config(image=photo)
        camera_feed.image = photo
    except Exception as e:
        print(e)

def login():
    username = username_entry.get()
    password = password_entry.get()
    if authenticate(username, password):
        messagebox.showinfo("Login Successful", "Welcome, Admin!")
        login_window.destroy()
        open_camera_application()
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")

def authenticate(username, password):
    return username == "admin" and password == "admin"

def open_camera_application():
    global root, camera_feed, record_button, stop_button
    root = tk.Tk()
    root.title("Camera Application")
    camera_frame = tk.Frame(root)
    camera_frame.pack(padx=10, pady=10)
    camera_feed = tk.Label(camera_frame)
    camera_feed.pack()
    button_frame = tk.Frame(root)
    button_frame.pack(padx=10, pady=5)
    capture_button = tk.Button(button_frame, text="Capture", command=capture_image)
    capture_button.grid(row=0, column=0, padx=5)
    record_button = tk.Button(button_frame, text="Record", command=start_recording)
    record_button.grid(row=0, column=1, padx=5)
    stop_button = tk.Button(button_frame, text="Stop", command=stop_recording, state=tk.DISABLED)
    stop_button.grid(row=0, column=2, padx=5)
    root.mainloop()
    
    

login_window = tk.Tk()
login_window.title("Login")
username_label = tk.Label(login_window, text="Username:")
username_label.grid(row=0, column=0, padx=5, pady=5)
username_entry = tk.Entry(login_window)
username_entry.grid(row=0, column=1, padx=5, pady=5)

password_label = tk.Label(login_window, text="Password:")
password_label.grid(row=1, column=0, padx=5, pady=5)
password_entry = tk.Entry(login_window, show="*")
password_entry.grid(row=1, column=1, padx=5, pady=5)

login_button = tk.Button(login_window, text="Login", command=login)
login_button.grid(row=2, columnspan=2, pady=10)

login_window.mainloop()


def register():
    # Get user inputs
    reg_number = reg_number_entry.get()
    owner_name = owner_name_entry.get()
    licence_number = licence_number_entry.get()
    department = department_entry.get()
    contact_number = contact_number_entry.get()
    
    # Determine the table to insert data based on radio button selection
    if role_var.get() == "student":
        table_name = "student"
    elif role_var.get() == "teacher":
        table_name = "teacher"
    else:
        messagebox.showerror("Error", "Please select a role.")
        return

    # Validate inputs
    if not all([reg_number, owner_name, department, contact_number]):
        messagebox.showerror("Error", "Please fill in all fields.")
        return

    # Check if registration number already exists in the database
    try:
        # Establish MySQL connection
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="number-plate"
        )

        cursor = conn.cursor()

        # Execute SQL query to check if registration number exists
        query = f"SELECT reg_number FROM {table_name} WHERE reg_number = %s"
        cursor.execute(query, (reg_number,))
        existing_record = cursor.fetchone()

        if existing_record:
            messagebox.showinfo("Info", "User is already registered.")
            return

        # Insert data into MySQL database
        if table_name == "student":
            insert_query = "INSERT INTO student (reg_number, owner_name, licence_number, department, contact_number) VALUES (%s, %s, %s, %s, %s)"
            insert_data = (reg_number, owner_name, licence_number, department, contact_number)
        elif table_name == "teacher":
            insert_query = "INSERT INTO teacher (reg_number, owner_name, licence_number, department, contact_number) VALUES (%s, %s, %s, %s, %s)"
            insert_data = (reg_number, owner_name, licence_number, department, contact_number)
        else:
            messagebox.showerror("Error", "Invalid table name.")
            return

        cursor.execute(insert_query, insert_data)
        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Registration successful!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

def delete():
    # Get user inputs
    reg_number = reg_number_entry.get()
    
    # Determine the table to delete from based on radio button selection
    if role_var.get() == "student":
        table_name = "student"
    elif role_var.get() == "teacher":
        table_name = "teacher"
    else:
        messagebox.showerror("Error", "Please select a role.")
        return

    # Validate inputs
    if not reg_number:
        messagebox.showerror("Error", "Please enter registration number.")
        return

    # Delete data from MySQL database
    try:
        # Establish MySQL connection
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="number-plate"
        )

        cursor = conn.cursor()

        # Execute SQL query to delete record
        delete_query = f"DELETE FROM {table_name} WHERE reg_number = %s"
        cursor.execute(delete_query, (reg_number,))

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Delete successful!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")
def update():
    # Get user inputs
    reg_number = reg_number_entry.get()
    owner_name = owner_name_entry.get()
    licence_number = licence_number_entry.get()
    department = department_entry.get()
    contact_number = contact_number_entry.get()
    
    # Determine the table to update based on radio button selection
    if role_var.get() == "student":
        table_name = "student"
    elif role_var.get() == "teacher":
        table_name = "teacher"
    else:
        messagebox.showerror("Error", "Please select a role.")
        return

    # Validate inputs
    if not all([reg_number, owner_name, licence_number, department, contact_number]):
        messagebox.showerror("Error", "Please fill in all fields.")
        return

    # Update data in MySQL database
    try:
        # Establish MySQL connection
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database="number-plate"
        )

        cursor = conn.cursor()

        # Execute SQL query to update record
        update_query = f"UPDATE {table_name} SET owner_name = %s, licence_number = %s, department = %s, contact_number = %s WHERE reg_number = %s"
        update_data = (owner_name, licence_number, department, contact_number, reg_number)
        cursor.execute(update_query, update_data)

        conn.commit()
        conn.close()

        messagebox.showinfo("Success", "Update successful!")
    except Exception as e:
        messagebox.showerror("Error", f"An error occurred: {e}")

# Create tkinter window for registration
registration_window = tk.Tk()
registration_window.title("Registration")

# Define role_var as a StringVar
role_var = tk.StringVar()

# Create input fields
reg_number_label = tk.Label(registration_window, text="Vehicle Registration Number:")
reg_number_label.grid(row=0, column=0, padx=5, pady=5)
reg_number_entry = tk.Entry(registration_window)
reg_number_entry.grid(row=0, column=1, padx=5, pady=5)

owner_name_label = tk.Label(registration_window, text="Registered Owner's Name:")
owner_name_label.grid(row=1, column=0, padx=5, pady=5)
owner_name_entry = tk.Entry(registration_window)
owner_name_entry.grid(row=1, column=1, padx=5, pady=5)

licence_number_label = tk.Label(registration_window, text="Driving Licence Number:")
licence_number_label.grid(row=2, column=0, padx=5, pady=5)
licence_number_entry = tk.Entry(registration_window)
licence_number_entry.grid(row=2, column=1, padx=5, pady=5)

department_label = tk.Label(registration_window, text="College Department:")
department_label.grid(row=3, column=0, padx=5, pady=5)
department_entry = tk.Entry(registration_window)
department_entry.grid(row=3, column=1, padx=5, pady=5)

contact_number_label = tk.Label(registration_window, text="Owner's Contact Number:")
contact_number_label.grid(row=4, column=0, padx=5, pady=5)
contact_number_entry = tk.Entry(registration_window)
contact_number_entry.grid(row=4, column=1, padx=5, pady=5)

# Create radio buttons for student and teacher
button_frame = tk.Frame(registration_window)
button_frame.grid(row=5, columnspan=2, pady=5)
student_radio = tk.Radiobutton(button_frame, text="Student", variable=role_var, value="student")
student_radio.grid(row=0, column=0, padx=5)
teacher_radio = tk.Radiobutton(button_frame, text="Teacher", variable=role_var, value="teacher")
teacher_radio.grid(row=0, column=1, padx=5)

# Create submit, update, and delete buttons
submit_button = tk.Button(registration_window, text="Submit", command=register)
submit_button.grid(row=6, column=0, padx=5, pady=10)
update_button = tk.Button(registration_window, text="Update", command=update)
update_button.grid(row=6, column=1, padx=5, pady=10)
delete_button = tk.Button(registration_window, text="Delete", command=delete)
delete_button.grid(row=6, column=2, padx=5, pady=10)

registration_window.mainloop()


 