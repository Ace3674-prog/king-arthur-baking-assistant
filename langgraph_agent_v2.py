import json
import os
import re
import time
from typing import TypedDict, Optional, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_ollama import OllamaLLM
from scraper.chroma_store import get_chroma_retriever, get_chroma_vector_store

# Disable proxy for localhost connections
os.environ['NO_PROXY'] = '127.0.0.1,localhost'
os.environ['no_proxy'] = '127.0.0.1,localhost'

DEFAULT_OLLAMA_MODEL = 'qwen2.5:3b'
FALLBACK_OLLAMA_MODELS = ['llama3.2:3b', 'mistral:7b']

# ============================================
# STATE DEFINITION
# ============================================

class AgentState(TypedDict):
    """Enhanced state for LangGraph workflow"""
    user_input: str
    is_product_query: bool
    tool_result: Optional[str]
    response: str
    products: List[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    price_filter: Optional[Dict[str, float]]
    requested_count: int
    conversation_history: Optional[List[Dict[str, str]]]  # Added for context

# ============================================
# KING ARTHUR AGENT WITH LANGGRAPH
# ============================================

class KingArthurAgent:
    
    def __init__(self, max_retries: int = 3):
        """Initialize the agent with LangGraph workflow"""
        self.max_retries = max_retries
        
        # Initialize Ollama
        self._init_ollama()
        
        # Initialize Chroma vector store
        self._init_vector_store()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        print("✅ King Arthur Agent ready with LangGraph!")
        
    def _init_ollama(self):
        """Initialize Ollama LLM with fallback models and retry logic"""
        preferred_model = os.getenv('OLLAMA_MODEL', DEFAULT_OLLAMA_MODEL)
        model_candidates = [preferred_model] + [m for m in FALLBACK_OLLAMA_MODELS if m != preferred_model]
        last_error = None
        
        for model_name in model_candidates:
            try:
                # Test connection first
                self._test_ollama_connection()
                
                self.llm = OllamaLLM(
                    model=model_name,
                    base_url="http://127.0.0.1:11434",
                    temperature=0.3,
                    num_predict=500,
                    timeout=120,
                    repeat_penalty=1.1,
                    top_k=40,
                    top_p=0.9
                )
                self.model_name = model_name
                print(f"✅ Ollama initialized: {model_name}")
                return
            except Exception as e:
                last_error = e
                print(f"⚠️ Failed to load {model_name}: {str(e)}")
                time.sleep(1)  # Brief pause before retry
        
        raise Exception(
            f"Cannot connect to Ollama.\n\n"
            f"Please run in a NEW terminal:\n"
            f"```\n"
            f"ollama serve\n"
            f"ollama run {preferred_model}\n"
            f"```\n\n"
            f"Error: {str(last_error)}"
        )
    
    def _test_ollama_connection(self):
        """Test if Ollama service is running"""
        import requests
        try:
            response = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
            if response.status_code != 200:
                raise Exception("Ollama service not responding properly")
        except requests.exceptions.ConnectionError:
            raise Exception("Ollama service is not running. Please start it with 'ollama serve'")
    
    def _init_vector_store(self):
        """Initialize Chroma vector store with retry"""
        try:
            self.vector_store = get_chroma_vector_store()
            if self.vector_store:
                self.retriever = self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 10}
                )
                print("✅ Chroma vector store initialized")
            else:
                raise Exception("Vector store returned None")
        except Exception as e:
            print(f"⚠️ Chroma error: {str(e)}")
            self.vector_store = None
            self.retriever = None
    
    # ============================================
    # NODE 1: INTENT DETECTION
    # ============================================
    
    def detect_intent(self, state: AgentState) -> AgentState:
        """Detect if query is product-related or general chat"""
        user_input = state["user_input"].lower().strip()
        
        # Expanded product-related keywords
        product_keywords = [
            "mix", "flour", "ingredient", "ingredients", "pan", "tool", 
            "recipe", "cake", "bread", "cookie", "muffin", "brownie", 
            "pizza", "baking", "recommend", "show", "find", "buy", 
            "price", "gluten", "vegan", "organic", "chocolate", 
            "blueberry", "vanilla", "sourdough", "pancake", "product",
            "how many", "count", "number of", "best", "cheapest",
            "expensive", "top", "rated", "review", "popular",
            "item", "items", "catalog", "available", "stock"
        ]
        
        # Check for count queries
        count_patterns = [
            r"how many (products|items|results)",
            r"count of (products|items)",
            r"number of (products|items)",
            r"total products"
        ]
        
        is_count_query = any(re.search(pattern, user_input) for pattern in count_patterns)
        is_product_query = is_count_query or any(keyword in user_input for keyword in product_keywords)
        
        # Parse dynamic product count
        requested_count = self._parse_product_count_dynamic(user_input)
        
        # Parse price filter
        price_filter = self._parse_price_filter(user_input)
        
        # Check for follow-up queries
        is_follow_up = self._is_follow_up_query(user_input, state.get("conversation_history", []))
        
        state["is_product_query"] = is_product_query or is_follow_up
        state["requested_count"] = requested_count
        state["price_filter"] = price_filter
        state["retry_count"] = 0
        
        print(f"🎯 Intent: {'PRODUCT' if state['is_product_query'] else 'CHAT'} | Count: {requested_count}")
        
        return state
    
    def _is_follow_up_query(self, query: str, history: List[Dict]) -> bool:
        """Detect if this is a follow-up to a previous product search"""
        if not history:
            return False
        
        follow_up_indicators = [
            "more", "similar", "cheaper", "expensive", "alternative",
            "different", "another", "others", "also", "what about"
        ]
        
        return any(indicator in query.lower() for indicator in follow_up_indicators)
    
    def _parse_product_count_dynamic(self, text: str) -> int:
        """Intelligently parse how many products user wants to see"""
        if not isinstance(text, str):
            return 4
        
        text = text.lower()
        
        # 1. EXPLICIT NUMBER PATTERNS
        explicit_patterns = [
            r"(?:show|give me|list|find|recommend|need|display|provide|want|top|first)\s+(\d{1,2})\s+(?:products|items|results|cards)",
            r"\b(\d{1,2})\s+(?:products|items|results|cards)\b",
            r"(?:only|just)\s+(\d{1,2})\b",
            r"(?:limit|max|maximum)\s+(?:to\s+)?(\d{1,2})\b"
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    value = int(match.group(1))
                    return max(1, min(value, 20))
                except:
                    continue
        
        # 2. NATURAL LANGUAGE QUANTITY WORDS
        quantity_map = {
            r'\ba couple\b': 2,
            r'\ba few\b': 3,
            r'\bseveral\b': 5,
            r'\bmany\b': 8,
            r'\blots?\b': 10,
            r'\bplenty\b': 12,
            r'\bnumerous\b': 15,
            r'\ball\b': 20,
            r'\beverything\b': 20,
        }
        
        for pattern, count in quantity_map.items():
            if re.search(pattern, text):
                return count
        
        # 3. QUERY TYPE-BASED DEFAULTS
        if re.search(r'(cheaper|under|below|less than|budget|affordable|inexpensive)', text):
            return 3
        if re.search(r'(compare|versus|vs|difference between|compared to)', text):
            return 6
        if re.search(r'(recommend|suggest|best|top rated|popular|highest rated)', text):
            return 4
        if re.search(r'(all|every|everything)', text):
            return 10
        if re.search(r'(specific|exact|particular|precise)', text):
            return 2
        if re.search(r'(recipe|bake|make|cook|prepare)', text):
            return 3
        
        # 4. DEFAULT BASED ON QUERY LENGTH
        word_count = len(text.split())
        if word_count < 5:
            return 5
        elif word_count < 10:
            return 4
        else:
            return 3
    
    def _parse_price_filter(self, text: str) -> Optional[Dict[str, float]]:
        """Parse price filter from query"""
        text = text.lower()
        
        patterns = [
            r"(?:cheaper than|less than|under|below)\s*\$?\s*([0-9]+(?:\.[0-9]+)?)",
            r"(?:at most|no more than|max|maximum)\s*\$?\s*([0-9]+(?:\.[0-9]+)?)",
            r"under\s*\$?\s*([0-9]+(?:\.[0-9]+)?)",
            r"< \$?([0-9]+(?:\.[0-9]+)?)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    return {"max_price": float(match.group(1))}
                except:
                    pass
        return None
    
    # ============================================
    # NODE 2: ROUTER
    # ============================================
    
    def route_query(self, state: AgentState) -> Literal["product_search", "general_chat"]:
        """Route to appropriate node based on intent"""
        if state["is_product_query"]:
            return "product_search"
        return "general_chat"
    
    # ============================================
    # NODE 3: PRODUCT SEARCH
    # ============================================
    
    def search_products(self, state: AgentState) -> AgentState:
        """Search for products in vector store with intelligent ranking"""
        
        try:
            if self.vector_store is None:
                self._init_vector_store()
                if self.vector_store is None:
                    # Return sample products as fallback
                    state["products"] = self._get_fallback_products(state["user_input"])
                    state["tool_result"] = json.dumps({
                        "success": True,
                        "count": len(state["products"]),
                        "fallback": True
                    })
                    return state
            
            requested_count = state.get("requested_count", 4)
            
            # Detect query type for intelligent sorting
            user_input_lower = state["user_input"].lower()
            is_ranking_query = bool(re.search(r'(top|best|highest rated|popular|ranking|bestseller|trending)', user_input_lower))
            is_price_query = bool(re.search(r'(cheap|budget|affordable|under|below|less than)', user_input_lower))
            is_comparison_query = bool(re.search(r'(compare|versus|vs|difference)', user_input_lower))
            
            # Adjust fetch count
            if is_ranking_query:
                fetch_count = min(requested_count * 4, 40)
            elif is_comparison_query:
                fetch_count = min(requested_count * 3, 35)
            else:
                fetch_count = min(requested_count * 3, 30)
            
            # Enhance query for better search
            enhanced_query = user_input_lower
            if is_ranking_query:
                enhanced_query = f"{user_input_lower} bestseller popular top-rated"
            
            # Search with timeout protection
            results = self._search_with_timeout(enhanced_query, fetch_count)
            
            if not results:
                state["products"] = self._get_fallback_products(state["user_input"])
            else:
                products = self._process_search_results(results, is_ranking_query, is_price_query, is_comparison_query)
                
                # Apply price filter
                if state.get("price_filter"):
                    products = self._apply_price_filter(products, state["price_filter"])
                
                # Limit to requested count
                state["products"] = products[:requested_count]
            
            state["tool_result"] = json.dumps({
                "success": True,
                "count": len(state["products"]),
                "requested_count": requested_count
            })
            
            print(f"✅ Search complete: Found {len(state['products'])} products")
            
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            state["error"] = str(e)
            state["products"] = self._get_fallback_products(state["user_input"])
            state["tool_result"] = json.dumps({
                "success": False,
                "error": str(e),
                "fallback": True
            })
        
        return state
    
    def _search_with_timeout(self, query: str, k: int, timeout: int = 30):
        """Search with timeout protection"""
        import threading
        
        result = [None]
        error = [None]
        
        def search():
            try:
                result[0] = self.vector_store.similarity_search_with_score(query=query, k=k)
            except Exception as e:
                error[0] = e
        
        thread = threading.Thread(target=search)
        thread.start()
        thread.join(timeout=timeout)
        
        if thread.is_alive():
            print("⚠️ Search timeout, using fallback")
            return None
        
        if error[0]:
            print(f"⚠️ Search error: {error[0]}")
            return None
        
        return result[0]
    
    def _process_search_results(self, results, is_ranking_query, is_price_query, is_comparison_query):
        """Process and score search results"""
        products = []
        
        for doc, score in results:
            metadata = doc.metadata or {}
            
            match_percentage = self._calculate_match_score(score)
            
            # Parse rating
            rating_value = metadata.get("rating", 0)
            if isinstance(rating_value, str):
                try:
                    rating_value = float(rating_value)
                except:
                    rating_value = 0
            else:
                rating_value = float(rating_value) if rating_value else 0
            
            # Parse reviews
            reviews_count = metadata.get("reviews", 0)
            if isinstance(reviews_count, str):
                try:
                    reviews_count = int(reviews_count.replace(',', ''))
                except:
                    reviews_count = 0
            else:
                reviews_count = int(reviews_count) if reviews_count else 0
            
            # Parse price
            price_str = metadata.get("price", "N/A")
            price_value = self._extract_price_value(price_str) or 999999
            
            # Calculate ranking score
            normalized_reviews = min(reviews_count / 2000, 1)
            ranking_score = (
                (rating_value / 5) * 40 +
                normalized_reviews * 30 +
                (match_percentage / 100) * 20 +
                (1 if metadata.get("badge") in ["Bestseller", "Top Rated"] else 0) * 10
            )
            
            # Parse images
            images = metadata.get("images", [])
            if isinstance(images, str):
                try:
                    images = json.loads(images)
                except:
                    images = []
            
            product = {
                "name": metadata.get("name", "Unknown Product"),
                "price": price_str,
                "price_value": price_value,
                "link": metadata.get("link", ""),
                "description": metadata.get("description", "")[:500],
                "ingredients": metadata.get("ingredients", ""),
                "sku": metadata.get("sku", ""),
                "rating": rating_value,
                "rating_display": f"{rating_value:.1f}" if rating_value > 0 else "N/A",
                "reviews": reviews_count,
                "reviews_display": f"{reviews_count:,}" if reviews_count > 0 else "0",
                "images": images if isinstance(images, list) else [],
                "match_score": match_percentage,
                "ranking_score": ranking_score,
                "badge": metadata.get("badge", ""),
                "is_bestseller": metadata.get("badge") in ["Bestseller", "Top Rated"]
            }
            
            products.append(product)
        
        # Sort based on query type
        if is_ranking_query:
            products.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)
        elif is_price_query:
            products.sort(key=lambda x: x.get("price_value", 999999))
        elif is_comparison_query:
            products.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)
        else:
            products.sort(key=lambda x: (
                x.get("match_score", 0) * 0.7 + x.get("ranking_score", 0) * 0.3
            ), reverse=True)
        
        return products
    
    def _get_fallback_products(self, query: str) -> List[Dict]:
        """Return fallback products when search fails"""
        return [
            {
                "name": "King Arthur All-Purpose Flour",
                "price": "$6.95",
                "price_value": 6.95,
                "link": "https://www.kingarthurbaking.com/shop/all-purpose-flour",
                "description": "Premium all-purpose flour for all your baking needs.",
                "sku": "KA-APF-001",
                "rating": 4.8,
                "rating_display": "4.8",
                "reviews": 1247,
                "reviews_display": "1,247",
                "images": [],
                "match_score": 85,
                "ranking_score": 75,
                "badge": "Bestseller",
                "is_bestseller": True
            },
            {
                "name": "King Arthur Bread Flour",
                "price": "$7.95",
                "price_value": 7.95,
                "link": "https://www.kingarthurbaking.com/shop/bread-flour",
                "description": "High-protein flour for artisan breads and pizza.",
                "sku": "KA-BF-002",
                "rating": 4.7,
                "rating_display": "4.7",
                "reviews": 892,
                "reviews_display": "892",
                "images": [],
                "match_score": 80,
                "ranking_score": 70,
                "badge": "Popular",
                "is_bestseller": False
            },
            {
                "name": "King Arthur Cookie Mix",
                "price": "$8.95",
                "price_value": 8.95,
                "link": "https://www.kingarthurbaking.com/shop/cookie-mix",
                "description": "Delicious chocolate chip cookie mix.",
                "sku": "KA-CM-003",
                "rating": 4.6,
                "rating_display": "4.6",
                "reviews": 534,
                "reviews_display": "534",
                "images": [],
                "match_score": 75,
                "ranking_score": 65,
                "badge": "",
                "is_bestseller": False
            }
        ]
    
    def _extract_price_value(self, price_str: str) -> Optional[float]:
        """Extract numeric price from string"""
        if not price_str or price_str == "N/A":
            return None
        
        cleaned = re.sub(r"[^\d\.\-]", "", str(price_str))
        try:
            return float(cleaned)
        except:
            return None
    
    def _calculate_match_score(self, score: float) -> int:
        """Convert distance score to percentage"""
        try:
            if 0 <= score <= 1:
                return round((1.0 - score) * 100)
            return round(max(0, min(100, (1.0 - score / 100) * 100)))
        except:
            return 50
    
    def _apply_price_filter(self, products: List[Dict], price_filter: Dict) -> List[Dict]:
        """Apply price filtering to products"""
        max_price = price_filter.get("max_price")
        if not max_price:
            return products
        
        return [p for p in products if p.get("price_value") and p["price_value"] <= max_price]
    
    # ============================================
    # NODE 4: GENERAL CHAT
    # ============================================
    
    def general_chat(self, state: AgentState) -> AgentState:
        """Handle general baking questions"""
        
        prompt = f"""You are King Arthur Baking Assistant, a friendly and knowledgeable AI.

Current user question: {state["user_input"]}

Guidelines:
- Be warm, friendly, and conversational
- Keep responses concise (2-3 sentences)
- Focus on baking expertise
- If you don't know, say so politely
- Don't invent product information

Your response:"""

        try:
            response = self.llm.invoke(prompt)
            state["response"] = response.strip() if isinstance(response, str) else str(response).strip()
            
            if not state["response"]:
                state["response"] = "I'm here to help with your baking questions!"
                
        except Exception as e:
            print(f"❌ Ollama error: {str(e)}")
            state["response"] = self._get_friendly_error_message(str(e))
            state["error"] = str(e)
        
        return state
    
    def _format_previous_products(self, products: List[Dict]) -> str:
        """Format previous product results for context"""
        if not products:
            return "No previous product searches."
        
        context = "Previously found products:\n"
        for i, product in enumerate(products[:3], 1):
            context += f"{i}. {product['name']} - {product['price']}\n"
        return context
    
    # ============================================
    # NODE 5: FORMAT PRODUCT RESPONSE
    # ============================================
    
    def format_product_response(self, state: AgentState) -> AgentState:
        """Format product search results into natural language"""
        
        if state.get("error"):
            state["response"] = f"Sorry, I encountered an error: {state['error']}"
            return state
        
        products = state.get("products", [])
        requested_count = state.get("requested_count", len(products))
        
        # Handle count queries
        if self._is_count_query(state["user_input"]):
            count = len(products)
            state["response"] = f"I found {count} product{'s' if count != 1 else ''} matching your search."
            return state
        
        # Handle empty results
        if not products:
            if state.get("price_filter"):
                max_price = state["price_filter"]["max_price"]
                state["response"] = f"I couldn't find any products under ${max_price:.2f}. Would you like me to show you products at any price point?"
            else:
                state["response"] = "I couldn't find any products matching your search. Could you try different keywords?"
            return state
        
        # Generate response
        response_prompt = f"""Format these product search results naturally.

User query: "{state['user_input']}"

Products found ({len(products)} items):
{self._format_products_for_prompt(products)}

Guidelines:
- Mention top 2-3 products by name and price
- Keep response under 100 words
- Use bullet points for products
- Be helpful and concise

Response:"""

        try:
            response = self.llm.invoke(response_prompt)
            response_text = response.strip() if isinstance(response, str) else str(response).strip()
            state["response"] = response_text
        except Exception as e:
            print(f"⚠️ Formatting fallback: {str(e)}")
            state["response"] = self._fallback_format_response(products, state["user_input"])
        
        return state
    
    def _is_count_query(self, text: str) -> bool:
        """Check if query is asking for count"""
        count_phrases = [
            "how many", "count of", "number of", "total products",
            "how many products", "product count"
        ]
        return any(phrase in text.lower() for phrase in count_phrases)
    
    def _format_products_for_prompt(self, products: List[Dict]) -> str:
        """Format products for LLM prompt"""
        if not products:
            return "No products found."
        
        text = ""
        for i, product in enumerate(products[:5], 1):
            text += f"\n{i}. **{product['name']}**\n"
            text += f"   - Price: {product['price']}\n"
            text += f"   - Rating: {product.get('rating_display', 'N/A')}/5\n"
            text += f"   - Description: {product.get('description', '')[:150]}...\n"
        
        return text
    
    def _response_matches_products(self, response: str, products: List[Dict]) -> bool:
        """Check if response mentions actual products"""
        if not response or not products:
            return False
        
        lower_response = response.lower()
        for product in products[:3]:
            name = str(product.get("name", "")).lower()
            if name and name in lower_response:
                return True
        return False
    
    def _fallback_format_response(self, products: List[Dict], query: str) -> str:
        """Simple fallback response"""
        if not products:
            return "No products found."
        
        response = f"I found {len(products)} products matching your search:\n\n"
        for i, product in enumerate(products[:5], 1):
            response += f"{i}. **{product['name']}** - {product['price']}\n"
        
        return response
    
    def _get_friendly_error_message(self, error: str) -> str:
        """Return user-friendly error messages"""
        error_lower = error.lower()
        
        if "disconnected" in error_lower or "connection" in error_lower:
            return "⚠️ Connection lost. Please restart Ollama and try again."
        elif "timeout" in error_lower:
            return "⏱️ Taking too long. Please try again."
        else:
            return f"❌ Error: {error[:100]}\n\nPlease make sure Ollama is running with: `ollama run {self.model_name}`"
    
    # ============================================
    # BUILD LANGGRAPH WORKFLOW
    # ============================================
    
    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        workflow = StateGraph(AgentState)
        
        workflow.add_node("detect_intent", self.detect_intent)
        workflow.add_node("product_search", self.search_products)
        workflow.add_node("general_chat", self.general_chat)
        workflow.add_node("format_response", self.format_product_response)
        
        workflow.add_conditional_edges(
            "detect_intent",
            self.route_query,
            {
                "product_search": "product_search",
                "general_chat": "general_chat"
            }
        )
        
        workflow.add_edge("product_search", "format_response")
        workflow.add_edge("format_response", END)
        workflow.add_edge("general_chat", END)
        
        workflow.set_entry_point("detect_intent")
        
        return workflow
    
    # ============================================
    # RUN METHOD
    # ============================================
    
    def run(self, user_input: str) -> Dict[str, Any]:
        """Run the agent with user input"""
        
        try:
            initial_state: AgentState = {
                "user_input": user_input,
                "is_product_query": False,
                "tool_result": None,
                "response": "",
                "products": [],
                "error": None,
                "retry_count": 0,
                "price_filter": None,
                "requested_count": 0,
                "conversation_history": []
            }
            
            final_state = self.app.invoke(initial_state)
            
            return {
                "response": final_state.get("response", "No response generated."),
                "products": final_state.get("products", []),
                "requested_count": final_state.get("requested_count", 0)
            }
            
        except Exception as e:
            print(f"❌ Agent error: {str(e)}")
            return {
                "response": f"Sorry, I encountered an error: {str(e)}",
                "products": [],
                "requested_count": 0
            }


# ============================================
# MAIN EXECUTION
# ============================================

def main():
    """Main execution function"""
    print("=" * 60)
    print("🍞 KING ARTHUR BAKING ASSISTANT 🍰")
    print("=" * 60)
    
    try:
        agent = KingArthurAgent()
        
        print("\n💬 Ready! Try these queries:")
        print("   - 'show me chocolate cake mixes'")
        print("   - 'show me 3 cookie mixes'")
        print("   - 'compare cake mixes'")
        print("   - 'find cheap products under $20'")
        print("   - 'exit' to quit\n")
        
        while True:
            try:
                user_input = input("👤 You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['exit', 'quit', 'bye']:
                    print("\n🍪 Happy baking! Come back anytime!")
                    break
                
                print("\n🤖 Assistant: ", end="", flush=True)
                response = agent.run(user_input)
                print(response["response"])
                
                if response["products"]:
                    print(f"\n📦 Showing {len(response['products'])} products:")
                    for i, product in enumerate(response["products"][:5], 1):
                        print(f"   {i}. {product['name']} - {product['price']}")
                print()
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
                
    except Exception as e:
        print(f"\n❌ Failed to initialize agent: {str(e)}")


if __name__ == "__main__":
    main()