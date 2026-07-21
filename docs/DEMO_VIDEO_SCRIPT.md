# 🎬 Script de la vidéo démo — Xeer AI (OpenAI Build Week)

**Durée cible : 2 min 30 – 3 min max.** Devpost exige souvent une vidéo pour
l'éligibilité. Filme ton écran (Loom, OBS, ou l'enregistreur d'écran de ton
téléphone pour la partie mobile), voix off en français ou anglais.

> Astuce : lance l'app en mode démo (`XEER_DEMO_MODE=1`) pour une démo fluide,
> ou avec ta vraie clé OpenAI si tu veux montrer de vraies citations de pages.

---

## Plan (timecodes indicatifs)

### 0:00 – 0:20 — Accroche & problème
> « Le Xeer Ciise, c'est le droit coutumier de la communauté Ciise, transmis
> oralement depuis des générations. Il n'existe presque nulle part sous forme
> consultable. Anciens, étudiants, juristes et diaspora n'ont aucun moyen simple
> d'y accéder. Xeer AI résout ça. »

*À l'écran :* la landing page (`index.html`) — logo, titre, le sous-titre.

### 0:20 – 0:35 — Ce que c'est
> « Xeer AI est un assistant IA qui a numérisé ce corpus et le rend
> interrogeable en langage naturel, avec des réponses citées et vérifiables. »

*À l'écran :* scroll rapide de la landing (fonctionnalités + tarifs).

### 0:35 – 1:30 — Démo cœur : le chat (le plus important)
1. Se connecter / ouvrir `app.html`.
2. Poser une **vraie question**, ex. :
   > « Que dit le Xeer Ciise sur la réparation en cas de blessure ? »
3. Montrer la réponse structurée **et surtout la citation de page**.
   > Voix off : « Chaque réponse cite la page source — on peut vérifier, il n'y
   > a pas d'hallucination invérifiable. C'est là qu'intervient l'API OpenAI :
   > on récupère les passages pertinents du corpus (RAG) et le modèle rédige la
   > réponse en s'appuyant strictement sur ces extraits. »
4. **Changer de langue** (somali → arabe → français → anglais) et reposer une
   question, pour montrer le multilingue.
5. Cliquer 👍 sur une réponse.

### 1:30 – 1:55 — SaaS : quota & paiement
> « Xeer AI est un vrai produit : plan gratuit à 3 questions/mois, Premium
> illimité à 10 $, et offre Organisation sur devis. »

*À l'écran :* atteindre le quota → écran d'abonnement → payer en **mode sandbox**
(Waafi mobile money / Visa) → quota débloqué. Insiste sur *Waafi mobile money*,
adapté à Djibouti, la Somalie et la diaspora.

### 1:55 – 2:15 — Admin & mobile
- Ouvrir `admin.html` : KPIs, MRR, revenus, graphiques, gestion utilisateurs.
- Montrer l'**installation PWA** (bouton « Installer ») ou l'**APK Android**.

### 2:15 – 2:40 — Tech & clôture
> « Sous le capot : FastAPI, un pipeline OCR maison, ChromaDB pour la recherche
> sémantique, et l'API OpenAI pour la génération. Le tout de bout en bout : du
> PDF brut à une app installable. »
>
> « Xeer AI préserve un patrimoine juridique en danger et le rend accessible à
> tous, dans leur langue. Merci. »

*À l'écran :* logo Xeer AI + URL de la démo + lien GitHub.

---

## Checklist avant d'enregistrer
- [ ] App lancée et testée (démo ou clé réelle)
- [ ] Question préparée qui donne une belle réponse citée
- [ ] Micro correct, pas de bruit de fond
- [ ] Résolution 1080p, plein écran
- [ ] Vidéo **publique/non répertoriée** sur YouTube et lien collé dans Devpost
- [ ] Durée ≤ 3 min
