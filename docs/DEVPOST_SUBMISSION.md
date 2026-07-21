# Devpost submission — Xeer AI (OpenAI Build Week)

Ready-to-paste content for the Devpost form. French first (primary), English
below in case the jury is anglophone.

---

## 🇫🇷 Version française

**Project name**
```
Xeer AI
```

**Elevator pitch**
```
Assistant IA qui rend consultable le Xeer Ciise, le droit coutumier somali. Recherche sémantique (RAG) sur le corpus numérisé, réponses citées et vérifiables, en somali, arabe, français et anglais.
```

**Built with (tags)**
```
python, fastapi, openai, chromadb, sentence-transformers, sqlite, javascript, pwa, tesseract, pymupdf
```

*(Le texte complet « About the project » en français a été fourni dans le chat
et suit la même structure que la version anglaise ci-dessous.)*

---

## 🇬🇧 English version

**Project name**
```
Xeer AI
```

**Elevator pitch**
```
An AI assistant that makes the Xeer Ciise — Somali customary law — searchable. Semantic (RAG) search over the digitized corpus, with verifiable page-cited answers in Somali, Arabic, French and English.
```

**About the project**
```markdown
## 🌍 Inspiration
The **Xeer Ciise** is the customary law of the Ciise (Issa) community, passed
down orally for generations and scattered across documents that were almost
never digitized. Elders, students, lawyers and the diaspora had no simple way
to consult or understand it. We wanted to preserve this legal heritage and make
it accessible to everyone, in their own language.

## 🤖 What it does
Xeer AI is a full SaaS platform built around an AI assistant:
- **Semantic search (RAG)** over the digitized Xeer Ciise corpus
- **Structured answers with verifiable page citations** — every answer points
  back to its source, so there is no unverifiable hallucination
- **Multilingual**: Somali, Arabic, French, English
- **Conversation history** synced across devices
- **👍/👎 feedback** on every answer
- **Installable PWA** (web + Android APK)
- Accounts, subscriptions (Free / Premium $10 / Organization), payments
  (Waafi mobile money, CAC Bank, Visa/MasterCard) and an **admin dashboard**
  (KPIs, MRR, revenue, user management).

## 🛠️ How we built it
- **Digitization pipeline**: OCR of the book (PyMuPDF + Tesseract), cleaning,
  translation.
- **RAG engine**: corpus chunking, embeddings, indexing in **ChromaDB**, then
  answer generation through the **OpenAI API** with the retrieved passages as
  context and a strict instruction to cite pages.
- **Backend**: FastAPI (PBKDF2 auth + signed tokens, quotas, billing, admin),
  SQLite.
- **Frontend**: vanilla-JS PWA (landing, chat, admin), service worker,
  installable manifest + Android APK packaging.

## 🧗 Challenges we ran into
- Reliable OCR on old documents.
- Keeping answers **faithful to the source** and forcing page citations.
- Serving content correctly in 4 languages, including under-resourced Somali.
- Building a real SaaS layer (quotas, mobile-money payments) around the model.

## 🏆 Accomplishments we're proud of
- An **end-to-end** product: from raw PDF to an installable app that answers
  with verifiable citations.
- A full demo mode (`XEER_DEMO_MODE=1`) that runs the whole platform with no
  API key and no index.
- A concrete way to preserve endangered legal heritage.

## 📚 What we learned
- How to architect a citable, multilingual RAG system.
- How to integrate mobile-money payments suited to Djibouti / Somalia / the
  diaspora.

## 🚀 What's next
- Expand the corpus to other Somali Xeer traditions.
- Continuous improvement from user 👍/👎 feedback.
- Partnerships with institutions and universities.
```

**Built with (tags)**
```
python, fastapi, openai, chromadb, sentence-transformers, sqlite, javascript, pwa, tesseract, pymupdf
```

**Try it out (links)**
```
GitHub: https://github.com/abomed95/xeer-ai
Live demo: <colle l'URL Render une fois déployée>
```

---

## Checklist Devpost
- [ ] Project name, elevator pitch remplis
- [ ] « About the project » collé (FR ou EN)
- [ ] « Built with » : tags ajoutés
- [ ] Thumbnail : `docs/xeer-ai-cover.png` téléversée
- [ ] Gallery : captures d'écran de l'app — `docs/screenshots/01-landing.png`,
      `02-chat.png`, `03-admin.png`
- [ ] Try it out : lien GitHub + URL démo live
- [ ] Vidéo démo (voir `docs/DEMO_VIDEO_SCRIPT.md`) mise en ligne et liée
