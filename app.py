import os
from dotenv import load_dotenv
import streamlit as st
import pdfplumber
from transformers import pipeline
import asyncio
import base64

# handling aync loop...
try:
  asyncio.get_running_loop()
except RuntimeError:
  ayncio.set_event_loop(asyncio.new_event_loop())

# loading environment variables from .env file 
load_dotenv()

# fetch token
# hf_token = os.getenv("HF_TOKEN")
gemini_token = os.getenv("GEMINI_TOKEN")

# catching the summarizer model...
@st.cache_resource
def load_summarizer():
  return pipeline ("summarization", model="facebook/bart-large-cnn", token = gemini_token)

summarizer = load_summarizer()

# text extracting...
def extract_text_from_pdf(uploaded_file):
  text = ""
  with pdfplumber.open(uploaded_file) as pdf:
    for page in pdf.pages:
      text += page.extract_text() + "\n"
  return text if text else "[ERROR] No text found in the PDF."

# styling using HTML/CSS...
st.markdown(
  """
  <style>
    body {background-color: #f4f4f4;}
    .main {backgoround-color: #ffffff; padding : 20px; border-radius: 10px; box-shadow: 0px 0px 10px rgba(0, 0, 0, 0.1);}
    h1 {color: #0078ff; text-align: center;}
    .stButton>button {background-color: #0078ff; color: #ffffff; font-size: 18px; padding: 10px; border-radius: 5px;}
    st.TextInput>div>div>input {border-radius: 5px;}
  </style>
  """,
  unsafe_allow_html=True
)

# streamlit UI...
st.markdown("<h1> AI Legal Document Analyzer &Summarizer </h1>", unsafe_allow_html=True)
st.write("Upload a Legal Document to analyze and summarize its content.")

uploaded_file = st.file_uploader("Drag & Drop or Browse", type=["pdf"], help="Upload a file for summarization.")

if uploaded_file:
  with st.spinner("Extracting text from PDF..."):
    text = extract_text_from_pdf(uploaded_file)

  if text.startswith("[ERROR]"):
    st.error(text)

  else:
    with st.success("Text Extracted Successfully. Generating Summary..."):
    with st.spinner("Generating Summary..."):
      summary = summarizer(text[:1000], max_length = 1000, min_length = 50, do_sample = False)[0]["summary_text"]
      st.success("Text summarized successfully.")

    st.markdown ("Summary: ")
    st.info(summary)

    # downloading the summary...
    summary_bytes = summary.encode("utf-8")
    b64_summary = base64.b64encode(summary_bytes).decode()
    href = f'<a href="data:file/txt;base64,{b64}" download="summary.txt">Download Summary</a>'
    st.markdown(href, unsafe_allow_html=True)