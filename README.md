# NumberPlateDetection


The provided code is a Python application built using the tkinter library for creating a user interface and OpenCV for camera functionalities. It serves as a camera application with features like capturing images, recording videos, detecting license plates from camera feed, and querying a MySQL database to match detected license plates with registered users.

Here's a summary of the main functionalities:

Login Authentication: Users need to authenticate themselves with a username and password to access the camera application. Only the admin username and password are accepted.
Camera Application: After successful login, the camera application opens with options to capture images, start/stop video recording, and display the camera feed. The application continuously captures frames from the camera and displays them in the UI.
License Plate Detection: The application uses OpenCV to detect license plates from the camera feed. It employs the Tesseract OCR library to extract text from the detected plates. Detected license plates are then matched against a MySQL database containing registered users' information.
Database Interaction: The application queries a MySQL database to check if detected license plates belong to registered users. It supports both student and teacher roles, with separate tables in the database for each role.
User Registration: Users can register their vehicle details, including registration number, owner's name, license number, department, contact number, and a PDF copy of the driving license. The registration process distinguishes between students and teachers and inserts data into the corresponding database table.
Update and Delete Records: Users can update existing records in the database by providing the registration number and modifying relevant fields. Additionally, they can delete records based on the registration number.
PDF Upload: Users can upload a PDF copy of their driving license, which is stored in a specified directory and the file path is stored in the database.
