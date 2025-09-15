import pdfplumber
import requests
import os
import re
from typing import List, Tuple
import tiktoken
from urllib.parse import urlparse

class PDFService:
    def __init__(self):
        """
        Initialize PDF service
        """
        self.encoding = tiktoken.encoding_for_model("gpt-4")
        os.makedirs("downloads", exist_ok=True)
    
    def download_pdf(self, url: str) -> str:
        """
        Download PDF from URL
        
        Args:
            url: URL of the PDF to download
            
        Returns:
            Path to the downloaded PDF file
        """
        try:
            # Parse URL to get filename
            parsed_url = urlparse(url)
            filename = os.path.basename(parsed_url.path)
            
            if not filename.endswith('.pdf'):
                filename = "downloaded_document.pdf"
            
            file_path = os.path.join("downloads", filename)
            
            # Download the PDF
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(file_path, "wb") as pdf_file:
                for chunk in response.iter_content(chunk_size=8192):
                    pdf_file.write(chunk)
            
            return file_path
            
        except Exception as e:
            raise Exception(f"Error downloading PDF: {str(e)}")
    
    def extract_text(self, pdf_path: str) -> str:
        """
        Extract text from PDF file
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Extracted text content
        """
        try:
            text = ""
            
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            
            return text.strip()
            
        except Exception as e:
            raise Exception(f"Error extracting text from PDF: {str(e)}")
    
    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 40, 
                   split_on_whitespace_only: bool = True) -> List[str]:
        """
        Split text into chunks with overlap
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk in characters
            overlap: Overlap between chunks in characters
            split_on_whitespace_only: Whether to split only on whitespace
            
        Returns:
            List of text chunks
        """
        try:
            chunks = []
            index = 0

            while index < len(text):
                if split_on_whitespace_only:
                    prev_whitespace = 0
                    left_index = index - overlap
                    while left_index >= 0:
                        if text[left_index] == " ":
                            prev_whitespace = left_index
                            break
                        left_index -= 1
                    
                    next_whitespace = text.find(" ", index + chunk_size)
                    if next_whitespace == -1:
                        next_whitespace = len(text)
                    
                    chunk = text[prev_whitespace:next_whitespace].strip()
                    chunks.append(chunk)
                    index = next_whitespace + 1
                else:
                    start = max(0, index - overlap + 1)
                    end = min(index + chunk_size + overlap, len(text))
                    chunk = text[start:end].strip()
                    chunks.append(chunk)
                    index += chunk_size

            return [chunk for chunk in chunks if chunk]  # Remove empty chunks
            
        except Exception as e:
            print(f"Error chunking text: {e}")
            return [text]  # Return original text as single chunk if chunking fails
    
    def split_text_by_titles(self, text: str) -> List[str]:
        """
        Split text by section titles (from inspiration code)
        
        Args:
            text: Text to split
            
        Returns:
            List of sections
        """
        try:
            # A regular expression pattern for titles that
            # match lines starting with one or more digits, an optional uppercase letter,
            # followed by a dot, a space, and then up to 50 characters
            title_pattern = re.compile(r"(\n\d+[A-Z]?\. {1,3}.{0,60}\n)", re.DOTALL)
            titles = title_pattern.findall(text)
            
            # Split the text at these titles
            sections = re.split(title_pattern, text)
            sections_with_titles = []
            
            # Append the first section
            if sections:
                sections_with_titles.append(sections[0])
            
            # Iterate over the rest of sections
            for i in range(1, len(titles) + 1):
                if i * 2 - 1 < len(sections) and i * 2 < len(sections):
                    section_text = sections[i * 2 - 1].strip() + "\n" + sections[i * 2].strip()
                    sections_with_titles.append(section_text)

            return [section for section in sections_with_titles if section.strip()]
            
        except Exception as e:
            print(f"Error splitting text by titles: {e}")
            return [text]  # Return original text if splitting fails
    
    def create_parent_child_chunks(self, text: str, parent_size: int = 2000, 
                                  child_size: int = 500, overlap: int = 40) -> List[Tuple[str, List[str]]]:
        """
        Create parent-child chunk structure
        
        Args:
            text: Text to chunk
            parent_size: Size of parent chunks
            child_size: Size of child chunks
            overlap: Overlap between chunks
            
        Returns:
            List of tuples (parent_chunk, [child_chunks])
        """
        try:
            # First split by sections if possible
            sections = self.split_text_by_titles(text)
            
            parent_child_pairs = []
            
            for section in sections:
                # Create parent chunks from sections
                parent_chunks = self.chunk_text(section, parent_size, overlap)
                
                for parent_chunk in parent_chunks:
                    # Create child chunks from each parent
                    child_chunks = self.chunk_text(parent_chunk, child_size, 20)
                    parent_child_pairs.append((parent_chunk, child_chunks))
            
            return parent_child_pairs
            
        except Exception as e:
            print(f"Error creating parent-child chunks: {e}")
            # Fallback to simple chunking
            parent_chunks = self.chunk_text(text, parent_size, overlap)
            return [(chunk, self.chunk_text(chunk, child_size, 20)) for chunk in parent_chunks]
    
    def num_tokens_from_string(self, string: str, model: str = "gpt-4") -> int:
        """
        Returns the number of tokens in a text string.
        
        Args:
            string: Text string
            model: Model name for tokenizer
            
        Returns:
            Number of tokens
        """
        try:
            num_tokens = len(self.encoding.encode(string))
            return num_tokens
        except Exception:
            # Fallback: approximate token count
            return int(len(string.split()) * 1.3)
    
    def get_pdf_metadata(self, pdf_path: str) -> dict:
        """
        Extract metadata from PDF
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with PDF metadata
        """
        try:
            metadata = {}
            
            with pdfplumber.open(pdf_path) as pdf:
                metadata.update({
                    "num_pages": len(pdf.pages),
                    "pdf_metadata": pdf.metadata or {},
                })
                
                # Get first page dimensions if available
                if pdf.pages:
                    first_page = pdf.pages[0]
                    metadata["page_width"] = first_page.width
                    metadata["page_height"] = first_page.height
            
            return metadata
            
        except Exception as e:
            return {"error": f"Error extracting PDF metadata: {str(e)}"}
    
    def extract_text_with_structure(self, pdf_path: str) -> dict:
        """
        Extract text with structural information
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Dictionary with structured text data
        """
        try:
            result = {
                "full_text": "",
                "pages": [],
                "metadata": self.get_pdf_metadata(pdf_path)
            }
            
            with pdfplumber.open(pdf_path) as pdf:
                for i, page in enumerate(pdf.pages):
                    page_text = page.extract_text()
                    if page_text:
                        result["pages"].append({
                            "page_number": i + 1,
                            "text": page_text,
                            "char_count": len(page_text),
                            "token_count": self.num_tokens_from_string(page_text)
                        })
                        result["full_text"] += page_text + "\n"
            
            result["full_text"] = result["full_text"].strip()
            result["total_chars"] = len(result["full_text"])
            result["total_tokens"] = self.num_tokens_from_string(result["full_text"])
            
            return result
            
        except Exception as e:
            return {"error": f"Error extracting structured text: {str(e)}"}
    
    def cleanup_downloaded_files(self, keep_recent: int = 10):
        """
        Clean up old downloaded files
        
        Args:
            keep_recent: Number of recent files to keep
        """
        try:
            downloads_dir = "downloads"
            if not os.path.exists(downloads_dir):
                return
            
            files = []
            for filename in os.listdir(downloads_dir):
                file_path = os.path.join(downloads_dir, filename)
                if os.path.isfile(file_path):
                    files.append((file_path, os.path.getmtime(file_path)))
            
            # Sort by modification time (newest first)
            files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old files
            for file_path, _ in files[keep_recent:]:
                try:
                    os.remove(file_path)
                    print(f"Removed old file: {file_path}")
                except Exception as e:
                    print(f"Error removing file {file_path}: {e}")
                    
        except Exception as e:
            print(f"Error cleaning up files: {e}")
