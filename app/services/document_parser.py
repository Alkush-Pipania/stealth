"""Document parsing service using LlamaParse with multi-modal support."""
import logging
import tempfile
from typing import List, Dict, Any, Optional
from pathlib import Path
import io

from llama_parse import LlamaParse
from llama_index.core import Document
from llama_index.core.node_parser import SimpleNodeParser
from llama_index.core.schema import TextNode, ImageNode
import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class DocumentParserService:
    """Service for parsing documents with multi-modal support."""

    def __init__(self):
        """Initialize document parser with LlamaParse."""
        self.llama_parse = None
        self.node_parser = None
        self._initialize_parser()
        self._initialize_gemini()

    def _initialize_parser(self):
        """Initialize LlamaParse client."""
        try:
            if not settings.LLAMA_CLOUD_API_KEY:
                logger.warning("LlamaParse API key not provided")
                return

            self.llama_parse = LlamaParse(
                api_key=settings.LLAMA_CLOUD_API_KEY,
                result_type="markdown",  # Get markdown output
                verbose=True,
                language="en",
                parsing_instruction="Extract all text and identify images. Preserve structure and formatting."
            )

            self.node_parser = SimpleNodeParser.from_defaults(
                chunk_size=settings.CHUNK_SIZE,
                chunk_overlap=settings.CHUNK_OVERLAP,
            )

            logger.info("LlamaParse initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize LlamaParse: {e}")
            raise

    def _initialize_gemini(self):
        """Initialize Gemini for image description."""
        try:
            if settings.ENABLE_IMAGE_EXTRACTION and settings.GOOGLE_API_KEY:
                genai.configure(api_key=settings.GOOGLE_API_KEY)
                logger.info("Gemini configured for image description")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")

    async def parse_document(
        self,
        file_content: bytes,
        file_name: str,
        extract_images: bool = True
    ) -> Dict[str, Any]:
        """
        Parse a document and extract text and images.

        Args:
            file_content: Document content as bytes
            file_name: Name of the file
            extract_images: Whether to extract and describe images

        Returns:
            Dictionary containing parsed text nodes and image metadata
        """
        try:
            logger.info(f"Parsing document: {file_name}")

            # Create temporary file for LlamaParse
            with tempfile.NamedTemporaryFile(
                suffix=Path(file_name).suffix,
                delete=False
            ) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name

            # Parse document using LlamaParse
            documents = self.llama_parse.load_data(temp_file_path)

            # Clean up temp file
            Path(temp_file_path).unlink()

            # Extract text content
            text_content = "\n\n".join([doc.text for doc in documents])

            # Parse into chunks/nodes
            text_nodes = self.node_parser.get_nodes_from_documents(documents)

            logger.info(f"Extracted {len(text_nodes)} text chunks from {file_name}")

            # Extract images if enabled
            image_data = []
            if extract_images and settings.ENABLE_IMAGE_EXTRACTION:
                image_data = await self._extract_images(file_content, file_name)

            return {
                "file_name": file_name,
                "text_nodes": text_nodes,
                "image_nodes": image_data,
                "raw_text": text_content,
                "metadata": {
                    "num_text_chunks": len(text_nodes),
                    "num_images": len(image_data),
                    "file_name": file_name,
                }
            }

        except Exception as e:
            logger.error(f"Error parsing document {file_name}: {e}")
            raise

    async def _extract_images(
        self,
        file_content: bytes,
        file_name: str
    ) -> List[Dict[str, Any]]:
        """
        Extract and describe images from PDF.

        Args:
            file_content: PDF content as bytes
            file_name: Name of the file

        Returns:
            List of image metadata with descriptions
        """
        image_data = []

        try:
            from pypdf import PdfReader
            from PIL import Image

            # Read PDF
            pdf_stream = io.BytesIO(file_content)
            pdf_reader = PdfReader(pdf_stream)

            logger.info(f"Extracting images from {file_name}")

            for page_num, page in enumerate(pdf_reader.pages):
                if "/XObject" in page["/Resources"]:
                    x_objects = page["/Resources"]["/XObject"].get_object()

                    for obj_name in x_objects:
                        obj = x_objects[obj_name]

                        if obj["/Subtype"] == "/Image":
                            try:
                                # Extract image data
                                image_bytes = obj.get_data()

                                # Convert to PIL Image
                                image = Image.open(io.BytesIO(image_bytes))

                                # Generate description using Gemini
                                description = await self._describe_image(image)

                                image_data.append({
                                    "page": page_num + 1,
                                    "image_name": f"{file_name}_page{page_num + 1}_{obj_name}",
                                    "description": description,
                                    "size": image.size,
                                    "format": image.format,
                                })

                                logger.info(f"Extracted image from page {page_num + 1}")

                            except Exception as e:
                                logger.warning(f"Could not process image on page {page_num + 1}: {e}")
                                continue

            logger.info(f"Extracted {len(image_data)} images from {file_name}")

        except Exception as e:
            logger.error(f"Error extracting images from {file_name}: {e}")

        return image_data

    async def _describe_image(self, image: Any) -> str:
        """
        Generate description for an image using Gemini.

        Args:
            image: PIL Image object

        Returns:
            Image description
        """
        try:
            model = genai.GenerativeModel(settings.IMAGE_DESCRIPTION_MODEL)

            # Convert PIL Image to bytes
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='PNG')
            img_byte_arr.seek(0)

            # Generate description
            response = model.generate_content([
                "Describe this image in detail, focusing on key elements, text content, and visual information that would be useful for document understanding:",
                image
            ])

            return response.text

        except Exception as e:
            logger.error(f"Error describing image: {e}")
            return "Image description unavailable"

    def create_text_nodes(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[TextNode]:
        """
        Create text nodes from raw text.

        Args:
            text: Raw text content
            metadata: Optional metadata to attach

        Returns:
            List of TextNode objects
        """
        try:
            document = Document(text=text, metadata=metadata or {})
            nodes = self.node_parser.get_nodes_from_documents([document])
            return nodes
        except Exception as e:
            logger.error(f"Error creating text nodes: {e}")
            raise


# Singleton instance
_document_parser_service: Optional[DocumentParserService] = None


def get_document_parser_service() -> DocumentParserService:
    """Get or create document parser service instance."""
    global _document_parser_service
    if _document_parser_service is None:
        _document_parser_service = DocumentParserService()
    return _document_parser_service
