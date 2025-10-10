import os
from dotenv import load_dotenv
import streamlit as st
import pdfplumber
import docx
from transformers import pipeline
import asyncio
import base64
import re
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
import google.generativeai as genai
import alternative_qa

# handling aync loop...
try:
    asyncio.get_running_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# loading environment variables from .env file 
load_dotenv()

# fetch token
gemini_token = os.getenv("GEMINI_TOKEN")
if gemini_token:
    genai.configure(api_key=gemini_token)

# text extracting...
def extract_text_from_files(uploaded_files):
    full_text = ""
    for file in uploaded_files:
        if file.type == "application/pdf":
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        full_text += f"--- Content from {file.name} ---\n" + page_text + "\n\n"
        elif file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
            doc = docx.Document(file)
            for para in doc.paragraphs:
                if para.text.strip():
                    full_text += para.text + "\n"
            full_text += f"--- Content from {file.name} ---\n\n"
    return full_text if full_text else "Error: No text could be extracted from the uploaded documents."

# Initialize HuggingFace embeddings (cached for performance)
@st.cache_resource
def get_embeddings(model_choice="default"):
    """Load HuggingFace embeddings model - Multiple options for different use cases!"""
    
    # Define available models (smaller models for better performance)
    model_options = {
        "default": "sentence-transformers/all-MiniLM-L6-v2",  # Fast, good quality
        "small": "sentence-transformers/paraphrase-MiniLM-L3-v2",  # Smaller, faster
        "legal": "sentence-transformers/all-mpnet-base-v2",  # Better for legal docs
        "multilingual": "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    }
    
    try:
        # Try sentence-transformers first
        from sentence_transformers import SentenceTransformer
        model_name = model_options.get(model_choice, model_options["default"])
        
        return HuggingFaceEmbeddings(
            model_name=model_name,
            model_kwargs={'device': 'cpu'},
            encode_kwargs={'normalize_embeddings': True}
        )
    except ImportError:
        # Fallback to basic transformers without sentence-transformers
        try:
            st.warning("⚠️ Using fallback embedding method (sentence-transformers not available)")
            from transformers import AutoTokenizer, AutoModel
            import torch
            
            # Use a basic transformer model
            model_name = "microsoft/DialoGPT-medium"  # Available in transformers
            return HuggingFaceEmbeddings(
                model_name="sentence-transformers/all-MiniLM-L6-v2",  # This will fallback internally
                model_kwargs={'device': 'cpu'}
            )
        except Exception as fallback_error:
            st.error("🚨 Could not load any embedding model!")
            st.error("Please install: pip install sentence-transformers==2.2.2")
            st.info("💡 Alternative: You can still use other features like citation extraction and legal summaries.")
            return None
    except Exception as e:
        st.error(f"❌ Error loading embeddings: {str(e)}")
        st.error("🔧 Trying alternative embedding method...")
        return None

# Function to create the vector store
@st.cache_resource
def get_vector_store(text_chunks):
    """Create FAISS vector store with HuggingFace embeddings"""
    try:
        embeddings = get_embeddings()
        vector_store = FAISS.from_texts(text_chunks, embedding=embeddings)
        vector_store.save_local("faiss_index")
        return True
    except Exception as e:
        st.error(f"Error creating vector store: {str(e)}")
        return False

# Function to create the conversational chain
def get_conversational_chain():
    prompt_template = """
    Answer the question as detailed as possible from the provided context, making sure to provide all the details. If the answer is not in
    the provided context, just say, "The answer is not available in the context". Don't provide a wrong answer.\n\n
    Context:\n {context}?\n
    Question: \n{question}\n

    Answer:
    """
    if gemini_token:
        model = ChatGoogleGenerativeAI(model="gemini-pro", temperature=0.3, google_api_key=gemini_token)
        prompt = PromptTemplate(template=prompt_template, input_variables=["context", "question"])
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)
        return chain
    return None

