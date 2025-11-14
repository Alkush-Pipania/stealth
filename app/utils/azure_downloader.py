import requests
from pathlib import Path
import tempfile
from typing import Optional
from io import BytesIO

from app.config import get_settings

settings = get_settings()


class AzureBlobDownloader:
    def __init__(self):
        """Initialize Azure Blob Downloader"""
        pass
    
    async def download_from_url(self, azure_url: str, download_path: Optional[str] = None) -> str:
        """
        Download a blob from Azure using its URL (simple HTTP GET)
        Works with public URLs or URLs with SAS tokens already embedded
        
        Args:
            azure_url: Full Azure blob URL (can include SAS token in URL)
            download_path: Optional path to save the file. If None, uses temp directory
            
        Returns:
            Path to the downloaded file
        """
        try:
            print(f"Downloading from URL: {azure_url}")
            
            # Fetch PDF from Azure Blob URL directly (just like your working code!)
            response = requests.get(azure_url, timeout=120)
            
            if response.status_code != 200:
                raise Exception(f"Failed to fetch PDF from Azure Blob URL. Status: {response.status_code}")
            
            # Determine download path
            if download_path is None:
                # Extract file extension from URL
                url_path = azure_url.split('?')[0]  # Remove query params
                file_extension = Path(url_path).suffix or '.pdf'
                
                # Create temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False, 
                    suffix=file_extension
                )
                download_path = temp_file.name
                temp_file.close()
            
            # Ensure directory exists
            Path(download_path).parent.mkdir(parents=True, exist_ok=True)
            
            # Write the downloaded content to file
            with open(download_path, "wb") as download_file:
                download_file.write(response.content)
            
            print(f"Successfully downloaded to: {download_path}")
            return download_path
            
        except Exception as e:
            print(f"Error downloading from Azure: {str(e)}")
            raise
    

