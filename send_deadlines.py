import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime
import os

SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Spring+Term+FP%26A"

def check_deadlines():
    try:
        # Skip 3 rows to match your Row 4 headers
        df = pd.read_csv(PLANNING_URL, skiprows=3)
        df.columns = df.columns.str.strip()
        
        today = datetime.now().date()
        alerts = []

        for _, row in df.iterrows():
            try:
                # 1. Check Long Form PO Due Date
                po_deadline = pd.to_datetime(row['Long Form PO due date']).date()
                if today == po_deadline:
                    alerts.append(f"🚨 PO DUE TODAY: {row['Event']} (Week {row['Week #']})")

                # 2. Check Catering Waiver Due Date
                waiver_deadline = pd.to_datetime(row['Catering Waiver']).date()
                if today == waiver_deadline:
                    alerts.append(f"🚨 CATERING WAIVER DUE TODAY: {row['Event']}")
            except:
                continue

        if alerts:
            send_email("\n".join(alerts), "Urgent Deadlines Today")
    except Exception as e:
        print(f"Error: {e}")

def send_email(content, subject):
    msg = EmailMessage()
    msg.set_content(f"Go Ducks!\n\n{content}\n\nHub: https://ai-club-treasury.streamlit.app")
    msg['Subject'] = f"🦆 DUCKS TREASURY: {subject}"
    msg['From'] = os.environ.get('EMAIL_USER')
    msg['To'] = os.environ.get('TREASURER_EMAIL')
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.environ.get('EMAIL_USER'), os.environ.get('EMAIL_PASS'))
        smtp.send_message(msg)

if __name__ == "__main__":
    check_deadlines()
