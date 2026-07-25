# Xeer AI

![Xeer AI](docs/xeer-ai-cover.png)

Assistant IA du **Xeer Ciise** (droit coutumier somali) — plateforme SaaS
complète : application web moderne (PWA installable + APK Android), comptes
utilisateurs, abonnements, paiements et tableau de bord administrateur.

## Déploiement en ligne

### DigitalOcean App Platform — **production**

[Déployer sur DigitalOcean](https://cloud.digitalocean.com/apps/new?repo=https://github.com/abomed95/xeer-ai/tree/main)
(spec : [`.do/app.yaml`](.do/app.yaml) · **procédure détaillée :
[`docs/DEPLOY_DIGITALOCEAN.md`](docs/DEPLOY_DIGITALOCEAN.md)**)

La spec déploie la plateforme en conditions réelles :

- **IA réelle** — génération OpenAI, `XEER_DEMO_MODE=0` ;
- **index vectoriel construit au build** depuis `data/pages/clean` (131 pages) ;
- **base PostgreSQL managée** — comptes, paiements et historiques survivent aux
  redéploiements (le disque d'App Platform est éphémère).

Deux secrets à créer dans le dashboard (jamais committés) : `OPENAI_API_KEY` et
`XEER_SECRET_KEY`. Vérifie ensuite **`/api/health`** :

```json
{ "demo_mode": false, "openai_key_set": true, "rag_ready": true,
  "database": "postgresql", "persistent_storage": true }
```

> App Platform applique la spec **stockée chez DigitalOcean**, pas le fichier du
> dépôt : un `git push` met à jour le code mais pas la configuration. Applique la
> spec une fois via `doctl apps update <APP_ID> --spec .do/app.yaml` (ou par le
> dashboard) — voir [`docs/DEPLOY_DIGITALOCEAN.md`](docs/DEPLOY_DIGITALOCEAN.md).

**Sécurité au démarrage** : l'API refuse de démarrer en production si
`XEER_SECRET_KEY` garde sa valeur par défaut (jetons admin forgeables) ou si le
mot de passe admin est celui de la démo. Sans clé OpenAI valide, elle ne plante
pas : elle retombe en réponses de démonstration.

### Render — **mode démo** (aucune clé requise)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)
(spec : [`render.yaml`](render.yaml)). Colle l'URL du dépôt sur
https://render.com/deploy. Lance toute la plateforme (comptes, quotas, paiements
sandbox, admin) sans clé ni index vectoriel, via le build léger
[`requirements-demo.txt`](requirements-demo.txt).

> Le déploiement Render reste en SQLite éphémère : c'est une vitrine, pas une
> production. Pour de vrais clients, utilise la spec DigitalOcean ci-dessus
> (PostgreSQL managé).

## Utilisation de Codex & GPT-4o (OpenAI Build Week)

<!-- NOTE ÉQUIPE : adaptez le paragraphe « Codex » à ce que vous avez réellement fait. -->

**Le modèle OpenAI — le cœur du produit.** Le moteur de réponses de Xeer AI
s'appuie sur l'API OpenAI. Utilisez un **modèle réel** via `OPENAI_MODEL`
(défaut : `gpt-4o-mini` ; `gpt-4o` pour une qualité supérieure). Dans le pipeline
RAG, les passages les plus pertinents du corpus numérisé du Xeer Ciise sont
récupérés (ChromaDB) puis fournis au modèle avec une consigne stricte : s'appuyer
uniquement sur ces extraits et citer les pages sources. D'où des réponses
multilingues (somali, arabe, français, anglais), structurées et **vérifiables**.
Voir [`app/services/rag.py`](app/services/rag.py).

> ⚠️ `OPENAI_MODEL` doit désigner un modèle **existant** côté OpenAI. Une valeur
> fictive (ex. `gpt-5.6`) fait échouer l'API avec « model not found ».

**Codex — assistant de développement.** Nous avons utilisé **Codex** (l'agent de
code d'OpenAI) pour concevoir et itérer sur le projet : backend FastAPI (auth,
quotas, billing, admin), moteur RAG, pipeline OCR et frontend PWA.

## Aperçu

| Landing | Chat (réponse citée) | Admin |
|---|---|---|
| ![Landing](docs/screenshots/01-landing.png) | ![Chat](docs/screenshots/02-chat.png) | ![Admin](docs/screenshots/03-admin.png) |

## Fonctionnalités

### Produit
- **Recherche sémantique** sur le corpus numérisé du Xeer Ciise (RAG)
- **Réponses structurées** avec citations de pages vérifiables
- **Historique de conversations** persisté en base, synchronisé sur tous les appareils
- **Feedback client** (👍/👎) sur chaque réponse, suivi dans l'admin
- **Multilingue** : somali, arabe, français, anglais
- **PWA installable** (web + mobile) et packaging **APK Android** (voir `docs/MOBILE_APK.md`)

### Abonnements
| Plan | Prix | Quota |
|------|------|-------|
| **Gratuit** | 0 $ | 3 questions / mois |
| **Premium** | **10 $ / mois** | Illimité |
| **Organisation** | Prix négociable (sur devis) | Personnalisé / illimité |

### Paiements
- **Waafi** (mobile money — Djibouti, Somalie, diaspora)
- **CAC Bank** (CAC Pay)
- **Visa** et **MasterCard** (passerelle carte bancaire)

Mode `sandbox` par défaut (paiements simulés de bout en bout) ; passez
`XEER_PAYMENTS_MODE=live` avec vos identifiants marchands pour la production.

### Administration (`/admin.html`)
- KPIs : utilisateurs, abonnés Premium, MRR, questions, revenus
- Graphiques 30 jours (questions posées, revenus encaissés)
- Gestion des utilisateurs et de leurs plans (dont quotas négociés)
- Suivi des paiements et des demandes de devis Organisation

## Démarrage rapide

```bash
pip install -r requirements.txt
cp .env.example .env          # renseignez OPENAI_API_KEY, XEER_SECRET_KEY…

# 1. Construire l'index vectoriel (une fois)
python scripts/build_vector_store.py

# 2. Lancer le serveur (API + frontend)
uvicorn app.main:app --reload
```

- Application : http://localhost:8000
- Chat : http://localhost:8000/app.html
- Admin : http://localhost:8000/admin.html (identifiants affichés au premier démarrage,
  ou définis via `XEER_ADMIN_EMAIL` / `XEER_ADMIN_PASSWORD`)
