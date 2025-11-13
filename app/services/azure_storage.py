"""Azure Blob Storage service for document retrieval."""
import io
import logging
from typing import Optional
from azure.storage.blob import BlobServiceClient, BlobClient
from azure.core.exceptions import ResourceNotFoundError
from app.config import settings

logger = logging.getLogger(__name__)


class AzureStorageService:
    """Service for interacting with Azure Blob Storage."""

    def __init__(self):
        """Initialize Azure Blob Storage client."""
        self.connection_string = settings.AZURE_STORAGE_CONNECTION_STRING
        self.container_name = settings.AZURE_STORAGE_CONTAINER_NAME
        self.blob_service_client: Optional[BlobServiceClient] = None
        self._initialize_client()

    def _initialize_client(self):
        """Initialize the blob service client."""
        try:
            if self.connection_string:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    self.connection_string
                )
                logger.info("Azure Blob Storage client initialized successfully")
            else:
                logger.warning("Azure Storage connection string not provided")
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob Storage client: {e}")
            raise

    def download_blob_from_url(self, blob_url: str) -> bytes:
        """
        Download a blob from Azure Storage using its URL.

        Args:
            blob_url: Full URL to the blob or blob name

        Returns:
            Blob content as bytes

        Raises:
            ResourceNotFoundError: If blob not found
            Exception: For other errors
        """
        try:
            # Extract blob name from URL if it's a full URL
            if blob_url.startswith("http"):
                blob_name = blob_url.split(f"{self.container_name}/")[-1].split("?")[0]
            else:
                blob_name = blob_url

            logger.info(f"Downloading blob: {blob_name}")

            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            # Download blob content
            stream = io.BytesIO()
            blob_client.download_blob().readinto(stream)
            stream.seek(0)

            content = stream.read()
            logger.info(f"Successfully downloaded blob: {blob_name}, size: {len(content)} bytes")

            return content

        except ResourceNotFoundError:
            logger.error(f"Blob not found: {blob_url}")
            raise ValueError(f"Document not found: {blob_url}")
        except Exception as e:
            logger.error(f"Error downloading blob from {blob_url}: {e}")
            raise

    def download_blob_to_file(self, blob_url: str, file_path: str):
        """
        Download a blob and save it to a file.

        Args:
            blob_url: Full URL to the blob or blob name
            file_path: Local file path to save the blob
        """
        try:
            content = self.download_blob_from_url(blob_url)
            with open(file_path, 'wb') as file:
                file.write(content)
            logger.info(f"Blob saved to: {file_path}")
        except Exception as e:
            logger.error(f"Error saving blob to file: {e}")
            raise

    def upload_blob(self, blob_name: str, data: bytes, overwrite: bool = True) -> str:
        """
        Upload data to Azure Blob Storage.

        Args:
            blob_name: Name for the blob
            data: Data to upload
            overwrite: Whether to overwrite existing blob

        Returns:
            URL of the uploaded blob
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            blob_client.upload_blob(data, overwrite=overwrite)
            logger.info(f"Successfully uploaded blob: {blob_name}")

            return blob_client.url

        except Exception as e:
            logger.error(f"Error uploading blob {blob_name}: {e}")
            raise

    def list_blobs(self, prefix: str = "") -> list:
        """
        List blobs in the container.

        Args:
            prefix: Optional prefix to filter blobs

        Returns:
            List of blob names
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                self.container_name
            )

            blobs = container_client.list_blobs(name_starts_with=prefix)
            blob_names = [blob.name for blob in blobs]

            logger.info(f"Found {len(blob_names)} blobs with prefix '{prefix}'")
            return blob_names

        except Exception as e:
            logger.error(f"Error listing blobs: {e}")
            raise

    def delete_blob(self, blob_name: str):
        """
        Delete a blob from storage.

        Args:
            blob_name: Name of the blob to delete
        """
        try:
            blob_client = self.blob_service_client.get_blob_client(
                container=self.container_name,
                blob=blob_name
            )

            blob_client.delete_blob()
            logger.info(f"Successfully deleted blob: {blob_name}")

        except Exception as e:
            logger.error(f"Error deleting blob {blob_name}: {e}")
            raise


# Singleton instance
_azure_storage_service: Optional[AzureStorageService] = None


def get_azure_storage_service() -> AzureStorageService:
    """Get or create Azure Storage service instance."""
    global _azure_storage_service
    if _azure_storage_service is None:
        _azure_storage_service = AzureStorageService()
    return _azure_storage_service
