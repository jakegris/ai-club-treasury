import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Setup Page
st.set_page_config(page_title="AI Club Treasury Assistant", layout="wide")
st.title("💰 AI Club Treasury Decision Support")

# 2. Secure Login (Simple version for you)
password = st.sidebar.text_input("Enter Treasurer Password", type="password")
if password == "YourSecretPassword123": # Change this!

    # 3. Setup AI (Gemini)
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    if api_key:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')

        # 4. Upload your Ledger (Excel or CSV)
        uploaded_file = st.file_uploader("Upload your current Ledger (CSV or Excel)", type=['csv', 'xlsx'])
        
        if uploaded_file:
            df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
            st.write("### Current Ledger View", df.head())

            # 5. Ask the AI for help
            user_question = st.text_input("Ask a treasury question (e.g., 'Can we afford $200 for pizza?')")
            
            if user_question:
                # We give the AI the data from your sheet + your question
                prompt = f"""
                You are the AI Club Treasurer assistant at University of Oregon. 
                Here is the current budget data: {df.to_string()}
                
                ASUO Rules to remember:
                - 10 day lead time for purchases.
                - No tax should be paid (we are tax exempt).
                
                Question: {user_question}
                """
                response = model.generate_content(prompt)
                st.info(f"**Assistant Recommendation:** {response.text}")
else:
    st.warning("Please enter the correct password in the sidebar to access treasury data.")