# Function to handle user input and get a response
def user_input(user_question):
    # Prefer the RAG flow when embeddings and FAISS are available
    embeddings = None
    try:
        embeddings = get_embeddings()
    except Exception:
        embeddings = None

    faiss_exists = os.path.exists("faiss_index")

    # If embeddings and FAISS vector store are available, try RAG
    if embeddings and faiss_exists:
        try:
            new_db = FAISS.load_local("faiss_index", embeddings, allow_dangerous_deserialization=True)
            docs = new_db.similarity_search(user_question, k=4)

            chain = get_conversational_chain()
            if chain:
                with st.spinner("🤔 Analyzing your question (RAG)..."):
                    response = chain({"input_documents": docs, "question": user_question}, return_only_outputs=True)

                st.success("✅ Answer generated successfully (RAG)!")
                st.markdown(f"**🤖 AI Response:** {response['output_text']}")

                with st.expander("📚 View Sources Used", expanded=False):
                    for i, doc in enumerate(docs):
                        st.markdown(f"**Source {i+1}:**")
                        st.text_area(f"source_{i}", doc.page_content[:300] + "...", height=100, key=f"source_{i}")
                return
            else:
                st.warning("RAG chain initialization failed — falling back to local Q&A.")
        except Exception as e:
            st.warning(f"RAG failed: {str(e)} — falling back to local Q&A.")

    # Fallback: use local/simple Q&A methods (no sentence-transformers/faiss required)
    st.info("Using fallback local Q&A (no embeddings required).")
    try:
        if 'full_text' not in st.session_state:
            st.error("No document text available. Upload and analyze documents first.")
            return

        # Try the enhanced hybrid fallback (may use Gemini if token available)
        answer = alternative_qa.enhanced_legal_qa(st.session_state.full_text, user_question, gemini_token if gemini_token else None)
        st.success("✅ Fallback answer generated")
        st.markdown(f"**🧭 Fallback Answer:** {answer}")
    except Exception as e:
        st.error(f"Fallback Q&A failed: {str(e)}")

# Translation function
def translate_text(text, target_language="simple, layman-friendly language"):
    if gemini_token:
        prompt = f"Translate the following text into {target_language}. Make it easy to understand for non-legal professionals:\n\n{text}"
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        return response.text
    return "Translation service not available."

# Legal citation extraction function
def extract_legal_citations(text):
    """Extract legal citations from text using regex patterns"""
    citations = []
    citation_dict = {}  # To avoid duplicates
    
    patterns = [
        (r'\b\d{1,4}\s+[A-Z][a-z]*\.?\s+\d{1,4}\b', 'Case Reporter'),  # "123 F.Supp. 456"
        (r'\b[A-Z][a-z]+\s+v\.?\s+[A-Z][a-z]+\b', 'Case Name'),  # "Smith v. Jones"
        (r'\b\d{1,3}\s+U\.S\.C?\.?\s+§?\s*\d+\b', 'USC Section'),  # USC sections
        (r'\bSection\s+\d+\b', 'Section Reference'),  # Section references
        (r'\bArticle\s+[IVXLCDM]+\b', 'Article Reference'),  # Article I, II, etc.
        (r'\b\d{4}\s+[A-Z]{2,}\s+\d+\b', 'Statute'),  # "2020 Cal. 123"
    ]
    
    for pattern, citation_type in patterns:
        matches = re.finditer(pattern, text, re.IGNORECASE)
        for match in matches:
            citation_text = match.group().strip()
            if citation_text not in citation_dict:
                citation_dict[citation_text] = {
                    'text': citation_text,
                    'type': citation_type,
                    'start': match.start(),
                    'end': match.end(),
                    'context': text[max(0, match.start()-50):min(len(text), match.end()+50)]
                }
    
    citations = list(citation_dict.values())
    return sorted(citations, key=lambda x: x['start'])

# Legal-specific structured summary using Gemini
def generate_legal_summary(text):
    """Generate structured legal summary with Facts, Issues, Judgments, and Reasoning"""
    if not gemini_token:
        return "Legal summary unavailable - Gemini API token not found"
    
    try:
        # Use Gemini 1.5 Pro with increased token limits
        model = genai.GenerativeModel(
            'gemini-1.5-pro-latest',
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=8192,
                temperature=0.1,
                candidate_count=1
            )
        )
        
        legal_prompt = f"""You are an expert legal AI assistant. Analyze this legal document and provide a comprehensive structured summary with these exact sections:

**FACTS:**
[Summarize the key factual background, parties involved, circumstances, and relevant events]

**ISSUES:**
[Identify the main legal questions, disputes, controversies, or matters that need to be addressed]

**JUDGMENTS/HOLDINGS:**
[State the court's decisions, rulings, legal conclusions, or outcomes]

**REASONING:**
[Explain the legal reasoning, precedents cited, statutory interpretations, and judicial rationale]

Document text: {text[:6000]}

Use professional legal language appropriate for lawyers and legal professionals. Be comprehensive and precise."""
        
        response = model.generate_content(legal_prompt)
        return response.text
    except Exception as e:
        # Fallback to gemini-pro if 1.5-pro fails
        try:
            model = genai.GenerativeModel('gemini-pro')
            response = model.generate_content(legal_prompt)
            return response.text
        except Exception as e2:
            return f"Error generating legal summary: {str(e2)}"

