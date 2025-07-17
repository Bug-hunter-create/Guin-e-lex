import os
import json
import re
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Configuration logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Dossiers par défaut
DOSSIER_TXTS = os.path.join(os.path.dirname(__file__), '..', 'scraping', 'textes_extraits')
DOSSIER_JSONS = os.path.join(os.path.dirname(__file__), '..', 'scraping', 'documents_structures_3')

def clean_text(text: str) -> str:
    text = re.sub(r'^FICHIER SOURCE:.*?\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^DATE D\'EXTRACTION:.*?\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^TAILLE DU FICHIER PDF:.*?\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'^=+\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'--- PAGE \d+ ---', '', text)
    return re.sub(r'\s+', ' ', text).strip()

def segmenter_articles(text: str) -> List[Dict[str, str]]:
    pattern = r'(ARTICLE\s+\d+[A-Z]?)\s*[:-]?\s*(.*?)(?=ARTICLE\s+\d+[A-Z]?[:\-]|\Z)'
    matches = re.finditer(pattern, text, re.IGNORECASE | re.DOTALL)
    articles = []
    for match in matches:
        numero = match.group(1).strip()
        contenu = match.group(2).strip().replace('\n', ' ')
        articles.append({
            "numero": numero,
            "titre": numero.title(),
            "contenu": contenu
        })
    return articles

def extraire_resume(text: str, max_phrases: int = 2) -> str:
    phrases = re.split(r'(?<=[.!?])\s+', text)
    resume = " ".join(phrases[:max_phrases])
    return resume.strip()

def infer_type_from_filename(filename: str) -> str:
    nom = filename.lower()
    for t in ['loi', 'decret', 'arrete', 'ordonnance', 'instruction']:
        if t in nom:
            return t
    return 'inconnu'

def extract_date(text: str) -> Optional[str]:
    match = re.search(r'(\d{1,2} [a-zA-Zéû]+ \d{4})', text)
    return match.group(1) if match else None

def generer_id(titre: str, doc_type: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', titre.lower())
    slug = re.sub(r'-+', '-', slug).strip('-')
    return f"{doc_type}-{slug[:40]}"

class TextStructurer:
    def __init__(self, txt_folder=DOSSIER_TXTS, json_folder=DOSSIER_JSONS):
        self.txt_folder = txt_folder
        self.json_folder = json_folder
        os.makedirs(self.json_folder, exist_ok=True)

    def get_txt_files(self) -> List[str]:
        return [os.path.join(self.txt_folder, f) for f in os.listdir(self.txt_folder)
                if f.lower().endswith('.txt') and not f.startswith(('index_', 'metadata_'))]

    def structure_document(self, txt_path: str) -> Optional[Dict]:
        try:
            with open(txt_path, 'r', encoding='utf-8') as f:
                raw_text = f.read()

            if not raw_text.strip():
                return None

            content = clean_text(raw_text)
            articles = segmenter_articles(content)
            resume = extraire_resume(content)

            titre_fichier = os.path.basename(txt_path).replace('.txt', '').replace('_', ' ').title()
            doc_type = infer_type_from_filename(titre_fichier)
            date = extract_date(content)

            document = {
                "id": generer_id(titre_fichier, doc_type),
                "type": doc_type,
                "titre": titre_fichier,
                "resume": resume,
                "date": date,
                "nb_articles": len(articles),
                "articles": articles,
                "metadata": {
                    "source": os.path.basename(txt_path),
                    "taille_contenu": len(content),
                    "date_structuration": datetime.now().isoformat()
                }
            }

            return document

        except Exception as e:
            logger.error(f"Erreur lors du traitement de {txt_path}: {e}")
            return None

    def save_json(self, doc: Dict):
        path = os.path.join(self.json_folder, f"{doc['id']}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(doc, f, indent=2, ensure_ascii=False)
        logger.info(f"Document sauvegardé : {doc['id']}")

    def process_all_texts(self):
        logger.info("Début de la structuration des documents...")
        fichiers = self.get_txt_files()
        for txt in fichiers:
            doc = self.structure_document(txt)
            if doc:
                self.save_json(doc)

if __name__ == "__main__":
    structurer = TextStructurer()
    structurer.process_all_texts()
