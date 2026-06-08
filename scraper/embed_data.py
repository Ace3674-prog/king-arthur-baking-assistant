import json
import os

from sentence_transformers import (
    SentenceTransformer
)

model = None


def get_model():
    global model
    if model is None:
        print("Loading embedding model...")
        model = SentenceTransformer(
            "all-MiniLM-L6-v2"
        )
    return model


def create_and_save_embeddings(products):
    """
    Create embeddings for products and save to embeddings.json
    """
    
    model = get_model()
    embedded_products = []
    failed_products = []

    print(
        f"Creating embeddings for "
        f"{len(products)} products..."
    )

    # =========================
    # CREATE EMBEDDINGS
    # =========================

    for index, product in enumerate(products):

        try:

            print(
                f"Embedding product "
                f"{index + 1}/{len(products)}: "
                f"{product.get('name', 'Unknown')}"
            )

            text = f"""
        Name:
        {product.get('name', '')}

        Price:
        {product.get('price', '')}

        Description:
        {product.get('description', '')}

        Ingredients:
        {product.get('ingredients', '')}

        Rating:
        {product.get('rating', '')}

        Reviews:
        {product.get('reviews', '')}
        """

            embedding = model.encode(
                text
            ).tolist()

            embedded_products.append(
                {
                    "text": text,
                    "embedding": embedding,
                    "metadata": product
                }
            )

            print("✓ Success")

        except Exception as e:

            print(
                f"✗ FAILED: {e}"
            )
            failed_products.append(
                product.get('name', 'Unknown')
            )

    # =========================
    # SAVE TO FILE
    # =========================

    os.makedirs(
        "data",
        exist_ok=True
    )

    OUTPUT_PATH = (
        "data/embeddings.json"
    )

    with open(
        OUTPUT_PATH,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            embedded_products,
            f,
            indent=2
        )

    print(
        f"\n{'='*50}"
    )
    print(
        f"Saved "
        f"{len(embedded_products)}/{len(products)} embeddings to "
        f"{OUTPUT_PATH}"
    )
    
    if failed_products:
        print(
            f"\nFailed to embed "
            f"{len(failed_products)} products:"
        )
        for name in failed_products:
            print(f"  - {name}")
    
    print(
        f"{'='*50}"
    )

    return embedded_products