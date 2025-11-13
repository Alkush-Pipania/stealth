from typing import List, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import json

from app.models.embed import Entity, Relationship, DocumentChunk
from app.utils.logger import setup_logger
from app.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class EntityExtractor:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            temperature=0,
            api_key=settings.GOOGLE_API_KEY
        )
        
        self.extraction_prompt = ChatPromptTemplate.from_template("""
Extract entities and relationships from the following text.

Text: {text}

Return a JSON object with:
{{
  "entities": [
    {{"name": "entity name", "type": "entity type (Person/Organization/Location/Concept/Product/etc)", "properties": {{}}}},
    ...
  ],
  "relationships": [
    {{"source": "entity1", "target": "entity2", "type": "relationship type", "properties": {{}}}},
    ...
  ]
}}

Rules:
- Extract all meaningful entities
- Identify clear relationships between entities
- Use consistent naming for entities
- Relationship types should be verbs (e.g., "WORKS_FOR", "LOCATED_IN", "PRODUCES")
- Be specific with entity types

Return ONLY the JSON object, no other text.
""")
    
    async def extract(self, chunk: DocumentChunk) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from a chunk"""
        try:
            logger.info(f"Extracting entities from chunk: {chunk.id}")
            
            # Skip extraction for images (already have description)
            if chunk.content_type == "image":
                # For images, create a simple entity
                entity = Entity(
                    name=f"Image_{chunk.id}",
                    type="Image",
                    properties={
                        "description": chunk.content,
                        "path": chunk.image_path
                    }
                )
                return [entity], []
            
            # Extract from text/table content
            messages = self.extraction_prompt.format_messages(text=chunk.content)
            response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:-3].strip()
            elif content.startswith("```"):
                content = content[3:-3].strip()
            
            data = json.loads(content)
            
            entities = [Entity(**e) for e in data.get("entities", [])]
            relationships = [Relationship(**r) for r in data.get("relationships", [])]
            
            logger.info(f"Extracted {len(entities)} entities and {len(relationships)} relationships")
            return entities, relationships
            
        except Exception as e:
            logger.error(f"Error extracting entities: {str(e)}")
            return [], []