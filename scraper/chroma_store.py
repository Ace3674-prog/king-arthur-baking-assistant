import json
import os
from typing import Any, Dict, Optional

import chromadb
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import Chroma

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(BASE_DIR, os.pardir))
EMBEDDINGS_PATH = os.path.join(REPO_ROOT, "data", "embeddings.json")
CHROMA_DB_PATH = os.path.join(REPO_ROOT, "chroma_db")


# ============================================
# CREATE CHROMA DB
# ============================================

def create_chroma_db_from_embeddings():
    """
    Load embeddings from embeddings.json
    and store them in ChromaDB
    """

    embeddings_path = EMBEDDINGS_PATH

    print(f"Loading embeddings from {embeddings_path}...")

    with open(
        embeddings_path,
        "r",
        encoding="utf-8"
    ) as f:

        embedded_data = json.load(f)

    print(f"Loaded {len(embedded_data)} embeddings")

    # ============================================
    # Initialize Chroma
    # ============================================

    chroma_db_path = CHROMA_DB_PATH

    os.makedirs(
        chroma_db_path,
        exist_ok=True
    )

    client = chromadb.PersistentClient(
        path=chroma_db_path
    )

    collection_name = "king_arthur_products"

    # ============================================
    # Delete old collection (IMPORTANT)
    # ============================================

    try:

        client.delete_collection(collection_name)

        print("Deleted old collection")

    except:

        pass

    # ============================================
    # Create fresh collection
    # ============================================

    collection = client.create_collection(
        name=collection_name,
        metadata={
            "hnsw:space": "cosine"
        }
    )

    print(f"Created collection: {collection_name}")

    # ============================================
    # Prepare Data
    # ============================================

    ids = []
    embeddings = []
    documents = []
    metadatas = []

    for idx, item in enumerate(embedded_data):

        metadata_data = item.get("metadata", {})

        product_id = metadata_data.get("sku")
        if not product_id:
            product_id = f"prod_{idx}"

        # ============================================
        # SEARCHABLE TEXT
        # ============================================

        searchable_text = f"""
        Product Name:
        {metadata_data.get('name', '')}

        Description:
        {metadata_data.get('description', '')}

        Ingredients:
        {metadata_data.get('ingredients', '')}

        Price:
        {metadata_data.get('price', '')}

        Rating:
        {metadata_data.get('rating', '')}

        Reviews:
        {metadata_data.get('reviews', '')}

        Brand:
        King Arthur Baking

        Category:
        Baking Mix

        Keywords:
        baking mix, cookie mix, cake mix,
        muffin mix, pancake mix, scone mix,
        bread mix, baking ingredients
        """

        ids.append(str(product_id))
        embeddings.append(item["embedding"])
        documents.append(searchable_text)

        # ============================================
        # FULL METADATA
        # ============================================

        metadata = {
            "name": str(metadata_data.get("name", "")),
            "price": str(metadata_data.get("price", "")),
            "link": str(metadata_data.get("link", "")),
            "description": str(metadata_data.get("description", ""))[:5000],
            "rating": str(metadata_data.get("rating", "")),
            "reviews": str(metadata_data.get("reviews", "")),
            "sku": str(metadata_data.get("sku", "")),
            "ingredients": str(metadata_data.get("ingredients", ""))[:5000],
            "images": json.dumps(metadata_data.get("images", []))
        }

        metadatas.append(metadata)

    # ============================================
    # Add To ChromaDB
    # ============================================

    print("Adding products to ChromaDB...")

    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas
    )

    print(f"Added {len(ids)} products")

    print(
        f"Database Count: "
        f"{collection.count()}"
    )

    return collection


# ============================================
# LANGCHAIN RETRIEVER HELPERS
# ============================================

def create_embedding_function(
    model_name: str = "all-MiniLM-L6-v2"
):
    """Build an embedding function for LangChain retrieval."""
    return SentenceTransformerEmbeddings(
        model_name=model_name
    )


def get_chroma_vector_store(
    collection_name: str = "king_arthur_products",
    persist_directory: str = CHROMA_DB_PATH,
    embedding_model_name: str = "all-MiniLM-L6-v2"
):
    embeddings = create_embedding_function(
        model_name=embedding_model_name
    )

    return Chroma(
        collection_name=collection_name,
        embedding_function=embeddings,
        persist_directory=persist_directory
    )


def get_chroma_retriever(
    collection_name: str = "king_arthur_products",
    persist_directory: str = CHROMA_DB_PATH,
    embedding_model_name: str = "all-MiniLM-L6-v2",
    search_kwargs: Optional[Dict[str, Any]] = None
):
    vector_store = get_chroma_vector_store(
        collection_name=collection_name,
        persist_directory=persist_directory,
        embedding_model_name=embedding_model_name
    )

    if search_kwargs is None:
        search_kwargs = {"k": 5}

    return vector_store.as_retriever(
        search_type="similarity",
        search_kwargs=search_kwargs
    )


# ============================================
# SEARCH PRODUCTS
# ============================================

def search_products(
    query_text,
    num_results=5
):
    vector_store = get_chroma_vector_store()

    results = vector_store.similarity_search_with_score(
        query=query_text,
        k=num_results
    )

    # DEBUG HERE
    print("\n" + "=" * 60)
    print("QUERY:", query_text)
    print("=" * 60)

    for doc, score in results:
        print(f"\nScore: {score}")
        print(
            "Product:",
            doc.metadata.get(
                "name",
                "Unknown"
            )
        )
        print("Preview:")
        print(doc.page_content[:200])

    ids = []
    documents = []
    metadatas = []
    distances = []

    for idx, (doc, score) in enumerate(results):
        metadata = doc.metadata or {}

        ids.append(
            str(
                metadata.get(
                    "sku",
                    metadata.get(
                        "id",
                        f"prod_{idx}"
                    )
                )
            )
        )

        documents.append(
            doc.page_content
        )

        metadatas.append(
            metadata
        )

        distances.append(
            float(score)
        )

    return {
        "ids": [ids],
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances]
    }
# TESTING
# ============================================

if __name__ == "__main__":

    print("=" * 50)
    print("CREATING CHROMADB")
    print("=" * 50)

    create_chroma_db_from_embeddings()

    print("\nTesting Search...\n")

    results = search_products(
        "blueberry scone mix",
        num_results=2
    )

    print(json.dumps(results, indent=2))