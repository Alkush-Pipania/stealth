"""
Example script for ingesting a document into Graph RAG system.
"""
import requests
import sys
import json
from typing import Dict, Any


API_BASE_URL = "http://localhost:8000/api/v1"


def ingest_document(
    file_url: str,
    metadata: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Ingest a document into the Graph RAG system.

    Args:
        file_url: URL to the document in Azure Blob Storage
        metadata: Optional metadata about the document

    Returns:
        Ingestion results
    """
    endpoint = f"{API_BASE_URL}/graph-rag/ingest"

    payload = {
        "file_url": file_url,
        "metadata": metadata or {}
    }

    print(f"Ingesting document: {file_url}")
    print(f"Endpoint: {endpoint}")

    try:
        response = requests.post(endpoint, json=payload, timeout=300)
        response.raise_for_status()

        result = response.json()
        return result

    except requests.exceptions.RequestException as e:
        print(f"Error ingesting document: {e}")
        if hasattr(e.response, 'text'):
            print(f"Response: {e.response.text}")
        sys.exit(1)


def main():
    """Main function."""
    # Example usage
    file_url = "https://yourstorage.blob.core.windows.net/documents/sample.pdf"

    # You can override this with command line argument
    if len(sys.argv) > 1:
        file_url = sys.argv[1]

    metadata = {
        "title": "Sample Document",
        "author": "John Doe",
        "category": "research",
        "tags": ["AI", "machine learning", "research"]
    }

    print("=" * 60)
    print("Graph RAG Document Ingestion Example")
    print("=" * 60)
    print()

    result = ingest_document(file_url, metadata)

    print()
    print("=" * 60)
    print("Ingestion Results:")
    print("=" * 60)
    print(json.dumps(result, indent=2))
    print()

    print("Summary:")
    print(f"  Document ID: {result['document_id']}")
    print(f"  File Name: {result['file_name']}")
    print(f"  Processing Time: {result['processing_time_seconds']:.2f}s")
    print(f"  Text Chunks: {result['chunks_created']}")
    print(f"  Images Extracted: {result['images_extracted']}")
    print(f"  Entities Found: {result['entities_extracted']}")
    print(f"  Relationships: {result['relationships_created']}")
    print(f"  Vectors Stored: {result['vectors_stored']}")


if __name__ == "__main__":
    main()
