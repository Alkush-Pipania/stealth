"""Graph RAG query engine combining vector search and graph traversal."""
import logging
from typing import Dict, Any, List, Optional

from app.services.embeddings import get_embeddings_service
from app.services.vector_store import get_vector_store_service
from app.services.graph_store import get_graph_store_service

logger = logging.getLogger(__name__)


class GraphRAGQueryEngine:
    """Query engine for Graph RAG system."""

    def __init__(self):
        """Initialize the query engine."""
        self.embeddings_service = get_embeddings_service()
        self.vector_store = get_vector_store_service()
        self.graph_store = get_graph_store_service()

    async def query(
        self,
        query: str,
        top_k: int = 10,
        namespace: str = "",
        use_graph: bool = True,
        graph_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Query the Graph RAG system.

        Args:
            query: User query
            top_k: Number of similar chunks to retrieve
            namespace: Optional namespace to search in
            use_graph: Whether to enhance results with graph data
            graph_depth: Depth of graph traversal

        Returns:
            Query results with context and graph data
        """
        try:
            logger.info(f"Processing query: {query}")

            # Step 1: Generate query embedding
            logger.info("Step 1: Generating query embedding")
            query_embedding = self.embeddings_service.embed_query(query)

            # Step 2: Vector similarity search
            logger.info("Step 2: Performing vector similarity search")
            similar_chunks = self.vector_store.query_vectors(
                query_vector=query_embedding,
                top_k=top_k,
                namespace=namespace,
                include_metadata=True
            )

            # Step 3: Extract entities from top results
            logger.info("Step 3: Extracting entities from results")
            entity_ids = self._extract_entities_from_chunks(similar_chunks)

            # Step 4: Graph-enhanced retrieval (if enabled)
            graph_context = {}
            if use_graph and entity_ids:
                logger.info("Step 4: Enhancing with graph context")
                graph_context = await self._get_graph_context(
                    entity_ids=entity_ids,
                    max_depth=graph_depth
                )

            # Step 5: Combine and rank results
            logger.info("Step 5: Combining and ranking results")
            final_results = self._combine_results(
                similar_chunks=similar_chunks,
                graph_context=graph_context
            )

            return {
                "query": query,
                "results": final_results,
                "num_results": len(similar_chunks),
                "num_entities": len(entity_ids),
                "graph_enhanced": use_graph and bool(graph_context),
                "context_chunks": [
                    {
                        "text": chunk['metadata'].get('text', ''),
                        "score": chunk['score'],
                        "doc_id": chunk['metadata'].get('doc_id', ''),
                        "type": chunk['metadata'].get('type', 'text')
                    }
                    for chunk in similar_chunks
                ],
                "graph_context": graph_context
            }

        except Exception as e:
            logger.error(f"Error processing query: {e}")
            raise

    async def hybrid_search(
        self,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """
        Perform hybrid search combining vector and graph search.

        Args:
            query: User query
            filters: Optional metadata filters
            top_k: Number of results

        Returns:
            Hybrid search results
        """
        try:
            logger.info(f"Performing hybrid search: {query}")

            # Generate query embedding
            query_embedding = self.embeddings_service.embed_query(query)

            # Vector search with filters
            vector_results = self.vector_store.query_vectors(
                query_vector=query_embedding,
                top_k=top_k * 2,  # Get more results for reranking
                filter=filters,
                include_metadata=True
            )

            # Extract and search for entities in the graph
            entity_results = await self._search_entities_in_graph(query)

            # Combine and rerank results
            combined_results = self._rerank_hybrid_results(
                vector_results=vector_results,
                entity_results=entity_results,
                top_k=top_k
            )

            return {
                "query": query,
                "results": combined_results[:top_k],
                "num_vector_results": len(vector_results),
                "num_entity_results": len(entity_results),
                "search_type": "hybrid"
            }

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            raise

    def _extract_entities_from_chunks(
        self,
        chunks: List[Dict[str, Any]]
    ) -> List[str]:
        """
        Extract entity IDs mentioned in chunk metadata.

        Args:
            chunks: List of chunk results

        Returns:
            List of entity IDs
        """
        entity_ids = []

        try:
            for chunk in chunks:
                metadata = chunk.get('metadata', {})

                # Extract entities from chunk text using graph store
                chunk_id = chunk.get('id', '')
                if chunk_id:
                    # In production, you'd query the graph for entities linked to this chunk
                    # For now, we'll use a simple approach
                    pass

            # Remove duplicates
            entity_ids = list(set(entity_ids))
            logger.info(f"Extracted {len(entity_ids)} unique entities")

        except Exception as e:
            logger.error(f"Error extracting entities: {e}")

        return entity_ids

    async def _get_graph_context(
        self,
        entity_ids: List[str],
        max_depth: int = 2
    ) -> Dict[str, Any]:
        """
        Get graph context around entities.

        Args:
            entity_ids: List of entity IDs
            max_depth: Maximum depth of graph traversal

        Returns:
            Graph context data
        """
        try:
            if not entity_ids:
                return {}

            # Query subgraph around entities
            subgraph = self.graph_store.query_subgraph(
                entity_ids=entity_ids[:10],  # Limit to 10 entities
                max_depth=max_depth
            )

            return {
                'entities': subgraph.get('nodes', []),
                'relationships': subgraph.get('relationships', []),
                'num_entities': len(subgraph.get('nodes', [])),
                'num_relationships': len(subgraph.get('relationships', []))
            }

        except Exception as e:
            logger.error(f"Error getting graph context: {e}")
            return {}

    async def _search_entities_in_graph(
        self,
        query: str
    ) -> List[Dict[str, Any]]:
        """
        Search for entities in the graph matching the query.

        Args:
            query: Search query

        Returns:
            List of matching entities
        """
        try:
            # Extract potential entity names from query
            query_terms = query.split()
            entities = []

            for term in query_terms:
                if len(term) > 3:  # Only search for terms longer than 3 chars
                    entity = self.graph_store.get_entity_by_name(term)
                    if entity:
                        entities.append(entity)

            logger.info(f"Found {len(entities)} entities matching query terms")
            return entities

        except Exception as e:
            logger.error(f"Error searching entities: {e}")
            return []

    def _combine_results(
        self,
        similar_chunks: List[Dict[str, Any]],
        graph_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Combine vector search results with graph context.

        Args:
            similar_chunks: Results from vector search
            graph_context: Graph context data

        Returns:
            Combined and enriched results
        """
        results = []

        for chunk in similar_chunks:
            result = {
                'id': chunk['id'],
                'score': chunk['score'],
                'text': chunk['metadata'].get('text', ''),
                'doc_id': chunk['metadata'].get('doc_id', ''),
                'type': chunk['metadata'].get('type', 'text'),
                'metadata': chunk['metadata']
            }

            # Add graph context if available
            if graph_context:
                result['graph_enhanced'] = True
                result['related_entities'] = graph_context.get('entities', [])[:5]
            else:
                result['graph_enhanced'] = False

            results.append(result)

        return results

    def _rerank_hybrid_results(
        self,
        vector_results: List[Dict[str, Any]],
        entity_results: List[Dict[str, Any]],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """
        Rerank results from hybrid search.

        Args:
            vector_results: Results from vector search
            entity_results: Results from entity search
            top_k: Number of top results to return

        Returns:
            Reranked results
        """
        combined = []

        # Add vector results with their scores
        for result in vector_results:
            combined.append({
                **result,
                'vector_score': result['score'],
                'entity_bonus': 0.0,
                'final_score': result['score']
            })

        # Boost scores for results that match entities
        entity_names = [e.get('name', '').lower() for e in entity_results]

        for result in combined:
            text = result.get('metadata', {}).get('text', '').lower()
            entity_matches = sum(1 for name in entity_names if name in text)

            if entity_matches > 0:
                result['entity_bonus'] = entity_matches * 0.1
                result['final_score'] = result['vector_score'] + result['entity_bonus']

        # Sort by final score
        combined.sort(key=lambda x: x['final_score'], reverse=True)

        return combined[:top_k]


# Singleton instance
_query_engine: Optional[GraphRAGQueryEngine] = None


def get_query_engine() -> GraphRAGQueryEngine:
    """Get or create query engine instance."""
    global _query_engine
    if _query_engine is None:
        _query_engine = GraphRAGQueryEngine()
    return _query_engine
