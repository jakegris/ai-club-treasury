import pandas as pd
import smtplib
from email.message import EmailMessage
from datetime import datetime, timedelta
import os

# 1. Setup Data Source
SHEET_ID = "1xHaK_bcyCsQButBmceqd2-BippPWVVZYsUbwHlN0jEM"
PLANNING_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Spring+Term+FP%26A"

def check_deadlines():
    print("Checking Google Sheet for deadlines...")
    try:
        df = pd.read_csv(PLANNING_URL)
        # Clean column names in case of trailing spaces
        df.columns = df.columns.str.strip()
        
        today = datetime.now().date()
        alerts = []

        for _, row in df.iterrows():
            try:
                event_date = pd.to_datetime(row['Date']).date()
                rtp_deadline = event_date - timedelta(days=14)
                waiver_deadline = event_date - timedelta(days=21)

                if today == rtp_deadline:
                    alerts.append(f"🚨 RTP DUE TODAY: {row['Event']} (Event: {event_date})")
                if today == waiver_deadline:
                    alerts.append(f"🚨 CATERING WAIVER DUE: {row['Event']}")
            except:
                continue

        if alerts:
            send_email("\n".join(alerts))
            print(f"Deadlines found! Email sent to {os.environ.get('TREASURER_EMAIL')}")
        else:
            # THIS IS THE KEY: If you run this manually, it sends a heartbeat email
            print("No deadlines today. Sending System Check email...")
            send_email("No urgent deadlines found today. The system is online and watching your Google Sheet! 🦆")

    except Exception as e:
        error_msg = f"Automation Error: {e}"
        print(error_msg)
        send_email(error_msg)

def send_email(content):
    msg = EmailMessage()
    msg.set_content(f"Go Ducks!\n\n{content}\n\nHub: https://ai-club-treasury.streamlit.app")
    msg['Subject'] = "🦆 DUCKS TREASURY: System Update"
    msg['From'] = os.environ.get('EMAIL_USER')
    msg['To'] = os.environ.get('TREASURER_EMAIL')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(os.environ.get('EMAIL_USER'), os.environ.get('EMAIL_PASS'))
        smtp.send_message(msg)

if __name__ == "__main__":
    check_deadlines()
