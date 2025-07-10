# 🗓️ Plan de travail – Projet GuinéeLex (Scraping & Structuration des données)

## 📍 Période : JEUDI – Samedi jours de travail en duo

## 🎯 Objectif principal :
Constituer un dataset complet, propre et structuré des textes juridiques officiels de la Guinée (2020–2025), à partir des sites du SGG et du Journal Officiel.

---

## 🧠 Répartition de l’équipe

| Prénom        | Rôle                               |
|---------------|------------------------------------|
| Foula         | Dev Web & Mobile – scraping, structuration JSON, base |
| Mariame | Dev IA – scraping, traitement du texte, préparation IA |

---

## 📦 Contenus à scraper

- 📘 Lois (https://sgg.gov.gn/document/lois/{id})
- 📄 Décrets
- 📑 Arrêtés
- 📚 Journaux Officiels (https://journal-officiel.sgg.gov.gn/JO/2025/...)

---

## 📂 Structure de travail recommandée

GuineeLex/
├── scraping/
│ ├── pdfs_originaux/
│ ├── textes_bruts/
│ ├── nettoyés/
│ └── json_structurés/
├── scripts/
├── data/
└── ai/

yaml
Copy
Edit



## 🗓️ Planning détaillé sur 4 jours

### 🔹 Jeudi – Recensement & téléchargement

- Lister les documents à récupérer (lois, JO, etc.)
- Répartir les plages d’URL à parcourir (ex: lois/1 à 200 pour Foula, 201 à 400 pour [Nom])
- Lancer le téléchargement automatique (ou semi-auto) des fichiers PDF
- Nommer et ranger les fichiers dans `pdfs_originaux/`

✅ Résultat : dossier `pdfs_originaux/` rempli et bien structuré.

---

### 🔹 Vendredi – Extraction du texte brut

- Extraire le texte de chaque PDF avec `PyMuPDF` ou `Tesseract`
- Supprimer les entêtes/pages inutiles
- Stocker chaque version brute dans `textes_bruts/`

✅ Résultat : dossier `textes_bruts/` rempli de fichiers `.txt` lisibles.

---

### 🔹 Samedi – Structuration des textes

- Analyser chaque fichier pour identifier les titres des textes (Loi, Décret, etc.)
- Découper et organiser chaque texte en format JSON :
```json
{
  "type": "Loi",
  "titre": "...",
  "date": "...",
  "numero": "...",
  "contenu": "..."
}
Regrouper les fichiers JSON dans json_structurés/

Générer un fichier global dataset_juridique.json

✅ Résultat : JSON propre et prêt à être utilisé côté app et IA.

🔹 Jour 4 – Validation & enrichissement
Vérification manuelle de l’exactitude des textes extraits

Ajout de champs comme résumé, thème, mots-clés, etc. (optionnel)

Préparer les fichiers d’entrée pour les modèles IA

✅ Résultat : dataset validé, enrichi et prêt pour l’application.

📌 Suivi de progression
Tâche	                           Foula Mariame  	             Statut                             	
Récupération des URLs / IDs lois	✅	✅	                 En cours
Téléchargement des PDF	            ✅	✅	                  À faire
Extraction du texte brut			                            À faire
Structuration JSON			                                    À faire
Nettoyage final			                                        À faire

🧠 Notes importantes
Le scraping doit rester respectueux (éviter de spammer le serveur)

Ne jamais pousser de PDF lourd ou .env dans le repo Git

Utiliser README.md pour documenter chaque étape ou dossier

Se synchroniser quotidiennement sur les points de blocage