# Xeer AI — Application Android (APK)

Xeer AI est une **PWA** (Progressive Web App) : le fichier
`frontend/manifest.webmanifest` et le service worker `frontend/sw.js` rendent
l'application installable depuis le navigateur, et permettent de générer un
**APK Android** sans réécrire l'application.

## Option 1 — PWABuilder (le plus simple, sans code)

1. Déployez le site en HTTPS (ex. `https://xeer.ai`).
2. Allez sur <https://www.pwabuilder.com>, entrez l'URL du site.
3. PWABuilder lit le manifest et génère un paquet **Android (APK / AAB)**
   prêt pour le Google Play Store ou la distribution directe.
4. Téléchargez l'APK et publiez-le (Play Store ou page de téléchargement).

## Option 2 — Bubblewrap (ligne de commande, TWA officielle Google)

```bash
npm install -g @bubblewrap/cli
bubblewrap init --manifest https://xeer.ai/manifest.webmanifest
bubblewrap build          # produit app-release-signed.apk
```

Bubblewrap crée une **Trusted Web Activity** : l'APK ouvre l'application web
en plein écran, avec l'icône et l'écran de démarrage définis dans le manifest.

> **Domaine vérifié** : ajoutez le fichier `assetlinks.json` généré par
> Bubblewrap dans `frontend/.well-known/` pour que l'APK s'ouvre sans barre
> d'adresse.

## Option 3 — Capacitor (si des API natives deviennent nécessaires)

Si un jour l'application a besoin d'API natives (notifications push locales,
biométrie…), encapsulez le frontend avec [Capacitor](https://capacitorjs.com) :

```bash
npm init @capacitor/app
npx cap add android
npx cap open android    # build APK depuis Android Studio
```

## Icônes

Les icônes vectorielles sont dans `frontend/assets/icon.svg` et
`icon-maskable.svg`. PWABuilder/Bubblewrap génèrent automatiquement les PNG
aux bonnes tailles à partir du manifest ; si un outil exige des PNG, exportez
le SVG en 192×192 et 512×512 (par ex. avec Inkscape ou https://svgtopng.com).
