import streamlit as st
import pandas as pd
import google.generativeai as genai

st.set_page_config(page_title="UO AI Club Treasury", layout="wide")
st.title("💰 Treasury Assistant")

# Sidebar for Setup
with st.sidebar:
    st.header("Setup")
    password = st.text_input("Treasurer Password", type="password")
    api_key = st.text_input("Gemini API Key", type="password")

if password == "AICLUBTREASURE" and api_key:
    try:
        genai.configure(api_key=api_key)
        
        # --- DYNAMIC MODEL DISCOVERY ---
        # We ask the API: "What can I actually use right now?"
        models = []
        try:
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    models.append(m.name) # We keep the full 'models/...' name
        except Exception as e:
            st.error(f"Could not list models. Is your API key correct? Error: {e}")

        if models:
            # We show the full names to be 100% sure we match Google's requirements
            selected_model_name = st.selectbox("Select an Available Model:", models)
            model = genai.GenerativeModel(selected_model_name)
            
            st.success(f"Connected to {selected_model_name}")
            
            # --- LEDGER UPLOAD ---
            uploaded_file = st.file_uploader("Upload Ledger (Excel or CSV)", type=['xlsx', 'csv'])
            
            if uploaded_file:
                df = pd.read_excel(uploaded_file) if uploaded_file.name.endswith('xlsx') else pd.read_csv(uploaded_file)
                st.dataframe(df.head(5)) # Show a preview

                # --- CHAT ---
                query = st.text_input("Ask a question about the budget:")
                if st.button("Query Ledger") and query:
                    # Small helper to format the table for the AI
                    table_context = df.to_string()
                    prompt = f"Data:\n{table_context}\n\nQuestion: {query}"
                    
                    try:
                        response = model.generate_content(prompt)
                        st.info(f"**AI Response:**\n{response.text}")
                    except Exception as e:
                        st.error(f"The model failed to answer. Error: {e}")
        else:
            st.warning("No models found. Check if your API key is active in Google AI Studio.")

    except Exception as e:
        st.error(f"System Error: {e}")
else:
    st.info("Please enter your Password and API Key in the sidebar to begin.")
