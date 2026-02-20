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
        df.columns = df.columns.str.strip() # Clean column names
        
        today = datetime.now().date()
        alerts = []

        for _, row in df.iterrows():
            try:
                # Adjust column names 'Date' and 'Event' to match your sheet exactly
                event_date = pd.to_datetime(row['Date']).date()
                event_name = row['Event']
                
                # UO Rules: 14 days for RTP, 21 days for Catering/Waivers
                rtp_deadline = event_date - timedelta(days=14)
                waiver_deadline = event_date - timedelta(days=21)

                if today == rtp_deadline:
                    alerts.append(f"🚨 RTP FORM DUE: {event_name} (Event Date: {event_date})")
                if today == waiver_deadline:
                    alerts.append(f"🚨 CATERING WAIVER DUE: {event_name} (Event Date: {event_date})")
            except:
                continue

        if alerts:
            send_email("\n".join(alerts), "Action Required: Treasury Deadlines")
            print("Alerts found. Email sent.")
        else:
            print("No deadlines today. No email sent.")

    except Exception as e:
        # We keep this so you know if the script crashes
        print(f"Error: {e}")
        send_email(f"The deadline checker encountered an error: {e}", "System Error: Deadline Checker")

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
