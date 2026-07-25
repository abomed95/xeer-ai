# Déployer Xeer AI en production sur DigitalOcean

Procédure complète pour une plateforme qui encaisse de vrais clients :
IA réelle (OpenAI), corpus indexé, et **données persistantes**.

> ⚠️ **À lire d'abord.** App Platform applique la spec **stockée chez
> DigitalOcean**, pas le fichier `.do/app.yaml` du dépôt. Un `git push` redéploie
> le *code* mais **ne modifie pas** la configuration (base de données, commande
> de build, variables). Il faut donc appliquer la spec une fois, par l'une des
> deux méthodes ci-dessous.

---

## Méthode A — en ligne de commande (recommandée)

Nécessite [`doctl`](https://docs.digitalocean.com/reference/doctl/how-to/install/)
authentifié (`doctl auth init`).

```bash
# 1. Récupère l'ID de ton app existante
doctl apps list

# 2. Applique la spec de production (crée la base PostgreSQL managée,
#    passe en mode complet, construit l'index au build)
doctl apps update <APP_ID> --spec .do/app.yaml

# 3. Ajoute les deux secrets (jamais committés dans le dépôt)
doctl apps update <APP_ID> \
  --spec .do/app.yaml \
  --env "OPENAI_API_KEY=sk-..." \
  --env "XEER_SECRET_KEY=$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
```

Si tu n'as pas encore d'app :

```bash
doctl apps create --spec .do/app.yaml
```

## Méthode B — par le dashboard

1. **Base de données** : ton app → **Create** → **Database** → PostgreSQL 16.
   Nomme-la `db`. DigitalOcean injecte alors `DATABASE_URL` automatiquement.
2. **Settings → Components → web → Build Command** :
   ```bash
   pip install --upgrade pip
   pip install torch --index-url https://download.pytorch.org/whl/cpu
   pip install -r requirements.txt
   python scripts/build_vector_store.py
   ```
3. **Settings → Components → web → Instance Size** : `basic-s` (2 Go).
   512 Mo ne suffisent pas à charger le modèle d'embeddings.
4. **Settings → App-Level Environment Variables** :

   | Variable | Valeur | Chiffré |
   |---|---|---|
   | `OPENAI_API_KEY` | `sk-...` | ✅ **Encrypt** |
   | `XEER_SECRET_KEY` | chaîne aléatoire longue (voir ci-dessous) | ✅ **Encrypt** |
   | `XEER_DEMO_MODE` | `0` | — |
   | `OPENAI_MODEL` | `gpt-4o-mini` | — |

   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(48))"
   ```
5. **Save** → DigitalOcean redéploie.

---

## Vérifier que tout fonctionne

```bash
curl https://<ton-app>.ondigitalocean.app/api/health
```

Réponse attendue en production :

```json
{
  "status": "ok",
  "demo_mode": false,
  "openai_key_set": true,
  "rag_ready": true,
  "database": "postgresql",
  "persistent_storage": true
}
```

| Champ | Ce qu'il signifie s'il est faux |
|---|---|
| `demo_mode: true` | Clé OpenAI absente → réponses simulées |
| `rag_ready: false` | Index vectoriel non construit → vérifie le build command |
| `persistent_storage: false` | Pas de base managée → **données perdues au redéploiement** |

## Premier accès administrateur

`XEER_ADMIN_PASSWORD` n'est volontairement pas défini : au premier démarrage,
un mot de passe aléatoire est généré et affiché dans les **Runtime Logs** :

```
[Xeer AI] Compte admin créé : admin@xeer.ai / <mot-de-passe-généré>
```

Récupère-le, connecte-toi sur `/admin.html`, puis change-le depuis l'interface.

## Garde-fous automatiques

L'API **refuse de démarrer** en production si :

- `XEER_SECRET_KEY` a sa valeur par défaut ou fait moins de 32 caractères —
  sinon n'importe qui pourrait forger un jeton d'administrateur ;
- `XEER_ADMIN_PASSWORD` vaut le mot de passe de démonstration, connu
  publiquement.

Elle **avertit** dans les logs (sans bloquer) si les données ne sont pas
persistantes ou si les paiements sont encore en mode `sandbox`.

## Encaisser de vrais paiements

Les paiements sont simulés par défaut (`XEER_PAYMENTS_MODE=sandbox`). Pour
encaisser réellement, passe `XEER_PAYMENTS_MODE=live` et renseigne, en variables
chiffrées, les identifiants du ou des fournisseurs utilisés :

- **WaafiPay** : `WAAFI_MERCHANT_UID`, `WAAFI_API_USER_ID`, `WAAFI_API_KEY`
- **CAC Bank** : `CACBANK_API_URL`, `CACBANK_MERCHANT_ID`, `CACBANK_API_KEY`
- **Visa / MasterCard** : `CARD_GATEWAY_SECRET_KEY`

Teste chaque moyen de paiement avec un petit montant réel avant l'ouverture
commerciale.

## Coût indicatif

| Poste | Configuration | Ordre de grandeur |
|---|---|---|
| Service web | `basic-s` (2 Go) | ~25 $/mois |
| Base PostgreSQL | base de dev (`production: false`) | ~7 $/mois |
| API OpenAI | `gpt-4o-mini`, à l'usage | quelques $/mois au démarrage |

Vérifie les tarifs à jour dans le dashboard DigitalOcean : ils évoluent.