# styling using HTML/CSS...
st.set_page_config(page_title="AI Legal Research Assistant", page_icon="⚖️", layout="wide")

# Custom CSS for a professional legal look
st.markdown("""
    <style>
    /* Main app background */
    .stApp {
        background-color: #f5f7fa;
    }

    /* Main content area */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }

    /* Title styling */
    h1 {
        font-family: 'Georgia', serif;
        color: #1f4e79;
        text-align: center;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }

    /* Section headers */
    h2, h3 {
        color: #2c5282;
        border-bottom: 2px solid #2c5282;
        padding-bottom: 0.5rem;
        margin-top: 1.5rem;
    }

    /* Subheader/instruction styling */
    .stMarkdown p {
        font-family: 'Segoe UI', sans-serif;
        font-size: 1.05rem;
        color: #2d3748;
    }

    /* File uploader styling */
    .stFileUploader {
        border: 2px dashed #2c5282;
        border-radius: 10px;
        background-color: #ffffff;
        padding: 20px;
    }

    /* Button styling */
    .stButton>button {
        border: none;
        border-radius: 8px;
        color: #ffffff;
        background: linear-gradient(135deg, #2c5282 0%, #1f4e79 100%);
        padding: 12px 28px;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease-in-out;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stButton>button:hover {
        background: linear-gradient(135deg, #1f4e79 0%, #2c5282 100%);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        transform: translateY(-1px);
    }

    /* Citation box styling */
    .citation-box {
        background: linear-gradient(135deg, #f7fafc 0%, #edf2f7 100%);
        border-left: 4px solid #3182ce;
        padding: 1rem 1.5rem;
        margin: 1rem 0;
        border-radius: 6px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }

    /* Legal summary styling */
    .legal-summary {
        background: linear-gradient(135deg, #edf2f7 0%, #e2e8f0 100%);
        padding: 1.5rem;
        border-radius: 10px;
        border: 1px solid #cbd5e0;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
    }

    /* Info/success boxes */
    .stSuccess {
        background-color: #c6f6d5;
        border-left: 4px solid #38a169;
        border-radius: 6px;
        padding: 1rem;
    }

    .stInfo {
        background-color: #bee3f8;
        border-left: 4px solid #3182ce;
        border-radius: 6px;
        padding: 1rem;
    }

    /* Expander styling */
    .streamlit-expanderHeader {
        background-color: #edf2f7;
        border-radius: 8px;
        font-weight: 600;
        color: #2c5282;
    }

    /* Text input styling */
    .stTextInput>div>div>input {
        border-radius: 8px;
        border: 2px solid #cbd5e0;
        padding: 10px;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #3182ce;
        box-shadow: 0 0 0 1px #3182ce;
    }

    /* Main header class */
    .main-header {
        font-size: 2.5rem;
        color: #1f4e79;
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 700;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    /* Section header class */
    .section-header {
        color: #2c5282;
        border-bottom: 2px solid #2c5282;
        padding-bottom: 0.5rem;
        margin-bottom: 1rem;
    }
    </style>
""", unsafe_allow_html=True)

# streamlit UI...
st.title("⚖️ AI Legal Research Assistant")
st.write("Upload legal documents (PDF or DOCX) to get structured summaries and ask complex questions.")

# --- Main app layout with columns ---
col1, col2 = st.columns([1, 1])

with col1:
    st.header("Document Upload & Analysis")
    uploaded_files = st.file_uploader(
        "Upload your PDF or DOCX documents",
        type=["pdf", "docx"],
        accept_multiple_files=True
    )

