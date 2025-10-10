# AI Legal Research Assistant

A comprehensive AI-powered legal document analyzer with RAG (Retrieval-Augmented Generation) capabilities.

## Features

- 🔍 **Multi-format Support**: Upload PDF and DOCX files
- 📄 **Smart Summarization**: Generate structured summaries using BART
- 💬 **AI Chat**: Ask questions about your documents using Gemini Pro
- 🎙️ **Voice Input**: Voice-to-text question input
- 🔊 **Audio Responses**: Text-to-speech for answers
- 📚 **Source Citations**: View source chunks for each answer
- 🌐 **Translation**: Simplify legal jargon for better understanding
- 📱 **Multi-document**: Analyze multiple documents simultaneously

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your Gemini API key in `.env` file
4. Run: `streamlit run app.py`

## Deployment

This app is ready for deployment on Streamlit Cloud. Make sure to add your `GEMINI_TOKEN` in the secrets management.

## Requirements

- Python 3.8+
- Gemini API key
- Microphone access (for voice features)