# BET INTELLIGENCE AI — API-Football Edition

Application Streamlit de suivi des rencontres et d'estimations statistiques football.

## Fonctionnalités
- Chargement automatique des rencontres accessibles via API-Football.
- Requête groupée sur une période de 11 jours, avec cache de 15 minutes pour limiter la consommation du quota.
- Horaires convertis en heure du Cameroun (`Africa/Douala`).
- Recherche par équipe ou compétition et filtres par compétition/période.
- Cartes de matchs avec probabilités 1/N/2, score modal, Over/Under et BTTS.
- Historique local des pronostics et suivi des résultats.

## Configuration obligatoire de la clé API

Dans Streamlit Community Cloud :
1. Ouvrez votre application, puis **Manage app** → **Settings** → **Secrets**.
2. Ajoutez exactement cette ligne (remplacez la valeur par votre clé privée) :

```toml
API_FOOTBALL_KEY = "VOTRE_CLE_API"
```

3. Enregistrez les secrets puis redémarrez l'application.

En local, créez `.streamlit/secrets.toml` avec la même ligne, ou définissez la variable d'environnement `API_FOOTBALL_KEY`.

**Ne placez jamais la clé dans `app.py`, dans GitHub, dans un CSV ou dans une capture d'écran.** Le fichier `secrets.toml` est ignoré par Git.

## Installation locale
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Déploiement gratuit
1. Décompressez le dossier `BET_INTELLIGENCE_AI`.
2. Envoyez son contenu dans votre dépôt GitHub.
3. Sur Streamlit Community Cloud, déployez le dépôt avec `app.py` comme fichier principal.
4. Configurez le secret `API_FOOTBALL_KEY` comme indiqué ci-dessus.

## Quota et couverture
Le chargement des rencontres utilise une requête API-Football pour la période demandée et un cache de 15 minutes. L'actualisation manuelle peut consommer une nouvelle requête. La disponibilité des compétitions et des rencontres dépend de la couverture de votre forfait API-Football et du calendrier publié par le fournisseur.

## Modèle et limites
Les probabilités utilisent Poisson avec ajustement Dixon–Coles. Sans historique de résultats vérifié, le modèle utilise des paramètres de départ génériques : les probabilités ne sont donc pas spécifiques aux équipes. Ce ne sont pas des garanties de gain. Les blessures, compositions, suspensions et mouvements de cotes ne sont pas automatiquement intégrés.