- Docs API : http://localhost:8000/docs

> **Mode démo** : `XEER_DEMO_MODE=1` permet de tester toute la plateforme
> (comptes, quotas, paiements sandbox, admin) sans clé OpenAI ni index vectoriel.

## Architecture

```bash
xeer-ai/
├── app/                      # Backend FastAPI
│   ├── main.py               # App, admin seed, statiques
│   ├── config.py             # Configuration (env)
│   ├── database.py           # SQLite (users, paiements, usage, leads)
│   ├── security.py           # PBKDF2 + jetons signés
│   ├── deps.py               # Auth / rôle admin
│   ├── routers/              # auth, chat, billing, admin
│   └── services/
│       ├── rag.py             # Moteur RAG (Chroma + OpenAI)
│       ├── accounts.py        # Plans, quotas, usage
│       └── payments/          # waafi, cacbank, card (Visa/MasterCard)
├── frontend/                 # Web (PWA)
│   ├── index.html             # Landing + tarifs + devis organisations
│   ├── app.html               # Chat (auth, quota, paiement intégré)
│   ├── admin.html             # Tableau de bord administrateur
│   ├── manifest.webmanifest   # PWA / APK
│   ├── sw.js                  # Service worker
│   └── assets/                # CSS, JS, icônes
├── scripts/                  # OCR, nettoyage, traduction, index vectoriel
├── data/                     # Corpus brut et nettoyé
└── docs/MOBILE_APK.md        # Générer l'APK Android
```

## Tech stack

Python · FastAPI · SQLite · ChromaDB · Sentence Transformers ·
OpenAI API (**GPT-4o**) · PWA (vanilla JS) · OCR PyMuPDF + Tesseract
