# nlp_utils.py

# --- spaCy setup ---
import spacy
nlp = spacy.load("en_core_web_md")

def semantic_similarity(text1, text2):
    """
    Semantic similarity using spaCy word vectors.
    Returns a float between 0 and 1.
    """
    doc1 = nlp(text1)
    doc2 = nlp(text2)
    return doc1.similarity(doc2)

# --- SBERT setup ---
from sentence_transformers import SentenceTransformer, util
import torch

sbert_model = SentenceTransformer('all-MiniLM-L6-v2')

def embedding_similarity(text1, text2):
    """
    Semantic similarity using SBERT sentence embeddings.
    Returns a float between 0 and 1.
    """
    embeddings = sbert_model.encode([text1, text2], convert_to_tensor=True)
    similarity_score = util.pytorch_cos_sim(embeddings[0], embeddings[1])
    return float(similarity_score)
