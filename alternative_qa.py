"""
Alternative Q&A implementation without sentence-transformers dependency.
This file provides a backup solution for the main app.
"""

import os
import streamlit as st
from transformers import pipeline
import google.generativeai as genai

# Simple Q&A using transformers pipeline (no sentence-transformers needed)
@st.cache_resource
def get_simple_qa_model():
    """Load a simple Q&A model using transformers pipeline"""
    try:
        # Use a smaller, more reliable model
        return pipeline(
            "question-answering",
            model="distilbert-base-cased-distilled-squad",
            return_all_scores=True
        )
    except Exception as e:
        st.error(f"Could not load Q&A model: {str(e)}")
        return None

def simple_qa_without_embeddings(text, question):
    """Simple Q&A without vector embeddings - uses direct text search"""
    try:
        qa_model = get_simple_qa_model()
        if not qa_model:
            return "Q&A model not available"
        
        # Split text into chunks (simple approach)
        max_length = 512  # Model's maximum input length
        text_chunks = [text[i:i+max_length] for i in range(0, len(text), max_length)]
        
        best_answer = ""
        best_score = 0
        
        # Try each chunk and find the best answer
        for chunk in text_chunks:
            if len(chunk.strip()) < 50:  # Skip very short chunks
                continue
                
            try:
                result = qa_model(question=question, context=chunk)
                if isinstance(result, list):
                    result = result[0]  # Take the first result
                
                if result['score'] > best_score:
                    best_score = result['score']
                    best_answer = result['answer']
            except:
                continue
        
        if best_answer and best_score > 0.1:  # Confidence threshold
            return f"**Answer:** {best_answer}\n\n**Confidence:** {best_score:.2%}"
        else:
            return "Could not find a confident answer in the document."
            
    except Exception as e:
        return f"Error in Q&A: {str(e)}"

def enhanced_legal_qa(text, question, gemini_token=None):
    """Enhanced Q&A that combines simple search with Gemini"""
    try:
        # First, try simple keyword-based search
        question_lower = question.lower()
        text_lower = text.lower()
        
        # Find relevant paragraphs containing question keywords
        keywords = question_lower.split()
        relevant_paragraphs = []
        
        paragraphs = text.split('\n\n')
        for para in paragraphs:
            if any(keyword in para.lower() for keyword in keywords):
                relevant_paragraphs.append(para)
        
        if not relevant_paragraphs:
            return "No relevant information found in the document."
        
        # Use Gemini for better understanding if available
        if gemini_token:
            try:
                context = "\n\n".join(relevant_paragraphs[:3])  # Limit context
                prompt = f"""
                Based on the following legal document excerpt, answer this question: {question}
                
                Document excerpt:
                {context}
                
                Provide a clear, concise answer. If the answer is not in the text, say so.
                """
                
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(prompt)
                return response.text
            except:
                pass  # Fall back to simple method
        
        # Simple fallback
        return f"Found relevant information:\n\n{relevant_paragraphs[0][:500]}..."
        
    except Exception as e:
        return f"Error processing question: {str(e)}"

# Test function
def test_alternative_qa():
    """Test the alternative Q&A methods"""
    sample_text = """
    This Software License Agreement is entered into between TechCorp Inc. and BusinessSoft LLC.
    The license fee is $50,000 annually, payable in advance.
    The agreement shall continue for three years unless terminated earlier.
    Either party may terminate with 30 days written notice for material breach.
    """
    
    questions = [
        "What is the license fee?",
        "How long does the agreement last?",
        "What are the termination conditions?"
    ]
    
    st.write("## Testing Alternative Q&A Methods")
    
    for question in questions:
        st.write(f"**Question:** {question}")
        
        # Test simple Q&A
        simple_answer = simple_qa_without_embeddings(sample_text, question)
        st.write(f"**Simple Q&A:** {simple_answer}")
        
        # Test enhanced Q&A
        enhanced_answer = enhanced_legal_qa(sample_text, question)
        st.write(f"**Enhanced Q&A:** {enhanced_answer}")
        
        st.write("---")

if __name__ == "__main__":
    test_alternative_qa()