import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse
import logging
from datetime import datetime
import re

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuration du dossier de destination
DOSSIER_PDFS = os.path.join(os.path.dirname(__file__), '..', 'scraping', 'pdfs_originaux')

class JournalOfficielGuineeScraper:
    def __init__(self, base_url="https://journal-officiel.sgg.gov.gn"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'fr-FR,fr;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
    def get_page_content(self, url):
        """Récupère le contenu HTML d'une page"""
        try:
            logger.info(f"Récupération de la page: {url}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            return response.text
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors de la récupération de {url}: {e}")
            return None
    
    def extract_jo_links_from_page(self, page_number=0):
        """Extrait les liens des journaux officiels depuis une page spécifique"""
        logger.info(f"Extraction des liens JO depuis la page {page_number}...")
        
        # Construction de l'URL avec pagination
        page_url = f"{self.base_url}/fr/journal-officiel/le-journal-officiel.html?page={page_number}&row=1178"
        content = self.get_page_content(page_url)
        if not content:
            return []
        
        soup = BeautifulSoup(content, 'html.parser')
        jo_links = []
        
        # Chercher tous les liens PDF dans la page
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.endswith('.pdf'):
                full_url = urljoin(self.base_url, href)
                
                # Extraire le titre du lien
                title = link.get_text(strip=True)
                if not title:
                    # Si pas de titre, essayer de trouver le titre dans les éléments parents
                    parent = link.parent
                    if parent:
                        title = parent.get_text(strip=True)
                    if not title:
                        title = os.path.basename(urlparse(full_url).path)
                
                # Nettoyer le titre
                title = re.sub(r'\s+', ' ', title).strip()
                
                jo_links.append({
                    'url': full_url,
                    'title': title,
                    'filename': os.path.basename(urlparse(full_url).path),
                    'page': page_number
                })
        
        logger.info(f"Trouvé {len(jo_links)} journaux officiels sur la page {page_number}")
        return jo_links
    
    def get_total_pages(self):
        """Détermine le nombre total de pages à parcourir"""
        logger.info("Détermination du nombre total de pages...")
        
        # Commencer par la page 0
        page_url = f"{self.base_url}/fr/journal-officiel/le-journal-officiel.html?page=0&row=1178"
        content = self.get_page_content(page_url)
        if not content:
            return 58  # Valeur par défaut selon l'utilisateur
        
        soup = BeautifulSoup(content, 'html.parser')
        
        # Chercher les éléments de pagination
        pagination_elements = soup.find_all(['a', 'span'], class_=re.compile(r'page|pagination'))
        
        max_page = 0
        for elem in pagination_elements:
            text = elem.get_text(strip=True)
            if text.isdigit():
                max_page = max(max_page, int(text))
        
        # Si on ne trouve pas de pagination, utiliser la valeur par défaut
        if max_page == 0:
            max_page = 58
            logger.warning(f"Pagination non détectée, utilisation de la valeur par défaut: {max_page} pages")
        else:
            logger.info(f"Nombre total de pages détecté: {max_page}")
        
        return max_page
    
    def get_all_jo_links_paginated(self, max_pages=None):
        """Récupère tous les liens des journaux officiels en parcourant toutes les pages"""
        logger.info("Récupération de tous les liens JO avec pagination...")
        
        if max_pages is None:
            max_pages = self.get_total_pages()
        
        all_links = []
        
        for page in range(max_pages):
            logger.info(f"Traitement de la page {page + 1}/{max_pages}")
            
            page_links = self.extract_jo_links_from_page(page)
            all_links.extend(page_links)
            
            # Pause entre les requêtes pour éviter de surcharger le serveur
            time.sleep(2)
            
            # Si aucun lien trouvé sur cette page, on peut arrêter
            if not page_links:
                logger.warning(f"Aucun lien trouvé sur la page {page}, arrêt du parcours")
                break
        
        # Supprimer les doublons basés sur l'URL
        seen_urls = set()
        unique_links = []
        for link in all_links:
            if link['url'] not in seen_urls:
                seen_urls.add(link['url'])
                unique_links.append(link)
        
        # Trier par nom de fichier
        unique_links.sort(key=lambda x: x['filename'])
        
        logger.info(f"Total: {len(unique_links)} journaux officiels uniques trouvés sur {max_pages} pages")
        return unique_links
    
    def download_pdf(self, url, filename, download_dir=None):
        """Télécharge un PDF"""
        if download_dir is None:
            download_dir = DOSSIER_PDFS
            
        # Créer le dossier de manière récursive
        os.makedirs(download_dir, exist_ok=True)
        logger.info(f"Dossier de téléchargement: {os.path.abspath(download_dir)}")
        
        file_path = os.path.join(download_dir, filename)
        
        # Vérifier si le fichier existe déjà
        if os.path.exists(file_path):
            logger.info(f"Fichier déjà existant: {filename}")
            return True
        
        try:
            logger.info(f"Téléchargement: {filename}")
            logger.info(f"Vers: {file_path}")
            response = self.session.get(url, timeout=60)
            response.raise_for_status()
            
            # Vérifier que c'est bien un PDF
            content_type = response.headers.get('content-type', '')
            if 'pdf' not in content_type.lower() and len(response.content) < 1000:
                logger.warning(f"Le fichier {filename} ne semble pas être un PDF valide")
                return False
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            file_size = os.path.getsize(file_path)
            logger.info(f"Téléchargé avec succès: {filename} ({file_size:,} bytes)")
            logger.info(f"Sauvegardé dans: {file_path}")
            return True
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erreur lors du téléchargement de {filename}: {e}")
            return False
        except Exception as e:
            logger.error(f"Erreur inattendue lors du téléchargement de {filename}: {e}")
            return False
    
    def scrape_all_journals_paginated(self, download=True, download_dir=None, max_pages=None):
        """Scrape tous les journaux officiels en parcourant toutes les pages"""
        logger.info("Début du scraping des journaux officiels avec pagination...")
        
        if download_dir is None:
            download_dir = DOSSIER_PDFS
            
        logger.info(f"Dossier de téléchargement: {download_dir}")
        
        # Récupérer tous les liens
        jo_links = self.get_all_jo_links_paginated(max_pages)
        
        if not jo_links:
            logger.warning("Aucun journal officiel trouvé")
            return []
        
        results = []
        successful_downloads = 0
        failed_downloads = 0
        
        for i, jo in enumerate(jo_links, 1):
            logger.info(f"Traitement {i}/{len(jo_links)}: {jo['title']}")
            
            result = {
                'title': jo['title'],
                'url': jo['url'],
                'filename': jo['filename'],
                'page': jo['page'],
                'downloaded': False,
                'file_size': 0
            }
            
            if download:
                if self.download_pdf(jo['url'], jo['filename'], download_dir):
                    result['downloaded'] = True
                    successful_downloads += 1
                    
                    # Obtenir la taille du fichier
                    file_path = os.path.join(download_dir, jo['filename'])
                    if os.path.exists(file_path):
                        result['file_size'] = os.path.getsize(file_path)
                else:
                    failed_downloads += 1
                
                # Pause entre les téléchargements
                time.sleep(3)
            
            results.append(result)
        
        logger.info(f"Scraping terminé:")
        logger.info(f"  - Succès: {successful_downloads}")
        logger.info(f"  - Échecs: {failed_downloads}")
        logger.info(f"  - Total: {len(jo_links)}")
        
        return results
    
    def save_metadata(self, results, filename="jo_metadata.txt"):
        """Sauvegarde les métadonnées des journaux officiels"""
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("JOURNAUX OFFICIELS DE GUINÉE - MÉTADONNÉES\n")
            f.write("="*60 + "\n")
            f.write(f"Date de scraping: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Nombre total de journaux: {len(results)}\n")
            f.write(f"Téléchargés avec succès: {sum(1 for r in results if r['downloaded'])}\n")
            f.write(f"Échecs de téléchargement: {sum(1 for r in results if not r['downloaded'])}\n")
            f.write(f"Taille totale: {sum(r['file_size'] for r in results):,} bytes\n")
            f.write("="*60 + "\n\n")
            
            # Grouper par page
            pages = {}
            for jo in results:
                page = jo['page']
                if page not in pages:
                    pages[page] = []
                pages[page].append(jo)
            
            for page in sorted(pages.keys()):
                f.write(f"PAGE {page}:\n")
                f.write("-" * 20 + "\n")
                for jo in pages[page]:
                    f.write(f"  • {jo['title']}\n")
                    f.write(f"    URL: {jo['url']}\n")
                    f.write(f"    Fichier: {jo['filename']}\n")
                    f.write(f"    Téléchargé: {'✓' if jo['downloaded'] else '✗'}\n")
                    if jo['file_size'] > 0:
                        f.write(f"    Taille: {jo['file_size']:,} bytes\n")
                    f.write("\n")
                f.write("\n")
        
        logger.info(f"Métadonnées sauvegardées dans {filename}")
    
    def create_download_report(self, results):
        """Crée un rapport de téléchargement"""
        print(f"\n{'='*60}")
        print("RAPPORT DE TÉLÉCHARGEMENT - JOURNAUX OFFICIELS DE GUINÉE")
        print(f"{'='*60}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Total des journaux trouvés: {len(results)}")
        
        # Statistiques par page
        pages = {}
        for jo in results:
            page = jo['page']
            if page not in pages:
                pages[page] = {'total': 0, 'downloaded': 0}
            pages[page]['total'] += 1
            if jo['downloaded']:
                pages[page]['downloaded'] += 1
        
        print(f"Pages parcourues: {len(pages)}")
        
        downloaded = [r for r in results if r['downloaded']]
        failed = [r for r in results if not r['downloaded']]
        
        print(f"Téléchargés avec succès: {len(downloaded)}")
        print(f"Échecs de téléchargement: {len(failed)}")
        
        if downloaded:
            total_size = sum(r['file_size'] for r in downloaded)
            print(f"Taille totale téléchargée: {total_size:,} bytes ({total_size/1024/1024:.1f} MB)")
        
        print(f"Dossier de téléchargement: {DOSSIER_PDFS}")
        print(f"Chemin absolu: {os.path.abspath(DOSSIER_PDFS)}")
        print(f"Fichier de métadonnées: jo_metadata.txt")
        
        # Afficher les statistiques par page
        print(f"\nStatistiques par page:")
        for page in sorted(pages.keys())[:10]:  # Afficher les 10 premières pages
            stats = pages[page]
            print(f"  Page {page}: {stats['downloaded']}/{stats['total']} téléchargés")
        
        if len(pages) > 10:
            print(f"  ... et {len(pages) - 10} autres pages")
        
        if failed:
            print(f"\nÉchecs de téléchargement:")
            for fail in failed[:5]:  # Afficher les 5 premiers échecs
                print(f"  - {fail['filename']} (page {fail['page']})")
            if len(failed) > 5:
                print(f"  ... et {len(failed) - 5} autres")
        
        print(f"{'='*60}")

def main():
    """Fonction principale"""
    scraper = JournalOfficielGuineeScraper()
    
    print("Démarrage du scraping des Journaux Officiels de Guinée...")
    print("Site: https://journal-officiel.sgg.gov.gn")
    print("Parcours des 3 premières pages...")
    print(f"Dossier de destination: {DOSSIER_PDFS}")
    print(f"Chemin absolu: {os.path.abspath(DOSSIER_PDFS)}")
    print("-" * 50)
    
    # Scraper les 3 premières pages seulement
    results = scraper.scrape_all_journals_paginated(download=True, max_pages=3)
    
    # Sauvegarder les métadonnées
    scraper.save_metadata(results)
    
    # Créer le rapport final
    scraper.create_download_report(results)

if __name__ == "__main__":
    main()