import os
import datetime
import spacy
from sentence_transformers import SentenceTransformer, util
from db_config import get_db_connection
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# Load NLP models
spacy_model = spacy.load("en_core_web_md")  # Changed from sm to md for vector support
sbert_model = SentenceTransformer('paraphrase-MiniLM-L6-v2')

# --- Preprocessing Function ---
def preprocess(text):
    doc = spacy_model(text.lower())
    return [token.lemma_ for token in doc if token.is_alpha and not token.is_stop]

# --- Lexical Token Overlap Similarity ---
def calculate_similarity(text1, text2):
    tokens1 = set(preprocess(text1))
    tokens2 = set(preprocess(text2))
    if not tokens1 or not tokens2:
        return 0.0
    common_tokens = tokens1.intersection(tokens2)
    return (2 * len(common_tokens)) / (len(tokens1) + len(tokens2)) * 100

# --- Semantic Similarity using SBERT ---
def semantic_similarity(text1, text2):
    embedding1 = sbert_model.encode(text1, convert_to_tensor=True)
    embedding2 = sbert_model.encode(text2, convert_to_tensor=True)
    score = util.pytorch_cos_sim(embedding1, embedding2)
    return float(score) * 100

# --- Semantic Similarity using spaCy ---
def spacy_similarity(text1, text2):
    doc1 = spacy_model(text1)
    doc2 = spacy_model(text2)
    return doc1.similarity(doc2) * 100

# --- Combined NLP-Based Comparison (SBERT + spaCy) ---
def compare_with_nlp(text1, text2):
    sbert_score = semantic_similarity(text1, text2)
    spacy_score = spacy_similarity(text1, text2)
    final_score = (sbert_score + spacy_score) / 2
    return round(final_score, 2)

# --- Full Comparison Function for History ---
def compare_texts(user_id, input_text, source_text):
    lexical_score = calculate_similarity(input_text, source_text)
    semantic_score = compare_with_nlp(input_text, source_text)  # uses SBERT + spaCy
    final_score = (lexical_score + semantic_score) / 2

    save_history(user_id, input_text, final_score)

    return {
        "lexical_similarity": round(lexical_score, 2),
        "semantic_similarity": round(semantic_score, 2),
        "final_score": round(final_score, 2)
    }

# --- Save to History Table ---
def save_history(user_id, input_text, plagiarism_percent):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO History (user_id, input_text, plagiarism_percent) VALUES (?, ?, ?)",
                   (user_id, input_text, plagiarism_percent))
    conn.commit()
    conn.close()

# --- Web Snippet Plagiarism (uses SBERT only) ---
def check_web_plagiarism(text, snippets):
    scores = []
    for snippet in snippets:
        score = semantic_similarity(text, snippet)
        scores.append(score)
    avg_score = sum(scores) / len(scores) if scores else 0
    return round(avg_score, 2)