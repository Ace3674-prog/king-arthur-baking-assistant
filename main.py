from scraper.web_scraper import (
    scrape_mixes
)

from scraper.embed_data import (
    create_and_save_embeddings
)

from scraper.chroma_store import (
    create_chroma_db_from_embeddings
)

import json
import os


def main():

    products = scrape_mixes()

    # Create folder
    os.makedirs(
        "data/processed",
        exist_ok=True
    )

    # Save products
    with open(
        "data/processed/products.json",
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            products,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        "Products saved successfully"
    )

    # Create and save embeddings
    create_and_save_embeddings(
        products
    )
    
    # Create Chroma DB from embeddings
    print("\n" + "="*50)
    create_chroma_db_from_embeddings()


if __name__ == "__main__":

    main()