import os
import logging
from datetime import datetime
import PyPDF2
import pdfplumber
from pathlib import Path
import json
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration des dossiers
DOSSIER_PDFS = os.path.join(os.path.dirname(__file__), '..', 'scraping', 'pdfs_originaux')
DOSSIER_TXTS = os.path.join(os.path.dirname(__file__), '..', 'scraping', 'textes_extraits')

class PDFExtractor:
    def __init__(self, pdf_folder=None, txt_folder=None):
        self.pdf_folder = pdf_folder or DOSSIER_PDFS
        self.txt_folder = txt_folder or DOSSIER_TXTS
        
        # Créer le dossier de destination s'il n'existe pas
        os.makedirs(self.txt_folder, exist_ok=True)
        
        logger.info(f"Dossier source PDFs: {os.path.abspath(self.pdf_folder)}")
        logger.info(f"Dossier destination TXTs: {os.path.abspath(self.txt_folder)}")
    
    def get_pdf_files(self):
        """Récupère la liste de tous les fichiers PDF dans le dossier"""
        if not os.path.exists(self.pdf_folder):
            logger.error(f"Le dossier {self.pdf_folder} n'existe pas")
            return []
        
        pdf_files = []
        for filename in os.listdir(self.pdf_folder):
            if filename.lower().endswith('.pdf'):
                pdf_path = os.path.join(self.pdf_folder, filename)
                pdf_files.append(pdf_path)
        
        logger.info(f"Trouvé {len(pdf_files)} fichiers PDF")
        return sorted(pdf_files)
    
    def extract_text_pypdf2(self, pdf_path):
        """Extrait le texte d'un PDF avec PyPDF2"""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text += f"\n--- PAGE {page_num + 1} ---\n"
                    text += page.extract_text()
                
                return text
        except Exception as e:
            logger.error(f"Erreur PyPDF2 pour {pdf_path}: {e}")
            return None
    
    def extract_text_pdfplumber(self, pdf_path):
        """Extrait le texte d'un PDF avec pdfplumber (plus précis)"""
        try:
            with pdfplumber.open(pdf_path) as pdf:
                text = ""
                
                for page_num, page in enumerate(pdf.pages):
                    text += f"\n--- PAGE {page_num + 1} ---\n"
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text
                    else:
                        text += "[Texte non extractible sur cette page]"
                
                return text
        except Exception as e:
            logger.error(f"Erreur pdfplumber pour {pdf_path}: {e}")
            return None
    
    def clean_text(self, text):
        """Nettoie le texte extrait"""
        if not text:
            return ""
        
        # Supprimer les espaces multiples
        text = re.sub(r'\s+', ' ', text)
        
        # Supprimer les lignes vides multiples
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Nettoyer les caractères spéciaux
        text = text.replace('\x00', '')
        
        return text.strip()
    
    def extract_pdf_to_txt(self, pdf_path):
        """Extrait un PDF vers un fichier TXT"""
        filename = os.path.basename(pdf_path)
        txt_filename = os.path.splitext(filename)[0] + '.txt'
        txt_path = os.path.join(self.txt_folder, txt_filename)
        
        # Vérifier si le fichier TXT existe déjà
        if os.path.exists(txt_path):
            logger.info(f"Fichier TXT déjà existant: {txt_filename}")
            return True, txt_path
        
        logger.info(f"Extraction: {filename}")
        
        # Essayer d'abord avec pdfplumber (plus précis)
        text = self.extract_text_pdfplumber(pdf_path)
        
        # Si pdfplumber échoue, essayer PyPDF2
        if not text:
            logger.warning(f"pdfplumber a échoué pour {filename}, essai avec PyPDF2")
            text = self.extract_text_pypdf2(pdf_path)
        
        if not text:
            logger.error(f"Impossible d'extraire le texte de {filename}")
            return False, None
        
        # Nettoyer le texte
        text = self.clean_text(text)
        
        # Sauvegarder dans un fichier TXT
        try:
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(f"FICHIER SOURCE: {filename}\n")
                f.write(f"DATE D'EXTRACTION: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"TAILLE DU FICHIER PDF: {os.path.getsize(pdf_path):,} bytes\n")
                f.write("="*80 + "\n\n")
                f.write(text)
            
            txt_size = os.path.getsize(txt_path)
            logger.info(f"Extrait avec succès: {txt_filename} ({txt_size:,} bytes)")
            return True, txt_path
            
        except Exception as e:
            logger.error(f"Erreur lors de la sauvegarde de {txt_filename}: {e}")
            return False, None
    
    def extract_all_pdfs(self):
        """Extrait tous les PDFs en fichiers TXT"""
        logger.info("Début de l'extraction des PDFs...")
        
        pdf_files = self.get_pdf_files()
        if not pdf_files:
            logger.warning("Aucun fichier PDF trouvé")
            return []
        
        results = []
        successful_extractions = 0
        failed_extractions = 0
        
        for i, pdf_path in enumerate(pdf_files, 1):
            logger.info(f"Traitement {i}/{len(pdf_files)}: {os.path.basename(pdf_path)}")
            
            success, txt_path = self.extract_pdf_to_txt(pdf_path)
            
            result = {
                'pdf_file': os.path.basename(pdf_path),
                'pdf_path': pdf_path,
                'txt_file': os.path.basename(txt_path) if txt_path else None,
                'txt_path': txt_path,
                'success': success,
                'pdf_size': os.path.getsize(pdf_path),
                'txt_size': os.path.getsize(txt_path) if txt_path and os.path.exists(txt_path) else 0
            }
            
            results.append(result)
            
            if success:
                successful_extractions += 1
            else:
                failed_extractions += 1
        
        logger.info(f"Extraction terminée:")
        logger.info(f"  - Succès: {successful_extractions}")
        logger.info(f"  - Échecs: {failed_extractions}")
        logger.info(f"  - Total: {len(pdf_files)}")
        
        return results
    
    def create_index_file(self, results):
        """Crée un fichier index avec la liste de tous les textes extraits"""
        index_path = os.path.join(self.txt_folder, 'index_extractions.txt')
        
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write("INDEX DES EXTRACTIONS - JOURNAUX OFFICIELS DE GUINÉE\n")
            f.write("="*60 + "\n")
            f.write(f"Date de création: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre total de PDFs traités: {len(results)}\n")
            
            successful = [r for r in results if r['success']]
            failed = [r for r in results if not r['success']]
            
            f.write(f"Extractions réussies: {len(successful)}\n")
            f.write(f"Extractions échouées: {len(failed)}\n")
            
            if successful:
                total_pdf_size = sum(r['pdf_size'] for r in successful)
                total_txt_size = sum(r['txt_size'] for r in successful)
                f.write(f"Taille totale PDFs: {total_pdf_size:,} bytes ({total_pdf_size/1024/1024:.1f} MB)\n")
                f.write(f"Taille totale TXTs: {total_txt_size:,} bytes ({total_txt_size/1024/1024:.1f} MB)\n")
            
            f.write("="*60 + "\n\n")
            
            f.write("FICHIERS EXTRAITS AVEC SUCCÈS:\n")
            f.write("-" * 40 + "\n")
            for result in successful:
                f.write(f"• {result['pdf_file']}\n")
                f.write(f"  → {result['txt_file']}\n")
                f.write(f"  PDF: {result['pdf_size']:,} bytes | TXT: {result['txt_size']:,} bytes\n\n")
            
            if failed:
                f.write("FICHIERS ÉCHOUÉS:\n")
                f.write("-" * 40 + "\n")
                for result in failed:
                    f.write(f"• {result['pdf_file']}\n")
                    f.write(f"  Taille: {result['pdf_size']:,} bytes\n\n")
        
        logger.info(f"Fichier index créé: {index_path}")
        return index_path
    
    def create_json_metadata(self, results):
        """Crée un fichier JSON avec les métadonnées pour faciliter la structuration future"""
        json_path = os.path.join(self.txt_folder, 'metadata_extractions.json')
        
        metadata = {
            'extraction_date': datetime.now().isoformat(),
            'total_files': len(results),
            'successful_extractions': len([r for r in results if r['success']]),
            'failed_extractions': len([r for r in results if not r['success']]),
            'pdf_folder': os.path.abspath(self.pdf_folder),
            'txt_folder': os.path.abspath(self.txt_folder),
            'files': results
        }
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Métadonnées JSON créées: {json_path}")
        return json_path
    
    def create_report(self, results):
        """Crée un rapport final"""
        successful = [r for r in results if r['success']]
        failed = [r for r in results if not r['success']]
        
        print(f"\n{'='*60}")
        print("RAPPORT D'EXTRACTION - JOURNAUX OFFICIELS DE GUINÉE")
        print(f"{'='*60}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Dossier PDFs: {os.path.abspath(self.pdf_folder)}")
        print(f"Dossier TXTs: {os.path.abspath(self.txt_folder)}")
        print(f"Total des PDFs traités: {len(results)}")
        print(f"Extractions réussies: {len(successful)}")
        print(f"Extractions échouées: {len(failed)}")
        
        if successful:
            total_pdf_size = sum(r['pdf_size'] for r in successful)
            total_txt_size = sum(r['txt_size'] for r in successful)
            print(f"Taille totale PDFs: {total_pdf_size:,} bytes ({total_pdf_size/1024/1024:.1f} MB)")
            print(f"Taille totale TXTs: {total_txt_size:,} bytes ({total_txt_size/1024/1024:.1f} MB)")
        
        print(f"\nFichiers créés:")
        print(f"  - Textes extraits: {len(successful)} fichiers .txt")
        print(f"  - Fichier index: index_extractions.txt")
        print(f"  - Métadonnées JSON: metadata_extractions.json")
        
        if failed:
            print(f"\nÉchecs d'extraction:")
            for fail in failed[:5]:  # Afficher les 5 premiers échecs
                print(f"  - {fail['pdf_file']}")
            if len(failed) > 5:
                print(f"  ... et {len(failed) - 5} autres")
        
        print(f"{'='*60}")

def main():
    """Fonction principale"""
    print("Démarrage de l'extraction des PDFs vers TXT...")
    print(f"Dossier source: {os.path.abspath(DOSSIER_PDFS)}")
    print(f"Dossier destination: {os.path.abspath(DOSSIER_TXTS)}")
    print("-" * 50)
    
    extractor = PDFExtractor()
    
    # Extraire tous les PDFs
    results = extractor.extract_all_pdfs()
    
    # Créer les fichiers de métadonnées
    extractor.create_index_file(results)
    extractor.create_json_metadata(results)
    
    # Créer le rapport final
    extractor.create_report(results)

if __name__ == "__main__":
    main()