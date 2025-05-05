import streamlit as st
import requests
from bs4 import BeautifulSoup
import os
import re
from urllib.parse import urljoin
import time
import zipfile
from io import BytesIO

# Base URL of the syllabus page
BASE_URL = "https://ptu.ac.in/syllabus/#1610102986246-e6ac72c5-c6da"
DOWNLOAD_DIR = "ptu_cse_syllabus_pdfs"

# Create directory for PDFs if it doesn't exist
if not os.path.exists(DOWNLOAD_DIR):
    os.makedirs(DOWNLOAD_DIR)

def get_page_content(url):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        st.error(f"Error fetching {url}: {e}")
        return None

def extract_cse_pdf_links(html_content, base_url):
    pdf_links = []
    soup = BeautifulSoup(html_content, 'html.parser')
    
    for a_tag in soup.find_all('a', href=True):
        href = a_tag['href']
        if href.lower().endswith('.pdf') and 'cse' in href.lower():
            full_url = urljoin(base_url, href)
            filename = href.split('/')[-1]
            filename = re.sub(r'[^\w\-\.]', '', filename)
            pdf_links.append((full_url, filename))
    
    return pdf_links

def download_pdf(url, filename, download_dir):
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        file_path = os.path.join(download_dir, filename)
        
        if not os.path.exists(file_path):
            with open(file_path, 'wb') as f:
                f.write(response.content)
            return True, f"Downloaded: {filename}"
        else:
            return True, f"Already exists: {filename}"
    except requests.RequestException as e:
        return False, f"Error downloading {url}: {e}"

def create_zip_of_pdfs(download_dir):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename in os.listdir(download_dir):
            if filename.endswith('.pdf'):
                file_path = os.path.join(download_dir, filename)
                zip_file.write(file_path, os.path.join("cse_syllabus_pdfs", filename))
    zip_buffer.seek(0)
    return zip_buffer

# Streamlit app
st.title("PTU CSE Syllabus Downloader")
st.markdown("This app scrapes and downloads Computer Science and Engineering (CSE) syllabus PDFs from the PTU website.")

# Button to start scraping
if st.button("Scrape CSE Syllabus PDFs"):
    with st.spinner("Fetching syllabus page..."):
        html_content = get_page_content(BASE_URL)
        
        if not html_content:
            st.error("Failed to retrieve the page content.")
        else:
            # Extract PDF links
            pdf_links = extract_cse_pdf_links(html_content, BASE_URL)
            
            if not pdf_links:
                st.warning("No CSE syllabus PDF links found on the page.")
            else:
                st.success(f"Found {len(pdf_links)} CSE syllabus PDFs.")
                
                # Progress bar
                progress_bar = st.progress(0)
                status_text = st.empty()
                downloaded_files = []
                
                # Download each PDF
                for i, (url, filename) in enumerate(pdf_links):
                    success, message = download_pdf(url, filename, DOWNLOAD_DIR)
                    status_text.text(message)
                    if success:
                        downloaded_files.append((filename, os.path.join(DOWNLOAD_DIR, filename)))
                    progress_bar.progress((i + 1) / len(pdf_links))
                    time.sleep(0.1)  # Brief pause for UI update
                
                # Display downloadable files
                st.subheader("Downloaded Files")
                for filename, file_path in downloaded_files:
                    with open(file_path, "rb") as file:
                        st.download_button(
                            label=f"Download {filename}",
                            data=file,
                            file_name=filename,
                            mime="application/pdf"
                        )
                
                # Button to download all PDFs as ZIP
                if downloaded_files:
                    zip_buffer = create_zip_of_pdfs(DOWNLOAD_DIR)
                    st.download_button(
                        label="Download All PDFs as ZIP",
                        data=zip_buffer,
                        file_name="cse_syllabus_pdfs.zip",
                        mime="application/zip"
                    )
                
                st.success(f"Download complete. PDFs saved in '{DOWNLOAD_DIR}' directory.")

st.markdown("---")
st.info("Click the 'Scrape CSE Syllabus PDFs' button to start. The app will fetch and download all CSE syllabus PDFs from the PTU syllabus page. After downloading, you can download individual PDFs or all as a ZIP file.")
