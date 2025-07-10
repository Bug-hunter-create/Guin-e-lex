# 🇬🇳 GuinéeLex – Accès simplifié au droit guinéen

**GuinéeLex** est une application web et mobile open source qui permet aux citoyens, étudiants, juristes et institutions d’accéder facilement aux textes juridiques officiels de la République de Guinée : lois, décrets, arrêtés, codes, etc.

Le projet vise à centraliser, structurer, et vulgariser l’ensemble de la documentation juridique publique, avec l’aide de l’intelligence artificielle.

---

## 🧠 Objectifs

- Centraliser les textes juridiques guinéens (JO, lois, décrets…)
- Offrir une recherche intuitive et filtrable par thème, type, date
- Fournir des résumés automatiques et explications simplifiées grâce à l’IA
- Mettre à disposition une API IA consultable via un chatbot intelligent
- Rendre le droit accessible à tous, gratuitement

---

## 👥 Équipe

- **Foula** — Développeur Web & Mobile (scraping, structuration, interface Flutter/Web, base de données)
- **Mariame Baldé** — Développeuse IA (résumé automatique, NLP, chatbot, API IA)

---

## 📂 Arborescence du projet
GuineeLex/
├── scraping/
├── scripts/
├── data/
├── web/
├── mobile/
├── ai/
├── .gitignore
├── LICENSE
├── README.md
├── requirements.txt
└── plan_de_travail.md

---

## ⚙️ Technologies utilisées

- Python (requests, BeautifulSoup, PyMuPDF, Tesseract, etc.)
- Flutter (mobile)
- Next.js (web)
- Supabase ou Firebase (backend)
- FastAPI ou Flask (API IA)
- Modèles LLM (résumé, classification, NLP)


## 📦 Dataset

Les textes juridiques sont collectés à partir du [Journal Officiel guinéen](https://journal-officiel.sgg.gov.gn/) et du [site du Secrétariat Général du Gouvernement](https://sgg.gov.gn/), puis structurés en fichiers JSON exploitables par l'application et les modèles IA.

---

## 🚀 Lancement du projet (scraping & structuration)

```bash
git clone https://github.com/Bug-hunter-create/Guin-lex.git
cd GuineeLex
pip install -r requirements.txt
python scripts/telechargement.py
python scripts/extraction.py
python scripts/structuration.py

 Licence
Ce projet est sous licence MIT 
Consulte le fichier LICENSE pour plus de détaillé
