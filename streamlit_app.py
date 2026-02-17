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

            # --- MODEL SELECTION ---
            # We get the list from Google, but also add the most stable ones manually
            try:
                fetched_models = [m.name.replace('models/', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            except:
                fetched_models = []
            
            # These are the stable ones we WANT to see
            stable_options = ["gemini-1.5-flash", "gemini-1.5-flash-8b", "gemini-1.5-pro"]
            
            # Combine them and remove duplicates
            all_options = list(dict.fromkeys(stable_options + fetched_models))
            
            selected_model = st.sidebar.selectbox("Select Model (Choose 1.5-flash for stability)", all_options)
            model = genai.GenerativeModel(selected_model)

            # --- FILE UPLOADER ---
            uploaded_file = st.file_uploader("Upload Ledger (CSV or Excel)", type=['csv', 'xlsx'])

            if uploaded_file:
                if uploaded_file.name.endswith('xlsx'):
                    df = pd.read_excel(uploaded_file)
                else:
                    df = pd.read_csv(uploaded_file)

                st.write("### Current Ledger View", df.head())

                # --- CHAT INTERFACE ---
                user_question = st.text_input("Ask a question about the budget:")
                ask_button = st.button("Ask AI") # Button prevents accidental double-requests

                if ask_button and user_question:
                    # Provide simple instructions to the AI
                    prompt = f"You are the Treasurer Assistant. Based on this data:\n{df.to_string()}\n\nQuestion: {user_question}"
                    
                    with st.spinner('AI is thinking...'):
                        try:
                            response = model.generate_content(prompt)
                            st.info(f"**Assistant:** {response.text}")
                        except Exception as chat_err:
                            st.error(f"Quota error: Please wait 60 seconds. The Free Tier is currently busy. Error: {chat_err}")

        except Exception as e:
            st.error(f"Error connecting to Google AI: {e}")
    else:
        st.info("Please enter your Gemini API Key in the sidebar.")

else:
    st.warning("Please enter the correct Treasurer Password in the sidebar.")
