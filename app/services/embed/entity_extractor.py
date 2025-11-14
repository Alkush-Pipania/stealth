from typing import List, Tuple
# from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
import json

from app.models.embed import Entity, Relationship, DocumentChunk
from app.config import get_settings

settings = get_settings()

class EntityExtractor:
    def __init__(self):
        # self.llm = ChatGoogleGenerativeAI(
        #     model="gemini-2.5-flash",
        #     temperature=0,
        #     api_key=settings.GOOGLE_API_KEY
        # )
        
        self.extraction_prompt = ChatPromptTemplate.from_template("""
Extract entities and relationships from the following legal deposition document text.

Text: {text}

Return a JSON object with:
{{
  "entities": [
    {{"name": "entity name", "type": "entity type", "properties": {{}}}},
    ...
  ],
  "relationships": [
    {{"source": "entity1", "target": "entity2", "type": "relationship type", "properties": {{}}}},
    ...
  ]
}}

ENTITY TYPES for legal depositions:
- Person (deponent, attorney, witness, plaintiff, defendant, etc.)
- Organization (law firm, company, government agency)
- Location (deposition venue, incident location, address)
- Event (incident, meeting, transaction, occurrence)
- Document (contract, email, report, evidence)
- Date (specific dates or time periods)
- Legal_Concept (claim, allegation, defense, charge)
- Case (lawsuit, legal matter)

RELATIONSHIP TYPES for legal depositions (use UPPERCASE with underscores):
- TESTIFIED_BY (Event -> Person: who gave testimony about an event)
- REPRESENTED_BY (Person -> Person: client represented by attorney)
- EMPLOYED_BY (Person -> Organization: employment relationship)
- WORKS_FOR (Person -> Organization: current or past employment)
- OCCURRED_AT (Event -> Location/Date: where/when something happened)
- WITNESSED (Person -> Event: person witnessed an event)
- INVOLVED_IN (Person -> Event: person participated in event)
- MENTIONED_IN (any -> Document: entity referenced in a document)
- AUTHORED (Person -> Document: who created a document)
- RECEIVED (Person -> Document: who received a document)
- SENT_TO (Document -> Person: document sent to person)
- CONTRADICTS (any -> any: contradictory statements or evidence)
- SUPPORTS (any -> any: corroborating statements or evidence)
- CROSS_EXAMINED_BY (Person -> Person: witness cross-examined by attorney)
- DEPOSED_BY (Person -> Person: deponent questioned by attorney)
- RELATED_TO (Case -> Person/Organization: parties involved in case)
- FILED_BY (Document -> Person: who filed the document)
- ALLEGES (Person -> Legal_Concept: who made an allegation)
- DENIES (Person -> Legal_Concept: who denied an allegation)
- EMPLOYED_AT (Person -> Organization: past/present employment)
- SUPERVISED_BY (Person -> Person: supervisory relationship)
- REPORTING_TO (Person -> Person: organizational hierarchy)
- LOCATED_IN (Organization -> Location: where organization is based)

Rules:
- Extract ALL meaningful entities (people, organizations, locations, events, documents, dates, legal concepts)
- Create SPECIFIC relationships with clear meaning - NO generic "RELATES" relationships
- Use consistent naming (e.g., "John Doe" not "john doe" or "John DOE")
- Relationship types MUST be one of the types listed above or similar specific verbs
- Include relevant properties (dates, context, details) in the properties field
- For dates, extract them as separate Date entities and connect with OCCURRED_AT
- Focus on factual relationships that can be verified from the text
- If multiple relationships exist between two entities, create separate relationship entries

Return ONLY the JSON object, no other text.
""")
    
    async def extract(self, chunk: DocumentChunk) -> Tuple[List[Entity], List[Relationship]]:
        """Extract entities and relationships from a chunk"""
        try:
            print(f"Extracting entities from chunk: {chunk.id}")
            
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
            # response = await self.llm.ainvoke(messages)
            
            # Parse JSON response
            # content = response.content.strip()
            # if content.startswith("```json"):
            #     content = content[7:-3].strip()
            # elif content.startswith("```"):
            #     content = content[3:-3].strip()
            
            # data = json.loads(content)
            
            # entities = [Entity(**e) for e in data.get("entities", [])]
            # relationships = [Relationship(**r) for r in data.get("relationships", [])]
            
            # print(f"Extracted {len(entities)} entities and {len(relationships)} relationships")
            # return entities, relationships
            
        except Exception as e:
            print(f"Error extracting entities: {str(e)}")
            return [], []