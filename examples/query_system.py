"""
Example script for querying the Graph RAG system.
"""
import requests
import sys
import json
from typing import Dict, Any, Optional


API_BASE_URL = "http://localhost:8000/api/v1"


def query_graph_rag(
    query: str,
    top_k: int = 10,
    namespace: str = "",
    use_graph: bool = True,
    graph_depth: int = 2
) -> Dict[str, Any]:
    """
    Query the Graph RAG system.

    Args:
        query: Query text
        top_k: Number of results to return
        namespace: Optional namespace (e.g., specific document ID)
        use_graph: Whether to use graph enhancement
        graph_depth: Depth of graph traversal

    Returns:
        Query results
    """
    endpoint = f"{API_BASE_URL}/graph-rag/query"

    payload = {
        "query": query,
        "top_k": top_k,
        "namespace": namespace,
        "use_graph": use_graph,
        "graph_depth": graph_depth
    }

    print(f"Querying: {query}")
    print(f"Top K: {top_k}, Graph: {use_graph}, Depth: {graph_depth}")

    try:
        response = requests.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error querying system: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


def hybrid_search(
    query: str,
    filters: Optional[Dict[str, Any]] = None,
    top_k: int = 10
) -> Dict[str, Any]:
    """
    Perform hybrid search.

    Args:
        query: Query text
        filters: Optional metadata filters
        top_k: Number of results

    Returns:
        Search results
    """
    endpoint = f"{API_BASE_URL}/graph-rag/hybrid-search"

    payload = {
        "query": query,
        "filters": filters,
        "top_k": top_k
    }

    print(f"Hybrid search: {query}")

    try:
        response = requests.post(endpoint, json=payload, timeout=60)
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error in hybrid search: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


def print_results(result: Dict[str, Any]):
    """Pretty print query results."""
    print()
    print("=" * 80)
    print("Query Results")
    print("=" * 80)
    print()

    print(f"Query: {result['query']}")
    print(f"Results Found: {result['num_results']}")
    print(f"Entities Involved: {result['num_entities']}")
    print(f"Graph Enhanced: {result['graph_enhanced']}")
    print()

    print("-" * 80)
    print("Top Results:")
    print("-" * 80)

    for i, res in enumerate(result['results'][:5], 1):
        print(f"\n{i}. Score: {res['score']:.4f} | Type: {res['type']}")
        print(f"   Document: {res['doc_id']}")
        print(f"   Text: {res['text'][:200]}...")
        if res.get('graph_enhanced'):
            print(f"   Graph Enhanced: Yes")

    # Show context chunks
    if result.get('context_chunks'):
        print()
        print("-" * 80)
        print("Context Chunks:")
        print("-" * 80)
        for i, chunk in enumerate(result['context_chunks'][:3], 1):
            print(f"\n{i}. Score: {chunk['score']:.4f}")
            print(f"   {chunk['text'][:150]}...")

    # Show graph context if available
    if result.get('graph_context') and result['graph_context']:
        print()
        print("-" * 80)
        print("Graph Context:")
        print("-" * 80)
        gc = result['graph_context']
        print(f"Entities: {gc.get('num_entities', 0)}")
        print(f"Relationships: {gc.get('num_relationships', 0)}")


def main():
    """Main function."""
    # Example queries
    queries = [
        "What are the main conclusions about artificial intelligence?",
        "Explain the methodology used in the research",
        "What are the key findings and results?",
    ]

    # Use command line argument if provided
    if len(sys.argv) > 1:
        queries = [" ".join(sys.argv[1:])]

    print("=" * 80)
    print("Graph RAG Query Example")
    print("=" * 80)
    print()

    # Standard query with graph enhancement
    for query_text in queries:
        result = query_graph_rag(
            query=query_text,
            top_k=10,
            use_graph=True,
            graph_depth=2
        )

        print_results(result)
        print()

    # Example hybrid search
    print()
    print("=" * 80)
    print("Hybrid Search Example")
    print("=" * 80)

    hybrid_result = hybrid_search(
        query="machine learning applications",
        filters={"category": "research"},
        top_k=5
    )

    print()
    print(f"Query: {hybrid_result['query']}")
    print(f"Vector Results: {hybrid_result['num_vector_results']}")
    print(f"Entity Results: {hybrid_result['num_entity_results']}")
    print(f"Search Type: {hybrid_result['search_type']}")
    print()

    for i, res in enumerate(hybrid_result['results'][:3], 1):
        print(f"{i}. Score: {res.get('final_score', 0):.4f}")
        print(f"   Text: {res.get('metadata', {}).get('text', '')[:100]}...")


if __name__ == "__main__":
    main()
