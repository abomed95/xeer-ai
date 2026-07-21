# Sauvegarde de la configuration du modèle

Pour l'**OpenAI Build Week**, le produit est aligné sur **GPT-5.6**
(`OPENAI_MODEL=gpt-5.6`), afin de correspondre à la session Codex et au
formulaire de soumission.

## Revenir à la configuration précédente (GPT-5.5) après la sélection du jury

La configuration modèle d'avant est sauvegardée dans la branche Git
**`backup/model-gpt-5.5`** (état du commit `b2427bd`).

Deux façons de revenir à GPT-5.5 :

1. **Le plus simple (sans toucher au code)** — définir la variable
   d'environnement :
   ```
   OPENAI_MODEL=gpt-5.5
   ```

2. **Restaurer l'état exact** depuis la branche de sauvegarde :
   ```bash
   git fetch origin backup/model-gpt-5.5
   git show origin/backup/model-gpt-5.5:app/config.py   # voir l'ancienne valeur
   # ou récupérer les fichiers précis :
   git checkout origin/backup/model-gpt-5.5 -- app/config.py .env.example
   ```

> Rappel : le modèle est piloté par `OPENAI_MODEL` (voir `app/config.py`) ;
> la valeur par défaut du code peut donc toujours être surchargée par
> l'environnement, sans modifier le code.
