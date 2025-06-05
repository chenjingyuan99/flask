FLASK-SUM-APP/
├─ assignment1.py          # Main Flask application
├─ templates/
│  └─ index.html           # Web interface
├─ uploads/               # Directory for uploaded files


Test locally:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flask run


Error Handling: The application handles various edge cases including missing data fields, unavailable pictures, duplicate photo uploads, and incorrect file types. It provides user-friendly error messages through Flask’s flash messaging system.


group: demoflask_group
appservice plan: ASP-demoflaskgroup-a4f1
storage account: 
container: 

