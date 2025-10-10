# Quick Installation Script for Missing Dependencies

# Run this to install remaining packages:
pip install streamlit==1.50.0
pip install google-generativeai>=0.3.1  
pip install langchain>=0.0.340
pip install langchain-google-genai>=0.0.5
pip install faiss-cpu>=1.12.0

# Test the installation:
python -c "import streamlit; print('Streamlit OK')"
python -c "import google.generativeai; print('Gemini OK')"

# Run the app:
streamlit run app.py