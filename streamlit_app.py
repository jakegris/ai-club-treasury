import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="AI Club Treasury Assistant", layout="wide")
st.title("💰 AI Club Treasury Decision Support")

password = st.sidebar.text_input("Enter Treasurer Password", type="password")

if password == "AICLUBTREASURE":
    api_key = st.sidebar.text_input("Gemini API Key", type="password")
    
    if api_key:
        try:
            genai.configure(api_key=api_key)
            
            # --- DEBUG SECTION: Let's see what models you actually have ---
            st.sidebar.write("### Available Models for your Key:")
            available_models = []
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    available_models.append(m.name.replace('models/', ''))
            
            # This creates a dropdown so you can pick the one that works!
            selected_model = st.sidebar.selectbox("Select Model", available_models if available_models else ["gemini-1.5-flash"])
            st.sidebar.info(f"Using: {selected_model}")
            
            model = genai.GenerativeModel(selected_model)
            # -----------------------------------------------------------

            uploaded_file = st.file_uploader("Upload Ledger (CSV or Excel)", type=['csv', 'xlsx'])
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
                st.write("### Current Ledger View", df.head())

                user_question = st.text_input("Ask a treasury question:")
                
                if user_question:
                    prompt = f"Budget Data:\n{df.to_string()}\n\nQuestion: {user_question}"
                    response = model.generate_content(prompt)
                    st.info(f"**Assistant:** {response.text}")
                    
        except Exception as e:
            st.error(f"Error: {e}")
else:
    st.warning("Please enter the password in the sidebar.")
else:
    st.warning("Please enter the correct password in the sidebar to access treasury data.")
