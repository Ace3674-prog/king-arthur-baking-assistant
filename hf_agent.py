import json
import os
import re
from typing import TypedDict, Optional, List, Dict, Any, Literal
from langgraph.graph import StateGraph, END
from langchain_huggingface import HuggingFacePipeline
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline
from scraper.chroma_store import get_chroma_retriever, get_chroma_vector_store
import streamlit as st

# ============================================
# STATE DEFINITION
# ============================================

class AgentState(TypedDict):
    user_input: str
    is_product_query: bool
    tool_result: Optional[str]
    response: str
    products: List[Dict[str, Any]]
    error: Optional[str]
    retry_count: int
    price_filter: Optional[Dict[str, float]]
    requested_count: int

# ============================================
# HUGGING FACE AGENT
# ============================================

class KingArthurAgent:
    
    def __init__(self):
        """Initialize the agent with Hugging Face model"""
        
        # Initialize Hugging Face model
        self._init_hf_model()
        
        # Initialize Chroma vector store
        self._init_vector_store()
        
        # Build LangGraph workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()
        
        print("✅ King Arthur Agent ready with Hugging Face!")
    
    def _init_hf_model(self):
        """Initialize Hugging Face model (CPU-friendly)"""
        try:
            model_name = "google/flan-t5-small"  # Small, fast CPU model
            
            @st.cache_resource
            def load_model():
                tokenizer = AutoTokenizer.from_pretrained(model_name)
                model = AutoModelForSeq2SeqLM.from_pretrained(model_name)
                pipe = pipeline(
                    "text2text-generation",
                    model=model,
                    tokenizer=tokenizer,
                    max_length=200,
                    temperature=0.3,
                    device=-1  # CPU
                )
                return HuggingFacePipeline(pipeline=pipe)
            
            self.llm = load_model()
            self.model_name = model_name
            print(f"✅ Hugging Face model loaded: {model_name}")
            
        except Exception as e:
            print(f"❌ Failed to load model: {str(e)}")
            self.llm = None
    
    def _init_vector_store(self):
        """Initialize Chroma vector store"""
        try:
            self.vector_store = get_chroma_vector_store()
            self.retriever = self.vector_store.as_retriever(
                search_type="similarity",
                search_kwargs={"k": 10}
            )
            print("✅ Chroma vector store initialized")
        except Exception as e:
            print(f"⚠️ Chroma error: {str(e)}")
            self.vector_store = None
            self.retriever = None
    
    # ============================================
    # INTENT DETECTION
    # ============================================
    
    def detect_intent(self, state: AgentState) -> AgentState:
        """Detect if query is product-related or general chat"""
        user_input = state["user_input"].lower().strip()
        
        product_keywords = [
            "mix", "flour", "ingredient", "cake", "bread", "cookie",
            "baking", "recommend", "show", "find", "price", "product",
            "how many", "count", "best", "cheap", "top", "rated"
        ]
        
        is_product_query = any(keyword in user_input for keyword in product_keywords)
        requested_count = self._parse_product_count_dynamic(user_input)
        price_filter = self._parse_price_filter(user_input)
        
        state["is_product_query"] = is_product_query
        state["requested_count"] = requested_count
        state["price_filter"] = price_filter
        
        return state
    
    def _parse_product_count_dynamic(self, text: str) -> int:
        """Parse product count from query"""
        if not isinstance(text, str):
            return 4
        
        text = text.lower()
        
        # Check for explicit numbers
        match = re.search(r'(\d{1,2})\s+(?:products|items)', text)
        if match:
            return max(1, min(int(match.group(1)), 20))
        
        # Natural language quantities
        if 'a few' in text:
            return 3
        if 'several' in text:
            return 5
        if 'many' in text:
            return 8
        if 'all' in text:
            return 10
        
        # Query type defaults
        if 'cheap' in text or 'under' in text:
            return 3
        if 'compare' in text:
            return 6
        if 'best' in text or 'top' in text:
            return 4
        
        # Default based on query length
        word_count = len(text.split())
        if word_count < 5:
            return 5
        return 4
    
    def _parse_price_filter(self, text: str) -> Optional[Dict[str, float]]:
        """Parse price filter from query"""
        text = text.lower()
        match = re.search(r'(?:under|below|less than)\s*\$?\s*(\d+(?:\.\d+)?)', text)
        if match:
            return {"max_price": float(match.group(1))}
        return None
    
    # ============================================
    # ROUTER
    # ============================================
    
    def route_query(self, state: AgentState) -> Literal["product_search", "general_chat"]:
        """Route to appropriate node"""
        return "product_search" if state["is_product_query"] else "general_chat"
    
    # ============================================
    # PRODUCT SEARCH
    # ============================================
    
    def search_products(self, state: AgentState) -> AgentState:
        """Search for products in vector store"""
        try:
            if self.vector_store is None:
                state["products"] = self._get_fallback_products()
                return state
            
            requested_count = state.get("requested_count", 4)
            
            # Search
            results = self.vector_store.similarity_search_with_score(
                query=state["user_input"],
                k=requested_count * 3
            )
            
            # Process results
            products = []
            for doc, score in results:
                metadata = doc.metadata or {}
                product = {
                    "name": metadata.get("name", "Unknown"),
                    "price": metadata.get("price", "N/A"),
                    "link": metadata.get("link", ""),
                    "description": metadata.get("description", "")[:200],
                    "rating": metadata.get("rating", 0),
                    "reviews": metadata.get("reviews", 0),
                    "images": metadata.get("images", [])
                }
                products.append(product)
            
            # Apply price filter
            if state.get("price_filter"):
                products = [p for p in products if self._extract_price_value(p["price"]) <= state["price_filter"]["max_price"]]
            
            state["products"] = products[:requested_count]
            state["tool_result"] = json.dumps({"success": True, "count": len(state["products"])})
            
        except Exception as e:
            print(f"❌ Search error: {str(e)}")
            state["error"] = str(e)
            state["products"] = self._get_fallback_products()
        
        return state
    
    def _get_fallback_products(self) -> List[Dict]:
        """Fallback products when search fails"""
        return [
            {"name": "King Arthur All-Purpose Flour", "price": "$6.95", "link": "#", "description": "Premium flour for all baking needs."},
            {"name": "King Arthur Bread Flour", "price": "$7.95", "link": "#", "description": "High-protein flour for artisan breads."},
            {"name": "King Arthur Cookie Mix", "price": "$8.95", "link": "#", "description": "Delicious chocolate chip cookie mix."}
        ]
    
    def _extract_price_value(self, price_str: str) -> float:
        """Extract numeric price"""
        if not price_str:
            return 999999
        match = re.search(r'(\d+(?:\.\d+)?)', str(price_str))
        return float(match.group(1)) if match else 999999
    
    # ============================================
    # GENERAL CHAT
    # ============================================
    
    def general_chat(self, state: AgentState) -> AgentState:
        """Handle general baking questions"""
        if self.llm is None:
            state["response"] = "I'm here to help with your baking questions!"
            return state
        
        prompt = f"Answer this baking question concisely: {state['user_input']}"
        
        try:
            response = self.llm.invoke(prompt)
            state["response"] = response if isinstance(response, str) else str(response)
        except Exception as e:
            state["response"] = "I'm here to help with your baking questions! What would you like to know?"
        
        return state
    
    # ============================================
    # FORMAT RESPONSE
    # ============================================
    
    def format_product_response(self, state: AgentState) -> AgentState:
        """Format product response"""
        products = state.get("products", [])
        
        if not products:
            state["response"] = "I couldn't find any products matching your search. Please try different keywords."
            return state
        
        response = f"I found {len(products)} products:\n\n"
        for i, p in enumerate(products[:5], 1):
            response += f"{i}. **{p['name']}** - {p['price']}\n"
            if p.get('description'):
                response += f"   {p['description'][:100]}...\n\n"
        
        state["response"] = response
        return state
    
    # ============================================
    # BUILD WORKFLOW
    # ============================================
    
    def _build_workflow(self) -> StateGraph:
        """Build LangGraph workflow"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("detect_intent", self.detect_intent)
        workflow.add_node("product_search", self.search_products)
        workflow.add_node("general_chat", self.general_chat)
        workflow.add_node("format_response", self.format_product_response)
        
        workflow.add_conditional_edges(
            "detect_intent",
            self.route_query,
            {"product_search": "product_search", "general_chat": "general_chat"}
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
        """Run the agent"""
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
                "requested_count": 0
            }
            
            final_state = self.app.invoke(initial_state)
            
            return {
                "response": final_state.get("response", "No response."),
                "products": final_state.get("products", []),
                "requested_count": final_state.get("requested_count", 0)
            }
            
        except Exception as e:
            return {"response": f"Error: {str(e)}", "products": [], "requested_count": 0}