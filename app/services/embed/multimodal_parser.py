from llama_parse import LlamaParse
from pathlib import Path
from typing import List
import os
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.config import get_settings
from app.models.embed import ContentType, DocumentChunk

settings = get_settings()

class MultimodalParser:
    def __init__(self):
        # Comprehensive parsing instruction for multimodal content
        parsing_instruction = """
        You are parsing a comprehensive document that may contain text, tables, charts, and images.
        
        For text content:
        - Extract all headings, subheadings, and body text
        - Maintain the original structure and hierarchy
        - Preserve formatting like bullet points and numbered lists
        
        For tables:
        - Convert all tables to markdown format
        - Preserve all data, headers, and structure
        - Include table captions if present
        
        For charts and graphs:
        - Describe the chart type and what it represents
        - Extract all numerical values, labels, and legends
        - Create a 2D table of relevant values when possible
        - Include chart titles and axis labels
        
        For images and diagrams:
        - Provide detailed descriptions of visual content
        - List all visible text, labels, and annotations
        - Describe relationships between components
        - Extract any embedded text or data
        
        Make sure to parse content in the correct reading order and maintain document structure.
        """
        
        print("🦙 Initializing LlamaParse with multimodal capabilities...")
        self.parser = LlamaParse(
            api_key=settings.LLAMA_CLOUD_API_KEY,
            result_type="markdown",
            use_vendor_multimodal_model=True,
            vendor_multimodal_model_name="gemini-2.0-flash-001",
            invalidate_cache=True,
            parsing_instruction=parsing_instruction,
            verbose=True,
            show_progress=True,
            max_timeout=300  # 5 minute timeout
        )
    
    async def parse_document(self, file_path: str) -> List[DocumentChunk]:
        """
        Parse multimodal documents using LlamaParse with full multimodal support.
        LlamaParse handles text, tables, images, and charts automatically.
        """
        try:
            print(f"📄 Parsing document: {file_path}")
            
            # Verify file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if not os.path.isfile(file_path):
                raise ValueError(f"Path is not a file: {file_path}")
            
            file_size = os.path.getsize(file_path)
            print(f"📊 File size: {file_size / (1024*1024):.2f} MB")
            
            if file_size == 0:
                raise ValueError("File is empty")
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                print("⚠️  File is large, this may take longer to process...")
            
            # Use LlamaParse to get JSON result with full multimodal parsing
            print("🔄 Calling LlamaParse API with multimodal support...")
            
            # Run synchronous get_json_result in executor to avoid event loop conflict
            loop = asyncio.get_event_loop()
            with ThreadPoolExecutor() as executor:
                json_objs = await loop.run_in_executor(executor, self.parser.get_json_result, file_path)
            
            if not json_objs:
                print("⚠️  LlamaParse returned None, falling back to load_data...")
                # Fallback to load_data
                documents = await self.parser.aload_data(file_path)
                return self._process_documents_to_chunks(documents, file_path)
            
            print(f"📄 LlamaParse returned {len(json_objs)} objects")
            
            if len(json_objs) == 0:
                raise ValueError("LlamaParse returned empty results")
            
            # Check if the first object has pages
            if "pages" not in json_objs[0]:
                print(f"⚠️  Available keys in result: {list(json_objs[0].keys())}")
                print("Falling back to load_data method...")
                documents = await self.parser.aload_data(file_path)
                return self._process_documents_to_chunks(documents, file_path)
            
            json_list = json_objs[0]["pages"]
            print(f"📑 Processing {len(json_list)} pages from LlamaParse")
            
            if len(json_list) == 0:
                raise ValueError("No pages found in LlamaParse result")
            
            # Convert JSON pages to chunks
            chunks = []
            for page_idx, page_data in enumerate(json_list):
                page_num = page_idx + 1
                
                # Extract markdown content from page
                if "md" in page_data:
                    markdown_content = page_data["md"]
                elif "text" in page_data:
                    markdown_content = page_data["text"]
                else:
                    print(f"Page {page_num}: No markdown or text found")
                    continue
                
                # Chunk the markdown content
                text_chunks = self._chunk_text(markdown_content)
                
                # Create chunks using helper method
                page_chunks = self._create_chunks_from_text(
                    text_chunks=text_chunks,
                    file_path=file_path,
                    id_prefix=f"{Path(file_path).stem}_p{page_num}_c",
                    page=page_num,
                    parsing_method="llamaparse_multimodal"
                )
                chunks.extend(page_chunks)
            
            print(f"✅ Multimodal parsing extracted {len(chunks)} chunks")
            return chunks
            
        except Exception as e:
            print(f"❌ Error parsing document {file_path}: {str(e)}")
            raise
    
    def _process_documents_to_chunks(self, documents: List, file_path: str) -> List[DocumentChunk]:
        """Convert LlamaIndex documents to chunks (fallback method)"""
        chunks = []
        
        for idx, doc in enumerate(documents):
            # Extract text chunks
            text_chunks = self._chunk_text(doc.text)
            
            # Create chunks using helper method
            doc_chunks = self._create_chunks_from_text(
                text_chunks=text_chunks,
                file_path=file_path,
                id_prefix=f"{Path(file_path).stem}_{idx}_",
                page=doc.metadata.get("page", idx),
                parsing_method="llamaparse_fallback"
            )
            chunks.extend(doc_chunks)
        
        print(f"Parsed {len(chunks)} chunks from {len(documents)} documents")
        return chunks
    
    def _create_chunks_from_text(
        self,
        text_chunks: List[str],
        file_path: str,
        id_prefix: str,
        page: int,
        parsing_method: str
    ) -> List[DocumentChunk]:
        """
        Helper method to create DocumentChunk objects from text chunks.
        
        Args:
            text_chunks: List of text chunks to convert
            file_path: Path to the source file
            id_prefix: Prefix for chunk IDs (e.g., "doc_p1_c" or "doc_0_")
            page: Page number for metadata
            parsing_method: Method used for parsing (e.g., "llamaparse_multimodal")
            
        Returns:
            List of DocumentChunk objects
        """
        chunks = []
        for chunk_idx, text in enumerate(text_chunks):
            chunk = DocumentChunk(
                id=f"{id_prefix}{chunk_idx}",
                content=text,
                content_type=ContentType.TEXT,
                metadata={
                    "source": file_path,
                    "page": page,
                    "chunk_index": chunk_idx,
                    "parsing_method": parsing_method
                }
            )
            chunks.append(chunk)
        return chunks
    
    def _chunk_text(self, text: str) -> List[str]:
        """Chunk text with overlap"""
        from langchain.text_splitter import RecursiveCharacterTextSplitter
        
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            separators=["\n\n", "\n", ". ", " ", ""]
        )
        return splitter.split_text(text)
