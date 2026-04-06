# Xeer AI Premium

AI-powered legal-cultural assistant for exploring **Xeer Ciise**, the Somali customary law tradition.

## Overview

Xeer AI Premium is a multilingual AI assistant designed to preserve, explore, and explain Somali customary law through:

- semantic search
- verified source retrieval
- conversation memory
- OpenAI-powered structured answers
- premium web interface

The system is built on a digitized Xeer Ciise corpus and combines RAG, memory, and a modern chat experience.

## Main Features

- **Semantic search on Xeer corpus**
- **Structured answers with page citations**
- **Conversation memory by session**
- **Somali / French / English support**
- **FastAPI backend**
- **Streamlit premium frontend**
- **Landing page for presentation/demo**

## Tech Stack

- Python
- FastAPI
- Streamlit
- ChromaDB
- Sentence Transformers
- OpenAI API
- OCR pipeline with PyMuPDF + Tesseract

## Project Structure

```bash
xeer-ai/
├── app/                      # FastAPI backend
│   ├── __init__.py
│   └── main.py
├── frontend/                 # Frontend files
│   ├── streamlit_app.py
│   └── landing.html
├── scripts/                  # OCR, cleaning, translation, vector build
├── data/                     # Raw and processed data
├── requirements.txt
├── .gitignore
└── README.md
