import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict
from models import ChatSession, ChatMessage, KnowledgeBase, Farm, Crop, Livestock, db

class AgentState(TypedDict):
    """State for the agricultural AI agent."""
    messages: List[Any]
    user_id: Optional[int]
    session_id: Optional[str]
    context: Dict[str, Any]
    farm_data: Optional[Dict[str, Any]]

class MkulimaLLMService:
    """LLM service for Mkulima Smart agricultural assistance."""
    
    def __init__(self, config):
        self.config = config
        self.llm = self._initialize_llm()
        self.graph = self._build_agent_graph()
        
    def _initialize_llm(self):
        """Initialize the OpenAI LLM."""
        if not self.config.OPENAI_API_KEY:
            raise ValueError("OpenAI API key not found in configuration")
        
        return ChatOpenAI(
            api_key=self.config.OPENAI_API_KEY,
            model="gpt-4o-mini",
            temperature=0.7,
            max_tokens=1000
        )
    
    def _build_agent_graph(self):
        """Build the LangGraph agent for agricultural assistance."""
        
        def analyze_query(state: AgentState) -> AgentState:
            """Analyze the user query and determine the type of assistance needed."""
            messages = state["messages"]
            last_message = messages[-1] if messages else None
            
            if not last_message:
                return state
            
            # Analyze query type (crop advice, livestock, weather, general farming)
            query_analysis_prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an agricultural AI assistant. Analyze the user's query and categorize it.
                Categories: crop_management, livestock_care, weather_advice, pest_disease, soil_management, general_farming, market_prices
                
                Respond with JSON format:
                {
                    "category": "category_name",
                    "confidence": 0.8,
                    "requires_farm_data": true/false,
                    "specific_crop_livestock": "name if mentioned"
                }"""),
                ("human", "{query}")
            ])
            
            try:
                analysis_response = self.llm.invoke(
                    query_analysis_prompt.format(query=last_message.content)
                )
                analysis = json.loads(analysis_response.content)
                state["context"]["query_analysis"] = analysis
            except Exception as e:
                # Fallback to general farming if analysis fails
                state["context"]["query_analysis"] = {
                    "category": "general_farming",
                    "confidence": 0.5,
                    "requires_farm_data": False
                }
            
            return state
        
        def fetch_context_data(state: AgentState) -> AgentState:
            """Fetch relevant context data based on query analysis."""
            analysis = state["context"].get("query_analysis", {})
            user_id = state.get("user_id")
            
            context_data = {}
            
            if user_id and analysis.get("requires_farm_data"):
                # Fetch user's farm data
                farms = Farm.query.filter_by(user_id=user_id).all()
                context_data["farms"] = [
                    {
                        "name": farm.name,
                        "location": farm.location,
                        "size_acres": farm.size_acres,
                        "farm_type": farm.farm_type,
                        "crops": [{"name": crop.name, "variety": crop.variety, "status": crop.status} 
                                for crop in farm.crops],
                        "livestock": [{"animal_type": ls.animal_type, "breed": ls.breed, "count": ls.count} 
                                    for ls in farm.livestock]
                    }
                    for farm in farms
                ]
            
            # Fetch relevant knowledge base articles
            category = analysis.get("category", "general_farming")
            kb_articles = KnowledgeBase.query.filter(
                KnowledgeBase.category.like(f"%{category}%"),
                KnowledgeBase.is_active == True
            ).limit(3).all()
            
            context_data["knowledge_base"] = [
                {
                    "title": article.title,
                    "content": article.content[:500] + "..." if len(article.content) > 500 else article.content,
                    "category": article.category
                }
                for article in kb_articles
            ]
            
            state["context"]["data"] = context_data
            return state
        
        def generate_response(state: AgentState) -> AgentState:
            """Generate the AI response based on context and query."""
            messages = state["messages"]
            context = state["context"]
            
            # Build system prompt with context
            system_prompt = self._build_system_prompt(context)
            
            # Prepare conversation history
            conversation_messages = [SystemMessage(content=system_prompt)]
            for msg in messages[-5:]:  # Keep last 5 messages for context
                conversation_messages.append(msg)
            
            # Generate response
            response = self.llm.invoke(conversation_messages)
            
            # Add AI response to messages
            state["messages"] = add_messages(state["messages"], [response])
            
            return state
        
        def save_conversation(state: AgentState) -> AgentState:
            """Save the conversation to database."""
            try:
                session_id = state.get("session_id")
                user_id = state.get("user_id")
                
                if session_id and user_id:
                    # Get or create chat session
                    chat_session = ChatSession.query.filter_by(session_id=session_id).first()
                    if not chat_session:
                        chat_session = ChatSession(
                            session_id=session_id,
                            user_id=user_id,
                            title=self._generate_session_title(state["messages"])
                        )
                        db.session.add(chat_session)
                        db.session.flush()
                    
                    # Save the last two messages (user and AI)
                    recent_messages = state["messages"][-2:]
                    for msg in recent_messages:
                        message_type = "user" if isinstance(msg, HumanMessage) else "assistant"
                        chat_message = ChatMessage(
                            session_id=chat_session.id,
                            message_type=message_type,
                            content=msg.content,
                            metadata=json.dumps(state["context"]) if message_type == "assistant" else None
                        )
                        db.session.add(chat_message)
                    
                    db.session.commit()
            except Exception as e:
                print(f"Error saving conversation: {e}")
                db.session.rollback()
            
            return state
        
        # Build the graph
        workflow = StateGraph(AgentState)
        
        # Add nodes
        workflow.add_node("analyze_query", analyze_query)
        workflow.add_node("fetch_context", fetch_context_data)
        workflow.add_node("generate_response", generate_response)
        workflow.add_node("save_conversation", save_conversation)
        
        # Add edges
        workflow.set_entry_point("analyze_query")
        workflow.add_edge("analyze_query", "fetch_context")
        workflow.add_edge("fetch_context", "generate_response")
        workflow.add_edge("generate_response", "save_conversation")
        workflow.add_edge("save_conversation", END)
        
        return workflow.compile()
    
    def _build_system_prompt(self, context: Dict[str, Any]) -> str:
        """Build system prompt with context data."""
        base_prompt = """You are Mkulima AI, an expert agricultural assistant specializing in smart farming practices in Kenya and East Africa. 
        
        Your expertise includes:
        - Crop management and cultivation techniques
        - Livestock care and animal husbandry
        - Pest and disease identification and management
        - Soil health and fertilization
        - Weather-based farming advice
        - Market prices and agricultural economics
        - Sustainable farming practices
        
        Always provide practical, actionable advice suitable for small to medium-scale farmers.
        Use simple language and explain technical terms when necessary.
        Consider local conditions, climate, and available resources in your recommendations."""
        
        # Add context data if available
        context_data = context.get("data", {})
        
        if context_data.get("farms"):
            base_prompt += f"\n\nUser's Farm Information:\n{json.dumps(context_data['farms'], indent=2)}"
        
        if context_data.get("knowledge_base"):
            base_prompt += f"\n\nRelevant Knowledge Base Articles:\n"
            for article in context_data["knowledge_base"]:
                base_prompt += f"- {article['title']}: {article['content']}\n"
        
        return base_prompt
    
    def _generate_session_title(self, messages: List[Any]) -> str:
        """Generate a title for the chat session based on the first user message."""
        if not messages:
            return "New Chat Session"
        
        first_user_message = None
        for msg in messages:
            if isinstance(msg, HumanMessage):
                first_user_message = msg.content
                break
        
        if first_user_message:
            # Truncate and clean up for title
            title = first_user_message[:50].strip()
            if len(first_user_message) > 50:
                title += "..."
            return title
        
        return "New Chat Session"
    
    def chat(self, message: str, user_id: int, session_id: str) -> Dict[str, Any]:
        """Main chat interface."""
        try:
            # Create initial state
            initial_state = AgentState(
                messages=[HumanMessage(content=message)],
                user_id=user_id,
                session_id=session_id,
                context={},
                farm_data=None
            )
            
            # Run the agent
            result = self.graph.invoke(initial_state)
            
            # Extract the AI response
            ai_message = result["messages"][-1]
            
            return {
                "success": True,
                "response": ai_message.content,
                "session_id": session_id,
                "context": result["context"]
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error processing your request. Please try again."
            }
    
    def get_chat_history(self, session_id: str) -> List[Dict[str, Any]]:
        """Retrieve chat history for a session."""
        try:
            chat_session = ChatSession.query.filter_by(session_id=session_id).first()
            if not chat_session:
                return []
            
            messages = ChatMessage.query.filter_by(session_id=chat_session.id)\
                                      .order_by(ChatMessage.timestamp.asc()).all()
            
            return [
                {
                    "type": msg.message_type,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": json.loads(msg.metadata) if msg.metadata else None
                }
                for msg in messages
            ]
            
        except Exception as e:
            print(f"Error retrieving chat history: {e}")
            return []
