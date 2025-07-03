import os
import requests
from bs4 import BeautifulSoup
import streamlit as st
from fpdf import FPDF
import time
from urllib.parse import urljoin

# Set up Streamlit app
st.title("HBR Article Downloader")
st.write("This tool helps you download HBR articles as PDFs")

# Create directories if they don't exist
if not os.path.exists("hbr_articles"):
    os.makedirs("hbr_articles")
if not os.path.exists("hbr_pdfs"):
    os.makedirs("hbr_pdfs")

def get_article_content(url):
    """Fetch article content from HBR URL"""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Extract title
        title = soup.find('h1').get_text().strip() if soup.find('h1') else "Untitled"
        
        # Extract article content - this may need adjustment based on HBR's HTML structure
        article_body = soup.find('div', class_='article-body') or soup.find('article')
        if not article_body:
            return None, None
        
        # Clean up content
        for element in article_body(['script', 'style', 'nav', 'footer', 'iframe', 'button']):
            element.decompose()
            
        content = article_body.get_text(separator='\n', strip=True)
        
        return title, content
        
    except Exception as e:
        st.error(f"Error fetching article: {e}")
        return None, None

def create_pdf(title, content, filename):
    """Create PDF from article content"""
    try:
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        
        # Add title
        pdf.set_font(size=16, style='B')
        pdf.multi_cell(0, 10, title)
        pdf.ln(10)
        
        # Add content
        pdf.set_font(size=12)
        pdf.multi_cell(0, 10, content)
        
        # Save PDF
        pdf.output(filename)
        return True
    except Exception as e:
        st.error(f"Error creating PDF: {e}")
        return False

def download_articles(base_url, start_page, end_page, max_articles):
    """Download articles from HBR"""
    downloaded = 0
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for page in range(start_page, end_page + 1):
        if downloaded >= max_articles:
            break
            
        try:
            # Construct the page URL - this may need adjustment based on HBR's pagination
            page_url = f"{base_url}?page={page}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(page_url, headers=headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find article links - this selector may need adjustment
            article_links = soup.select('a.article-link')  # Update this selector based on HBR's HTML
            
            for link in article_links:
                if downloaded >= max_articles:
                    break
                    
                article_url = urljoin(base_url, link['href'])
                
                # Skip if already downloaded
                pdf_filename = f"hbr_pdfs/{article_url.split('/')[-1]}.pdf"
                if os.path.exists(pdf_filename):
                    continue
                
                title, content = get_article_content(article_url)
                if title and content:
                    # Save raw content
                    with open(f"hbr_articles/{title[:50]}.txt", 'w', encoding='utf-8') as f:
                        f.write(content)
                    
                    # Create PDF
                    if create_pdf(title, content, pdf_filename):
                        downloaded += 1
                        status_text.text(f"Downloaded {downloaded}/{max_articles} articles")
                        progress_bar.progress(downloaded / max_articles)
                        time.sleep(2)  # Be polite with requests
                
        except Exception as e:
            st.error(f"Error processing page {page}: {e}")
            continue
    
    return downloaded

# Streamlit UI
base_url = st.text_input("Enter HBR base URL:", "https://hbr.org/")
start_page = st.number_input("Start page:", min_value=1, value=1)
end_page = st.number_input("End page:", min_value=1, value=10)
max_articles = st.number_input("Maximum articles to download:", min_value=1, max_value=500, value=500)

if st.button("Start Download"):
    if not base_url.startswith(("http://", "https://")):
        st.error("Please enter a valid URL starting with http:// or https://")
    else:
        st.info(f"Starting download from {base_url} (pages {start_page}-{end_page})")
        downloaded_count = download_articles(base_url, start_page, end_page, max_articles)
        st.success(f"Download completed! {downloaded_count} articles saved as PDFs in 'hbr_pdfs' folder.")
        
        # Create zip file of all PDFs
        if downloaded_count > 0:
            import zipfile
            with zipfile.ZipFile('hbr_articles_collection.zip', 'w') as zipf:
                for root, _, files in os.walk('hbr_pdfs'):
                    for file in files:
                        zipf.write(os.path.join(root, file), file)
            
            with open('hbr_articles_collection.zip', 'rb') as f:
                st.download_button(
                    label="Download All PDFs as ZIP",
                    data=f,
                    file_name='hbr_articles_collection.zip',
                    mime='application/zip'
                )

# Display downloaded files
if st.checkbox("Show downloaded files"):
    if os.path.exists('hbr_pdfs'):
        pdf_files = os.listdir('hbr_pdfs')
        st.write(f"Found {len(pdf_files)} PDF files:")
        st.write(pdf_files)
    else:
        st.write("No PDF files downloaded yet.")