with col2:
    st.header("Actions & Results")
    if uploaded_files:
        if st.button("Analyze Documents"):
            with st.spinner("Extracting text from all documents..."):
                text = extract_text_from_files(uploaded_files)
            
            if text.startswith("Error:"):
                st.error(text)
            else:
                # Generate legal-specific structured summary
                with st.spinner("Generating Legal Summary with AI..."):
                    summary = generate_legal_summary(text)
                    st.success("Legal summary generated successfully!")
                
                # Extract legal citations
                with st.spinner("Extracting legal citations..."):
                    citations = extract_legal_citations(text)
                    st.success(f"Found {len(citations)} legal citations!")
                
                # Store in session state
                st.session_state.summary = summary
                st.session_state.full_text = text
                st.session_state.citations = citations
                
                # Create vector store for RAG
                with st.spinner("Creating knowledge base for Q&A..."):
                    text_splitter = RecursiveCharacterTextSplitter(chunk_size=10000, chunk_overlap=1000)
                    text_chunks = text_splitter.split_text(text)
                    
                    if get_vector_store(text_chunks):
                        st.success("✅ Document analysis complete! You can now view summaries, citations, and ask questions below.")
                        st.session_state.vector_store_ready = True
                    else:
                        st.warning("Q&A feature not available. Please check your Gemini API token.")

# Use st.expander to neatly organize the output
with st.expander("📋 View Structured Legal Summary", expanded=True):
    st.markdown('<h2 class="section-header">Structured Legal Summary</h2>', unsafe_allow_html=True)
    if 'summary' in st.session_state:
        st.markdown(f'<div class="legal-summary">{st.session_state.summary}</div>', unsafe_allow_html=True)
        
        # Translation feature
        if st.button("🌐 Translate Summary to Simple Language"):
            with st.spinner("Translating to simple language..."):
                simple_summary = translate_text(st.session_state.summary)
                st.markdown('<h3 class="section-header">Simplified Summary</h3>', unsafe_allow_html=True)
                st.success(simple_summary)
        
        # downloading the summary...
        summary_bytes = st.session_state.summary.encode("utf-8")
        b64_summary = base64.b64encode(summary_bytes).decode()
        href = f'<a href="data:file/txt;base64,{b64_summary}" download="legal_summary.txt">📥 Download Summary</a>'
        st.markdown(href, unsafe_allow_html=True)
    else:
        st.markdown("Your structured legal summary will appear here after analysis.")

# Legal Citations Section
with st.expander("⚖️ Extracted Legal Citations", expanded=False):
    st.markdown('<h2 class="section-header">Legal Citations</h2>', unsafe_allow_html=True)
    if 'citations' in st.session_state and st.session_state.citations:
        st.write(f"**Total Citations Found:** {len(st.session_state.citations)}")
        
        for idx, citation in enumerate(st.session_state.citations, 1):
            citation_html = f"""
            <div class="citation-box">
                <strong>Citation {idx}:</strong> {citation['text']}<br>
                <small><em>Type:</em> {citation['type']}</small><br>
                <small><em>Context:</em> ...{citation['context']}...</small>
            </div>
            """
            st.markdown(citation_html, unsafe_allow_html=True)
        
        # Download citations
        if st.button("📥 Download All Citations"):
            citations_text = "\n\n".join([f"Citation {i+1}:\n{c['text']}\nType: {c['type']}\nContext: {c['context']}\n" 
                                         for i, c in enumerate(st.session_state.citations)])
            citations_bytes = citations_text.encode("utf-8")
            b64_citations = base64.b64encode(citations_bytes).decode()
            href = f'<a href="data:file/txt;base64,{b64_citations}" download="legal_citations.txt">Download Citations File</a>'
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("Legal citations will appear here after document analysis.")

with st.expander("Ask the Document (AI Chat)"):
    st.subheader("Chat with your Documents")
    
    if 'vector_store_ready' in st.session_state and st.session_state.vector_store_ready:
        user_question = st.text_input("Ask a question about the content of your documents:")
        
        if user_question:
            user_input(user_question)
    else:
        st.info("Please upload and analyze documents first to enable Q&A functionality.")

# Footer
st.markdown("---")
st.markdown("**Note:** This app supports PDF and DOCX files up to 50MB each. For best results, use clear, text-based documents.")