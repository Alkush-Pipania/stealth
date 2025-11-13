"""
Complete workflow example: Ingest documents and query them.
"""
import requests
import time
import json
from typing import Dict, Any, List


API_BASE_URL = "http://localhost:8000/api/v1"


class GraphRAGClient:
    """Simple client for Graph RAG API."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.base_url = base_url

    def health_check(self) -> Dict[str, Any]:
        """Check system health."""
        response = requests.get(f"{self.base_url}/graph-rag/health")
        response.raise_for_status()
        return response.json()

    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        response = requests.get(f"{self.base_url}/graph-rag/stats")
        response.raise_for_status()
        return response.json()

    def ingest_document(
        self,
        file_url: str,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Ingest a document."""
        payload = {
            "file_url": file_url,
            "metadata": metadata or {}
        }
        response = requests.post(
            f"{self.base_url}/graph-rag/ingest",
            json=payload,
            timeout=300
        )
        response.raise_for_status()
        return response.json()

    def query(
        self,
        query: str,
        top_k: int = 10,
        use_graph: bool = True
    ) -> Dict[str, Any]:
        """Query the system."""
        payload = {
            "query": query,
            "top_k": top_k,
            "use_graph": use_graph,
            "graph_depth": 2
        }
        response = requests.post(
            f"{self.base_url}/graph-rag/query",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()

    def hybrid_search(
        self,
        query: str,
        filters: Dict[str, Any] = None,
        top_k: int = 10
    ) -> Dict[str, Any]:
        """Perform hybrid search."""
        payload = {
            "query": query,
            "filters": filters,
            "top_k": top_k
        }
        response = requests.post(
            f"{self.base_url}/graph-rag/hybrid-search",
            json=payload,
            timeout=60
        )
        response.raise_for_status()
        return response.json()


def print_section(title: str):
    """Print a section header."""
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)
    print()


def main():
    """Main workflow demonstration."""
    client = GraphRAGClient()

    print_section("Graph RAG Complete Workflow Demo")

    # Step 1: Health Check
    print_section("Step 1: Health Check")
    try:
        health = client.health_check()
        print(f"Status: {health['status']}")
        print(f"Services:")
        for service, status in health['services'].items():
            print(f"  - {service}: {status}")
    except Exception as e:
        print(f"Health check failed: {e}")
        print("Make sure the API is running!")
        return

    # Step 2: Get Initial Stats
    print_section("Step 2: System Statistics")
    try:
        stats = client.get_stats()
        print("Vector Store:")
        print(json.dumps(stats.get('vector_store', {}), indent=2))
    except Exception as e:
        print(f"Could not get stats: {e}")

    # Step 3: Ingest Documents
    print_section("Step 3: Ingesting Documents")

    documents = [
        {
            "url": "https://yourstorage.blob.core.windows.net/documents/doc1.pdf",
            "metadata": {
                "title": "AI Research Paper",
                "author": "Dr. Smith",
                "category": "research",
                "year": 2024
            }
        },
        {
            "url": "https://yourstorage.blob.core.windows.net/documents/doc2.pdf",
            "metadata": {
                "title": "Machine Learning Guide",
                "author": "Dr. Johnson",
                "category": "tutorial",
                "year": 2024
            }
        }
    ]

    print("NOTE: Replace these URLs with actual document URLs from your Azure Blob Storage")
    print()

    ingested_docs = []

    for i, doc in enumerate(documents, 1):
        print(f"Ingesting document {i}/{len(documents)}: {doc['metadata']['title']}")
        print(f"URL: {doc['url']}")

        try:
            result = client.ingest_document(doc['url'], doc['metadata'])

            print(f"✓ Success!")
            print(f"  Document ID: {result['document_id']}")
            print(f"  Chunks: {result['chunks_created']}")
            print(f"  Images: {result['images_extracted']}")
            print(f"  Entities: {result['entities_extracted']}")
            print(f"  Time: {result['processing_time_seconds']:.2f}s")

            ingested_docs.append(result)

        except Exception as e:
            print(f"✗ Failed: {e}")

        print()
        time.sleep(1)

    # Step 4: Query Documents
    print_section("Step 4: Querying Documents")

    queries = [
        "What are the main topics discussed?",
        "Explain the key concepts of artificial intelligence",
        "What are the practical applications mentioned?",
    ]

    for query_text in queries:
        print(f"Query: {query_text}")
        print("-" * 80)

        try:
            result = client.query(query_text, top_k=5, use_graph=True)

            print(f"Found {result['num_results']} results")
            print(f"Entities: {result['num_entities']}")
            print(f"Graph Enhanced: {result['graph_enhanced']}")
            print()

            print("Top 3 Results:")
            for i, res in enumerate(result['results'][:3], 1):
                print(f"{i}. Score: {res['score']:.4f}")
                print(f"   {res['text'][:150]}...")
                print()

        except Exception as e:
            print(f"Query failed: {e}")

        print()

    # Step 5: Hybrid Search
    print_section("Step 5: Hybrid Search")

    try:
        search_query = "machine learning algorithms"
        print(f"Searching for: {search_query}")
        print("-" * 80)

        result = client.hybrid_search(
            query=search_query,
            filters={"category": "research"},
            top_k=5
        )

        print(f"Vector Results: {result['num_vector_results']}")
        print(f"Entity Results: {result['num_entity_results']}")
        print()

        print("Top Results:")
        for i, res in enumerate(result['results'][:3], 1):
            print(f"{i}. Final Score: {res.get('final_score', 0):.4f}")
            text = res.get('metadata', {}).get('text', '')
            print(f"   {text[:150]}...")
            print()

    except Exception as e:
        print(f"Hybrid search failed: {e}")

    # Step 6: Final Stats
    print_section("Step 6: Final Statistics")

    try:
        stats = client.get_stats()
        print("System Summary:")
        print(json.dumps(stats, indent=2))
    except Exception as e:
        print(f"Could not get stats: {e}")

    print_section("Workflow Complete!")
    print("Summary:")
    print(f"  Documents Ingested: {len(ingested_docs)}")
    print(f"  Queries Executed: {len(queries) + 1}")
    print()
    print("Next steps:")
    print("  - Explore the API docs: http://localhost:8000/api/docs")
    print("  - View Neo4j graph: http://localhost:7474")
    print("  - Integrate with your application")


if __name__ == "__main__":
    main()
