from neo4j import GraphDatabase, AsyncGraphDatabase
from typing import List, Dict, Any
import asyncio

from app.models.embed import Entity, Relationship, GraphContext
from app.config import get_settings

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
            await session.run(
                "CREATE INDEX entity_user IF NOT EXISTS FOR (e:Entity) ON (e.user_id)"
            )
            print("Created Neo4j indexes (including user_id for isolation)")
    
    async def add_entity(self, entity: Entity, user_id: str = None):
        """Add or merge an entity with user isolation"""
        async with self.driver.session() as session:
            if user_id:
                # With user isolation: merge based on name AND user_id
                await session.run("""
                    MERGE (e:Entity {name: $name, user_id: $user_id})
                    SET e.type = $type,
                        e += $properties,
                        e.embedding = $embedding,
                        e.updated_at = datetime()
                """, 
                    name=entity.name,
                    user_id=user_id,
                    type=entity.type,
                    properties=entity.properties,
                    embedding=entity.embedding
                )
            else:
                # Without user isolation (backward compatibility)
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
    
    async def add_relationship(self, relationship: Relationship, user_id: str = None):
        """Add a relationship between entities with dynamic relationship type and user isolation"""
        async with self.driver.session() as session:
            # Sanitize relationship type to ensure it's a valid Neo4j relationship type
            rel_type = self._sanitize_relationship_type(relationship.type)
            
            if user_id:
                # With user isolation: match entities by name AND user_id
                query = f"""
                    MATCH (source:Entity {{name: $source, user_id: $user_id}})
                    MATCH (target:Entity {{name: $target, user_id: $user_id}})
                    MERGE (source)-[r:{rel_type}]->(target)
                    SET r += $properties,
                        r.user_id = $user_id,
                        r.updated_at = datetime()
                """
                
                await session.run(
                    query,
                    source=relationship.source,
                    target=relationship.target,
                    user_id=user_id,
                    properties=relationship.properties
                )
            else:
                # Without user isolation (backward compatibility)
                query = f"""
                    MATCH (source:Entity {{name: $source}})
                    MATCH (target:Entity {{name: $target}})
                    MERGE (source)-[r:{rel_type}]->(target)
                    SET r += $properties,
                        r.updated_at = datetime()
                """
                
                await session.run(
                    query,
                    source=relationship.source,
                    target=relationship.target,
                    properties=relationship.properties
                )
    
    def _sanitize_relationship_type(self, rel_type: str) -> str:
        """Sanitize relationship type to be a valid Neo4j relationship label"""
        # Remove any characters that aren't alphanumeric or underscore
        # Convert to uppercase and replace spaces with underscores
        import re
        sanitized = re.sub(r'[^A-Za-z0-9_]', '_', rel_type.upper())
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = '_' + sanitized
        return sanitized or 'RELATES_TO'
    
    async def batch_insert(
        self, 
        entities: List[Entity], 
        relationships: List[Relationship],
        user_id: str = None
    ):
        """Batch insert entities and relationships with user isolation"""
        try:
            if user_id:
                print(f"Batch inserting {len(entities)} entities and {len(relationships)} relationships for user: {user_id}")
            else:
                print(f"Batch inserting {len(entities)} entities and {len(relationships)} relationships (no user isolation)")
            
            # Insert entities in batches
            async with self.driver.session() as session:
                for entity in entities:
                    await self.add_entity(entity, user_id=user_id)
                
                for relationship in relationships:
                    await self.add_relationship(relationship, user_id=user_id)
            
            print("Batch insert completed")
            
        except Exception as e:
            print(f"Error in batch insert: {str(e)}")
            raise
    
    async def query_subgraph(
        self, 
        entity_names: List[str], 
        max_depth: int = 2,
        user_id: str = None
    ) -> GraphContext:
        """Query subgraph around given entities with user isolation"""
        async with self.driver.session() as session:
            if user_id:
                # With user isolation: only query entities belonging to this user
                result = await session.run("""
                    MATCH (e:Entity)
                    WHERE e.name IN $entity_names AND e.user_id = $user_id
                    CALL apoc.path.subgraphAll(e, {
                        maxLevel: $max_depth,
                        labelFilter: "+Entity",
                        relationshipFilter: ">",
                        filterStartNode: false
                    })
                    YIELD nodes, relationships
                    WITH nodes, relationships
                    WHERE ALL(n IN nodes WHERE n.user_id = $user_id)
                    RETURN nodes, relationships
                """,
                    entity_names=entity_names,
                    max_depth=max_depth,
                    user_id=user_id
                )
            else:
                # Without user isolation (backward compatibility)
                result = await session.run("""
                    MATCH (e:Entity)
                    WHERE e.name IN $entity_names
                    CALL apoc.path.subgraphAll(e, {
                        maxLevel: $max_depth
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
                    type=type(rel).__name__,  # Get the actual relationship type
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
        top_k: int = 5,
        user_id: str = None
    ) -> List[Entity]:
        """Find similar entities using vector similarity with user isolation"""
        async with self.driver.session() as session:
            if user_id:
                # With user isolation: only search entities belonging to this user
                result = await session.run("""
                    MATCH (e:Entity)
                    WHERE e.embedding IS NOT NULL AND e.user_id = $user_id
                    WITH e, gds.similarity.cosine(e.embedding, $embedding) AS similarity
                    ORDER BY similarity DESC
                    LIMIT $top_k
                    RETURN e, similarity
                """,
                    embedding=embedding,
                    top_k=top_k,
                    user_id=user_id
                )
            else:
                # Without user isolation (backward compatibility)
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