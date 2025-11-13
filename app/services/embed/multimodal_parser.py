from llama_parse import LlamaParse
from llama_index.core import Document
from pathlib import Path
from typing import List
import base64
from PIL import Image
import io

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage

from app.config import get_settings
from app.models.embed import ContentType, DocumentChunk
from app.utils.logger import setup_logger

logger = setup_logger(__name__)
settings = get_settings()

class MultimodalParser:
    def __init__(self):
        self.parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            verbose=True,
            language="en",
            parsing_instruction="Extract all text, tables, and images with their context"
        )
        
        # Initialize Gemini vision model
        self.vision_model = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            google_api_key=settings.GOOGLE_API_KEY
        )
    
    async def parse_document(self, file_path: str) -> List[DocumentChunk]:
        """Parse multimodal documents with tables and images"""
        try:
            logger.info(f"Parsing document: {file_path}")
            
            # Parse with LlamaParse
            documents = await self.parser.aload_data(file_path)
            
            chunks = []
            for idx, doc in enumerate(documents):
                # Extract text chunks
                text_chunks = self._chunk_text(doc.text)
                
                for chunk_idx, text in enumerate(text_chunks):
                    chunk = DocumentChunk(
                        id=f"{Path(file_path).stem}_{idx}_{chunk_idx}",
                        content=text,
                        content_type=ContentType.TEXT,
                        metadata={
                            "source": file_path,
                            "page": doc.metadata.get("page", idx),
                            "chunk_index": chunk_idx
                        }
                    )
                    chunks.append(chunk)
                
                # Extract tables
                if "table" in doc.metadata:
                    table_chunk = DocumentChunk(
                        id=f"{Path(file_path).stem}_{idx}_table",
                        content=doc.metadata["table"],
                        content_type=ContentType.TABLE,
                        metadata={
                            "source": file_path,
                            "page": doc.metadata.get("page", idx),
                            "type": "table"
                        }
                    )
                    chunks.append(table_chunk)
                
                # Extract images
                if "images" in doc.metadata:
                    for img_idx, img_data in enumerate(doc.metadata["images"]):
                        image_chunk = await self._process_image(
                            img_data, 
                            file_path, 
                            idx, 
                            img_idx
                        )
                        chunks.append(image_chunk)
            
            logger.info(f"Parsed {len(chunks)} chunks from {file_path}")
            return chunks
            
        except Exception as e:
            logger.error(f"Error parsing document {file_path}: {str(e)}")
            raise
    
    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text with overlap"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        return splitter.split_text(text)
    
    async def _process_image(
        self, 
        img_data: bytes, 
        source: str, 
        page: int, 
        img_idx: int
    ) -> DocumentChunk:
        """Process image and generate description using Gemini vision model"""
        # Save image
        img_path = f"data/images/{Path(source).stem}_p{page}_img{img_idx}.png"
        Path(img_path).parent.mkdir(parents=True, exist_ok=True)
        
        img = Image.open(io.BytesIO(img_data))
        img.save(img_path)
        
        # Convert image to base64 for Gemini
        base64_image = base64.b64encode(img_data).decode('utf-8')
        
        # Generate description with Gemini Vision
        message = HumanMessage(
            content=[
                {
                    "type": "text",
                    "text": "Describe this image in detail, including any text, charts, diagrams, or important visual information."
                },
                {
                    "type": "image_url",
                    "image_url": f"data:image/png;base64,{base64_image}"
                }
            ]
        )
        
        response = await self.vision_model.ainvoke([message])
        description = response.content
        
        return DocumentChunk(
            id=f"{Path(source).stem}_p{page}_img{img_idx}",
            content=description,
            content_type=ContentType.IMAGE,
            metadata={
                "source": source,
                "page": page,
                "image_index": img_idx
            },
            image_path=img_path
        ) 