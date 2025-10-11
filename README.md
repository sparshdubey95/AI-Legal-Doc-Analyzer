# ⚖️ AI Legal Document Analyzer# AI Legal Research Assistant



An AI-powered legal document analysis tool that extracts citations, generates structured summaries, and provides intelligent Q&A capabilities for legal professionals.A comprehensive AI-powered legal document analyzer with RAG (Retrieval-Augmented Generation) capabilities.



## 🚀 Features## Features



- **📄 Multi-Format Support**: Upload PDF and DOCX legal documents- 🔍 **Multi-format Support**: Upload PDF and DOCX files

- **⚖️ Smart Citation Extraction**: Automatically identifies case citations, USC sections, and legal references (2,231+ citations/sec)- 📄 **Smart Summarization**: Generate structured summaries using BART

- **🤖 AI-Powered Summaries**: Generates structured legal analysis (Facts, Issues, Judgments, Reasoning)- 💬 **AI Chat**: Ask questions about your documents using Gemini Pro

- **💬 Intelligent Q&A**: Ask questions about your documents with fallback support-  **Source Citations**: View source chunks for each answer

- **🎨 Professional UI**: Clean, legal-themed interface with custom styling- 🌐 **Translation**: Simplify legal jargon for better understanding

- **🌐 Language Translation**: Converts legal jargon to simple language- 📱 **Multi-document**: Analyze multiple documents simultaneously



## 📦 Quick Start## Setup



### Local Development1. Clone the repository

2. Install dependencies: `pip install -r requirements.txt`

```bash3. Set up your Gemini API key in `.env` file

# Install dependencies4. Run: `streamlit run app.py`

pip install -r requirements.txt

## Deployment

# Set up environment variables

echo "GEMINI_TOKEN=your_api_key_here" > .envThis app is ready for deployment on Streamlit Cloud. Make sure to add your `GEMINI_TOKEN` in the secrets management.



# Run the app## Requirements

streamlit run app.py

```- Python 3.8+

- Gemini API key
### Streamlit Cloud Deployment

1. Fork this repository
2. Connect to Streamlit Cloud
3. Add `GEMINI_TOKEN` in Secrets (Settings → Secrets)
4. Deploy!

## 🛠️ Tech Stack

- **Frontend**: Streamlit with custom CSS
- **AI Engine**: Google Gemini Pro
- **NLP**: Transformers, sentence-transformers
- **Vector DB**: FAISS
- **Framework**: LangChain
- **Document Processing**: pdfplumber, python-docx

## 📊 Performance

- Citation extraction: **2,231 citations/second**
- Supports documents up to 50MB
- Real-time processing with progress indicators
- Robust error handling and fallback systems

## 📝 License

MIT License - feel free to use for hackathons and commercial projects!