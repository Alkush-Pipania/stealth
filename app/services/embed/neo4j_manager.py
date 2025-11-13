from neo4j import GraphDatabase, AsyncGraphDatabase
from typing import List, Dict, Any
import asyncio

from app.models.embed import Entity, Relationship, GraphContext
from app.utils.logger import setup_logger
from app.config import get_settings

logger = setup_logger(__name__)
settings = get_settings()

class Neo4jManager:
    def __init__(self):
        self.driver = AsyncGraphDatabase.driver(
            settings.NEO4J_URI,
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
    
    async def close(self):
        await self.driver.close()
    
    async def create_indexes(self):
        """Create necessary indexes for performance"""
        async with self.driver.session() as session:
            await session.run(
                "CREATE INDEX entity_name IF NOT EXISTS FOR (e:Entity) ON (e.name)"
            )
            await session.run(
                "CREATE INDEX entity_type IF NOT EXISTS FOR (e:Entity) ON (e.type)"
            )
            logger.info("Created Neo4j indexes")
    
    async def add_entity(self, entity: Entity):
        """Add or merge an entity"""
        async with self.driver.session() as session:
            await session.run("""
                MERGE (e:Entity {name: $name})
                SET e.type = $type,
                    e += $properties,
                    e.embedding = $embedding,
                    e.updated_at = datetime()
            """, 
                name=entity.name,
                type=entity.type,
                properties=entity.properties,
                embedding=entity.embedding
            )
    
    async def add_relationship(self, relationship: Relationship):
        """Add a relationship between entities"""
        async with self.driver.session() as session:
            await session.run("""
                MATCH (source:Entity {name: $source})
                MATCH (target:Entity {name: $target})
                MERGE (source)-[r:RELATES {type: $type}]->(target)
                SET r += $properties,
                    r.updated_at = datetime()
            """,
                source=relationship.source,
                target=relationship.target,
                type=relationship.type,
                properties=relationship.properties
            )
    
    async def batch_insert(
        self, 
        entities: List[Entity], 
        relationships: List[Relationship]
    ):
        """Batch insert entities and relationships"""
        try:
            logger.info(f"Batch inserting {len(entities)} entities and {len(relationships)} relationships")
            
            # Insert entities in batches
            async with self.driver.session() as session:
                for entity in entities:
                    await self.add_entity(entity)
                
                for relationship in relationships:
                    await self.add_relationship(relationship)
            
            logger.info("Batch insert completed")
            
        except Exception as e:
            logger.error(f"Error in batch insert: {str(e)}")
            raise
    
    async def query_subgraph(
        self, 
        entity_names: List[str], 
        max_depth: int = 2
    ) -> GraphContext:
        """Query subgraph around given entities"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (e:Entity)
                WHERE e.name IN $entity_names
                CALL apoc.path.subgraphAll(e, {
                    maxLevel: $max_depth,
                    relationshipFilter: "RELATES>"
                })
                YIELD nodes, relationships
                RETURN nodes, relationships
            """,
                entity_names=entity_names,
                max_depth=max_depth
            )
            
            record = await result.single()
            if not record:
                return GraphContext(entities=[], relationships=[], chunks=[])
            
            entities = [
                Entity(
                    name=node["name"],
                    type=node["type"],
                    properties=dict(node),
                    embedding=node.get("embedding")
                )
                for node in record["nodes"]
            ]
            
            relationships = [
                Relationship(
                    source=rel.start_node["name"],
                    target=rel.end_node["name"],
                    type=rel["type"],
                    properties=dict(rel)
                )
                for rel in record["relationships"]
            ]
            
            return GraphContext(
                entities=entities,
                relationships=relationships,
                chunks=[]
            )
    
    async def similarity_search(
        self, 
        embedding: List[float], 
        top_k: int = 5
    ) -> List[Entity]:
        """Find similar entities using vector similarity"""
        async with self.driver.session() as session:
            result = await session.run("""
                MATCH (e:Entity)
                WHERE e.embedding IS NOT NULL
                WITH e, gds.similarity.cosine(e.embedding, $embedding) AS similarity
                ORDER BY similarity DESC
                LIMIT $top_k
                RETURN e, similarity
            """,
                embedding=embedding,
                top_k=top_k
            )
            
            entities = []
            async for record in result:
                node = record["e"]
                entities.append(Entity(
                    name=node["name"],
                    type=node["type"],
                    properties=dict(node),
                    embedding=node.get("embedding")
                ))
            
            return entities