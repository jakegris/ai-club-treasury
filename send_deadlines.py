import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import os

# 1. Setup Data Source (Your Google Sheet)
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Spring+Term+FP%26A"

def check_deadlines():
    try:
        df = pd.read_csv(PLANNING_URL)
        today = datetime.now().date()
        alerts = []

        for _, row in df.iterrows():
            event_date = pd.to_datetime(row['Date']).date()
            # ASUO Rules
            rtp_deadline = event_date - timedelta(days=14)
            waiver_deadline = event_date - timedelta(days=21)

            if today == rtp_deadline:
                alerts.append(f"🚨 RTP DUE TODAY for {row['Event']} (Event Date: {event_date})")
            if today == waiver_deadline:
                alerts.append(f"🚨 CATERING WAIVER DUE TODAY for {row['Event']}")

        if alerts:
            send_email("\n".join(alerts))
    except Exception as e:
        print(f"Error: {e}")

def send_email(content):
    msg = EmailMessage()
    msg.set_content(f"Go Ducks! You have the following Treasury deadlines today:\n\n{content}\n\nCheck the Hub: https://ai-club-treasury.streamlit.app")
    msg['Subject'] = "🦆 DUCKS TREASURY: Deadline Alert"
    msg['From'] = os.environ.get('EMAIL_USER')
    msg['To'] = os.environ.get('TREASURER_EMAIL')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.environ.get('EMAIL_USER'), os.environ.get('EMAIL_PASS'))
        smtp.send_message(msg)

if __name__ == "__main__":
    check_deadlines()
