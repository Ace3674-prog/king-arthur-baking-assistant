"""
Flask API for King Arthur Product Search
"""

from flask import Flask, request, jsonify
from scraper.chroma_store import search_products
import os


app = Flask(__name__)


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "ok",
            "message": "API is running"
        }
    )


@app.route("/search", methods=["POST"])
def search():
    """
    Search for products
    
    Request body:
    {
        "query": "chocolate cake mix",
        "limit": 5
    }
    """
    
    try:
        
        data = request.get_json()
        query = data.get(
            "query",
            ""
        )
        limit = data.get(
            "limit",
            5
        )
        
        if not query:
            return jsonify(
                {
                    "error": "Query is required"
                }
            ), 400
        
        # Search Chroma DB
        results = search_products(
            query,
            num_results=limit
        )
        
        # Format results
        products = []
        
        if results and results["ids"]:
            
            for idx, (
                id_,
                distance,
                doc,
                metadata
            ) in enumerate(
                zip(
                    results["ids"][0],
                    results["distances"][0],
                    results["documents"][0],
                    results["metadatas"][0]
                )
            ):
                
                products.append(
                    {
                        "id": id_,
                        "name": metadata.get(
                            "name",
                            "Unknown"
                        ),
                        "price": metadata.get(
                            "price",
                            "N/A"
                        ),
                        "link": metadata.get(
                            "link",
                            ""
                        ),
                        "match_score": (
                            (1 - distance) * 100
                        ),
                        "rank": idx + 1
                    }
                )
        
        return jsonify(
            {
                "query": query,
                "total_results": len(products),
                "products": products
            }
        )
    
    except Exception as e:
        
        return jsonify(
            {
                "error": str(e)
            }
        ), 500


@app.route("/search/<query>", methods=["GET"])
def search_get(query):
    """
    Search for products (GET endpoint)
    
    Usage: /search/chocolate%20cake?limit=5
    """
    
    try:
        
        limit = request.args.get(
            "limit",
            5,
            type=int
        )
        
        # Search Chroma DB
        results = search_products(
            query,
            num_results=limit
        )
        
        # Format results
        products = []
        
        if results and results["ids"]:
            
            for idx, (
                id_,
                distance,
                doc,
                metadata
            ) in enumerate(
                zip(
                    results["ids"][0],
                    results["distances"][0],
                    results["documents"][0],
                    results["metadatas"][0]
                )
            ):
                
                products.append(
                    {
                        "id": id_,
                        "name": metadata.get(
                            "name",
                            "Unknown"
                        ),
                        "price": metadata.get(
                            "price",
                            "N/A"
                        ),
                        "link": metadata.get(
                            "link",
                            ""
                        ),
                        "match_score": (
                            (1 - distance) * 100
                        ),
                        "rank": idx + 1
                    }
                )
        
        return jsonify(
            {
                "query": query,
                "total_results": len(products),
                "products": products
            }
        )
    
    except Exception as e:
        
        return jsonify(
            {
                "error": str(e)
            }
        ), 500


if __name__ == "__main__":
    
    print("Starting API server...")
    print("Visit http://localhost:5000/health")
    print(
        "Search: POST to http://localhost:5000/search"
    )
    
    app.run(
        debug=True,
        host="0.0.0.0",
        port=5000
    )
