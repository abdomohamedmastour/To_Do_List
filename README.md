# To-Do List Web Application

A full-stack web application for managing daily tasks and personal to-do lists, built using Flask and MySQL.

## Project Features

- User Authentication: Secure user registration and login functionality.
- Task Management: Create, view, update, and delete daily tasks (CRUD operations).
- Security: Password hashing using bcrypt and session-based user authentication.

## Tech Stack

- Backend: Python (Flask, PyMySQL)
- Database: MySQL
- Frontend: HTML, CSS, JavaScript

## Database Setup

1. Open MySQL Workbench or your MySQL client.
2. Run the SQL script located at `database/schema.sql` to initialize the database structure and required tables.

## How to Run Locally

1. Clone the repository:
   git clone https://github.com/abdomohamedmastour/To_Do_List.git

2. Install dependencies:
   pip install -r requirements.txt

3. Create a `.env` file in the root directory with your database configuration:
   DB_HOST=localhost
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   DB_NAME=todo_db
   SECRET_KEY=your_secret_key

4. Start the application:
   python app.py

5. Access the app in your browser at `http://127.0.0.1:5000`.

## Project Team

- Abdelrahman Mastour
- Mohamed Ibrahim
