# Student Placement Management System

A complete Streamlit + SQLite web application for managing campus placements.

## Features
- Student registration and login
- Admin dashboard with placement statistics
- Manage student records
- Add and manage company profiles
- Publish, close, update and delete job listings
- Students can browse jobs and apply with a PDF/DOC/DOCX resume
- Students can track application status
- Admin can update application status and download uploaded resumes
- SQLite database is created automatically on first run
- Sample company and job are seeded automatically

## Requirements
- Python 3.9 or newer

## Run locally
1. Extract the ZIP.
2. Open a terminal in the extracted folder.
3. Create and activate a virtual environment (recommended).
4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Start the website:

   ```bash
   streamlit run app.py
   ```

6. Open the local URL shown in the terminal (usually http://localhost:8501).

## Demo admin login
- Email: `admin@campus.com`
- Password: `admin123`

Change the demo password and use a stronger password before deploying publicly.

## Deployment
For Streamlit Community Cloud:
1. Push `app.py`, `requirements.txt`, and `README.md` to a GitHub repository.
2. In Streamlit Community Cloud, create an app from that repository.
3. Set the main file path to `app.py`.
4. Deploy.

Note: Streamlit Community Cloud storage may be ephemeral. For a production deployment, use managed persistent storage/database and secure password hashing/secrets. This project is a college/demo project starter, not a hardened production authentication system.

## Project structure
```text
student_placement_management_system/
├── app.py
├── requirements.txt
├── README.md
├── .gitignore
└── uploads/              # created automatically for resumes
```
