import json
import chromadb

# =========================
# LOAD EMBEDDINGS
# =========================

with open(
    "data/embeddings.json",
    "r",
    encoding="utf-8"
) as f:

    embedded_products = json.load(f)

print(
    f"Loaded "
    f"{len(embedded_products)} embeddings"
)

# =========================
# CREATE CHROMADB CLIENT
# =========================

client = chromadb.PersistentClient(
    path="data/chroma_db"
)

collection = client.get_or_create_collection(
    name="products"
)

# =========================
# ADD PRODUCTS
# =========================

for index, item in enumerate(
    embedded_products
):

    try:

        collection.add(
            ids=[str(index)],

            documents=[
                item["text"]
            ],

            embeddings=[
                item["embedding"]
            ],

            metadatas=[
                item["metadata"]
            ]
        )

        print(
            f"Added product "
            f"{index + 1}"
        )

    except Exception as e:

        print(
            f"Failed: {e}"
        )

print(
    "\nVector database created"
)