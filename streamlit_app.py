import streamlit as st
import pandas as pd
import google.generativeai as genai

# 1. Page Configuration
st.set_page_config(page_title="AI Club Treasury Assistant", layout="wide")
st.title("💰 AI Club Treasury Assistant")

# 2. Sidebar Credentials
password = st.sidebar.text_input("Enter Treasurer Password", type="password")

if password == "AICLUBTREASURE":
    api_key = st.sidebar.text_input("Gemini API Key", type="password")

    if api_key:
        try:
            genai.configure(api_key=api_key)

            # --- AUTO-SELECT MODEL ---
            # This part finds which models your key is allowed to use
            available_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            if available_models:
                selected_model = st.sidebar.selectbox("Select Model", available_models)
                model = genai.GenerativeModel(selected_model)
            else:
                st.error("No compatible models found for this API key.")
                st.stop()

            # --- FILE UPLOADER ---
            uploaded_file = st.file_uploader("Upload Ledger (CSV or Excel)", type=['csv', 'xlsx'])

            if uploaded_file:
                # Read the file
                if uploaded_file.name.endswith('xlsx'):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)

                st.write("### Current Ledger View (Top 5 Rows)", df.head())

                # --- CHAT INTERFACE ---
                user_question = st.text_input("Ask a question about the budget:")

                if user_question:
                    # The prompt sends the data to the AI
                    prompt = f"Here is the club budget data:\n\n{df.to_string()}\n\nQuestion: {user_question}"
                    
                    with st.spinner('AI is analyzing the ledger...'):
                        response = model.generate_content(prompt)
                        st.info(f"**Assistant:** {response.text}")

        except Exception as e:
            st.error(f"Error connecting to Google AI: {e}")
    else:
        st.info("Please enter your Gemini API Key in the sidebar to start.")

else:
    st.warning("Please enter the correct Treasurer Password in the sidebar.")
