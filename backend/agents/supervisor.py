import os
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langgraph.graph.message import add_messages
from typing_extensions import Annotated, TypedDict

try:
    from .data_collector import data_collector_agent
    from .market_analyzer import market_analyzer_agent
    from .optimization_advisor import optimization_advisor_agent
except ImportError:
    from data_collector import data_collector_agent
    from market_analyzer import market_analyzer_agent
    from optimization_advisor import optimization_advisor_agent
# Load environment variables from project root
from dotenv import load_dotenv
import os
# Load from project root
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))

# State management for LangGraph workflow
class AnalysisState(TypedDict):
    messages: Annotated[List, add_messages]
    amazon_url: str
    main_product_data: Optional[str]
    competitor_data: Optional[List[str]]
    product_analysis: Optional[str]
    competitor_analysis: Optional[str]
    market_positioning: Optional[str]
    optimization_strategy: Optional[str]
    next_agent: Optional[str]
    session_id: Optional[str]

def create_supervisor_workflow():
    """Create a LangGraph-based supervisor workflow"""
    
    # Initialize the model
    model = ChatOpenAI(
        model="gpt-4o",
        api_key=os.getenv("OPENAI_API_KEY"),
        temperature=0.3
    )
    
    # Define agent nodes
    def data_collector_node(state: AnalysisState) -> AnalysisState:
        """Data collection agent node"""
        print("🔍 Data Collector Agent: Starting product data collection...")
        
        # Get the Amazon URL from state
        amazon_url = state.get("amazon_url", "")
        session_id = state.get("session_id")
        
        # Set session context for WebSocket notifications
        try:
            from .session_context import set_session_id
        except ImportError:
            from session_context import set_session_id
        
        if session_id:
            set_session_id(session_id)
            print(f"✅ Set session_id in context: {session_id}")
        
        # Invoke the data collector agent with clear completion criteria
        result = data_collector_agent.invoke({
            "messages": [{"role": "user", "content": f"""Analyze this Amazon product and collect competitor data: {amazon_url}

CRITICAL: Make sure to COMPLETE ALL STEPS before finishing:
1. Scrape the main product data
2. Generate relevant search keywords
3. Use amazon_search_sequential to find competitors
4. Scrape at least 3-5 competitor products
5. Format output with clear sections as specified

Do NOT finish until you have attempted to scrape competitor data. Even if scraping fails, include the attempt results."""}]
        })
        
        # Extract data from result - handle both dict and AIMessage objects
        if hasattr(result, 'get') and result.get("messages"):
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                final_message = last_message.content
            elif isinstance(last_message, dict):
                final_message = last_message.get("content", "")
            else:
                final_message = str(last_message)
        else:
            final_message = str(result)
        
        # Parse competitor data from the response
        competitor_data = []
        
        # Look for competitor data sections in the response
        if "Competitor Data:" in final_message:
            lines = final_message.split('\n')
            capturing = False
            current_competitor = ""
            
            for line in lines:
                if "Competitor Data:" in line:
                    capturing = True
                    continue
                elif capturing:
                    # Look for competitor separators or new sections
                    if line.strip().startswith('Competitor ') or "scraping result:" in line.lower():
                        if current_competitor:
                            competitor_data.append(current_competitor.strip())
                        current_competitor = line
                    elif capturing and line.strip():
                        current_competitor += "\n" + line
                    elif not line.strip() and current_competitor:
                        # Empty line might indicate end of competitor
                        continue
                    
                    # Stop capturing if we hit another major section
                    if any(x in line for x in ["Search Keywords", "OUTPUT FORMAT", "WORKFLOW"]):
                        if current_competitor:
                            competitor_data.append(current_competitor.strip())
                        break
            
            # Add the last competitor if exists
            if current_competitor and current_competitor not in competitor_data:
                competitor_data.append(current_competitor.strip())
        
        # If no structured competitor data found, try to extract from JSON-like structure
        if not competitor_data and "{" in final_message:
            import re
            # Look for JSON blocks that might contain competitor info
            json_blocks = re.findall(r'\{[^}]*"title"[^}]*\}', final_message)
            for block in json_blocks:
                try:
                    import json
                    data = json.loads(block)
                    if data.get('title') and data.get('success'):
                        title = data.get('title', 'Unknown')
                        price = data.get('price', 'N/A')
                        brand = data.get('brand', 'Unknown')
                        competitor_data.append(f"Product: {title} | Price: ${price} | Brand: {brand}")
                except:
                    continue
        
        # Validate that we have attempted competitor collection
        has_competitor_attempt = any([
            "Competitor Data:" in final_message,
            "competitor" in final_message.lower(),
            "search" in final_message.lower(),
            len(competitor_data) > 0
        ])
        
        if not has_competitor_attempt:
            print("⚠️ Data collector may not have completed competitor search - proceeding anyway")
        
        # Update state
        state["main_product_data"] = final_message
        state["competitor_data"] = competitor_data if competitor_data else ["No competitor data found"]
        state["next_agent"] = "market_analyzer"
        
        print(f"✅ Data collector completed - Found {len(competitor_data)} competitors")
        return state
    
    def market_analyzer_node(state: AnalysisState) -> AnalysisState:
        """Market analysis agent node"""
        print("📊 Market Analyzer Agent: Analyzing market position and competitors...")
        
        main_product_data = state.get("main_product_data", "")
        session_id = state.get("session_id")
        
        # Parse the product data if it's a JSON string
        try:
            if isinstance(main_product_data, str) and main_product_data.startswith('{'):
                import json
                product_dict = json.loads(main_product_data)
                product_summary = f"Product: {product_dict.get('title', 'Unknown')} | Price: ${product_dict.get('price', 'N/A')} | Brand: {product_dict.get('brand', 'Unknown')} | ASIN: {product_dict.get('asin', 'Unknown')}"
            else:
                product_summary = main_product_data
        except:
            product_summary = main_product_data
        
        # Get competitor data for the analysis
        competitor_data = state.get("competitor_data", [])
        
        # Debug logging
        print(f"🔍 Market analyzer - competitor_data count: {len(competitor_data)}")
        for i, comp in enumerate(competitor_data):
            print(f"   - competitor {i+1}: {comp[:100] if comp else 'None'}...")
        
        competitor_info = "\n\n".join([f"Competitor {i+1}:\n{data}" for i, data in enumerate(competitor_data) if data])
        
        # Debug what we're sending
        print(f"📝 Sending to market analyzer:")
        print(f"   - main product length: {len(main_product_data)}")
        print(f"   - competitor info length: {len(competitor_info)}")
        
        # Invoke the market analyzer agent with clear instructions
        result = market_analyzer_agent.invoke({
            "messages": [{"role": "user", "content": f"""Please perform a comprehensive market analysis:

1. First, use the product_analysis tool to analyze the main product's market position:
{main_product_data}

2. Then, use the competitor_analysis tool to compare the main product against these competitors:
Main Product:
{main_product_data}

Competitors:
{competitor_info if competitor_info else "No competitor data available"}

Make sure to call BOTH tools to provide separate analyses."""}],
            "session_id": session_id
        })
        
        # Extract messages from the agent's response
        product_analysis_result = None
        competitor_analysis_result = None
        
        if hasattr(result, 'get') and result.get("messages"):
            # Get all message content
            all_content = []
            for message in result["messages"]:
                if hasattr(message, 'content'):
                    all_content.append(message.content)
                elif isinstance(message, dict):
                    all_content.append(message.get("content", ""))
            
            # Join all content and look for our markers
            full_text = "\n".join(all_content)
            
            # Extract product analysis
            if "## Product Analysis" in full_text:
                parts = full_text.split("## Product Analysis", 1)
                if len(parts) > 1:
                    # Find the next section or end
                    product_part = parts[1]
                    if "## Competitor Analysis" in product_part:
                        product_analysis_result = product_part.split("## Competitor Analysis")[0].strip()
                    else:
                        product_analysis_result = product_part.strip()
            
            # Extract competitor analysis
            if "## Competitor Analysis" in full_text:
                parts = full_text.split("## Competitor Analysis", 1)
                if len(parts) > 1:
                    competitor_analysis_result = parts[1].strip()
            
            # Fallback if we didn't find the markers
            if not product_analysis_result and not competitor_analysis_result:
                # Use the last substantial message
                for message in reversed(result["messages"]):
                    content = ""
                    if hasattr(message, 'content'):
                        content = message.content
                    elif isinstance(message, dict):
                        content = message.get("content", "")
                    
                    if len(content) > 100:  # Skip short messages
                        product_analysis_result = content
                        competitor_analysis_result = "Competitor analysis not available - agent may not have called the competitor_analysis tool"
                        break
        
        # Validate that we have completed both analyses
        has_product_analysis = bool(product_analysis_result and len(product_analysis_result) > 50)
        has_competitor_analysis = bool(competitor_analysis_result and len(competitor_analysis_result) > 50)
        
        # Debug logging
        print(f"🔍 Market analyzer completion check:")
        print(f"   - Product analysis: {'✅' if has_product_analysis else '❌'} ({len(product_analysis_result or '')} chars)")
        print(f"   - Competitor analysis: {'✅' if has_competitor_analysis else '❌'} ({len(competitor_analysis_result or '')} chars)")
        
        if not has_product_analysis:
            print("⚠️ Product analysis appears incomplete or missing")
        if not has_competitor_analysis:
            print("⚠️ Competitor analysis appears incomplete or missing")
        
        # Update state with separated analyses
        state["product_analysis"] = product_analysis_result or "Product analysis not available"
        state["competitor_analysis"] = competitor_analysis_result or "Competitor analysis not available"
        state["next_agent"] = "optimization_advisor"
        
        print(f"✅ Market analyzer completed - Proceeding to optimization advisor")
        return state
    
    def optimization_advisor_node(state: AnalysisState) -> AnalysisState:
        """Optimization advisor agent node"""
        print("🎯 Optimization Advisor Agent: Generating optimization strategy...")
        
        product_analysis = state.get("product_analysis", "")
        competitor_analysis = state.get("competitor_analysis", "")
        main_product_data = state.get("main_product_data", "")
        session_id = state.get("session_id")
        
        # Debug logging
        print(f"🔍 Optimization advisor inputs:")
        print(f"   - Product analysis: {len(product_analysis)} chars")
        print(f"   - Competitor analysis: {len(competitor_analysis)} chars")
        print(f"   - Main product data: {len(main_product_data)} chars")
        
        # Validate we have analysis results to work with
        has_analyses = bool(product_analysis and competitor_analysis and 
                           len(product_analysis) > 50 and len(competitor_analysis) > 50)
        
        if not has_analyses:
            print("⚠️ Optimization advisor starting without complete market analysis")
        else:
            print("✅ Optimization advisor has complete market analysis data")
        
        # Include product data if analyses are empty
        if not product_analysis and not competitor_analysis:
            content = f"Create optimization recommendations for this product:\n{main_product_data}"
        else:
            content = f"Based on this analysis, create optimization recommendations:\n\nProduct Analysis:\n{product_analysis}\n\nCompetitor Analysis:\n{competitor_analysis}"
        
        # Invoke the optimization advisor agent
        result = optimization_advisor_agent.invoke({
            "messages": [{"role": "user", "content": content}],
            "session_id": session_id
        })
        
        # Extract strategy from result - handle both dict and AIMessage objects
        if hasattr(result, 'get') and result.get("messages"):
            last_message = result["messages"][-1]
            if hasattr(last_message, 'content'):
                final_message = last_message.content
            elif isinstance(last_message, dict):
                final_message = last_message.get("content", "")
            else:
                final_message = str(last_message)
        else:
            final_message = str(result)
        
        # Update state
        state["optimization_strategy"] = final_message
        state["next_agent"] = None  # Workflow complete
        
        return state
    
    def supervisor_node(state: AnalysisState) -> AnalysisState:
        """Supervisor node to coordinate workflow"""
        next_agent = state.get("next_agent")
        
        if not next_agent:
            # Workflow is complete
            return state
        
        print(f"👥 Supervisor: Directing workflow to {next_agent}")
        return state
    
    def route_to_agent(state: AnalysisState) -> str:
        """Route to the next agent based on state"""
        next_agent = state.get("next_agent")
        
        if next_agent == "data_collector":
            return "data_collector"
        elif next_agent == "market_analyzer":
            return "market_analyzer"
        elif next_agent == "optimization_advisor":
            return "optimization_advisor"
        else:
            return END
    
    # Create the graph
    workflow = StateGraph(AnalysisState)
    
    # Add nodes
    workflow.add_node("supervisor", supervisor_node)
    workflow.add_node("data_collector", data_collector_node)
    workflow.add_node("market_analyzer", market_analyzer_node)
    workflow.add_node("optimization_advisor", optimization_advisor_node)
    
    # Add edges
    workflow.add_edge("data_collector", "supervisor")
    workflow.add_edge("market_analyzer", "supervisor")
    workflow.add_edge("optimization_advisor", "supervisor")
    
    # Add conditional edges from supervisor
    workflow.add_conditional_edges(
        "supervisor",
        route_to_agent,
        {
            "data_collector": "data_collector",
            "market_analyzer": "market_analyzer", 
            "optimization_advisor": "optimization_advisor",
            END: END
        }
    )
    
    # Set entry point
    workflow.set_entry_point("supervisor")
    
    return workflow


def analyze_product(amazon_url: str, session_id: Optional[str] = None):
    """
    Analyze an Amazon product using the multi-agent workflow
    
    Args:
        amazon_url: The Amazon product URL to analyze
        session_id: Optional session ID for WebSocket updates
        
    Returns:
        Analysis results from all agents
    """
    # Create and compile the workflow
    workflow = create_supervisor_workflow().compile()
    
    # Initial state
    initial_state = {
        "messages": [],
        "amazon_url": amazon_url,
        "main_product_data": None,
        "competitor_data": None,
        "product_analysis": None,
        "competitor_analysis": None,
        "market_positioning": None,
        "optimization_strategy": None,
        "next_agent": "data_collector",  # Start with data collection
        "session_id": session_id
    }
    
    # Execute the workflow
    try:
        result = workflow.invoke(initial_state)
        
        # Format the final result
        return {
            "success": True,
            "amazon_url": amazon_url,
            "main_product_data": result.get("main_product_data"),
            "product_analysis": result.get("product_analysis"),
            "competitor_analysis": result.get("competitor_analysis"),
            "optimization_strategy": result.get("optimization_strategy"),
            "session_id": session_id
        }
    except Exception as e:
        print(f"Error in workflow execution: {e}")
        return {
            "success": False,
            "error": str(e),
            "amazon_url": amazon_url,
            "session_id": session_id
        }


# Example usage
if __name__ == "__main__":
    # Example product URL
    test_url = "https://www.amazon.com/Tamagotchi-Nano-Peanuts-Silicone-Case/dp/B0FB7FQWJL/?_encoding=UTF8&pd_rd_w=z2Ksk&content-id=amzn1.sym.0ee7ac10-1e05-43b4-8708-e2b0e6430ef1&pf_rd_p=0ee7ac10-1e05-43b4-8708-e2b0e6430ef1&pf_rd_r=CH7HD7239THZ01SHTZ6N&pd_rd_wg=2kLkB&pd_rd_r=9344b5f4-da0d-45b3-b124-2e19d8d944eb&ref_=pd_hp_d_btf_exports_top_sellers_unrec"
    
    print("Starting Amazon Product Analysis...")
    print(f"Analyzing: {test_url}")
    print("-" * 50)
    
    # Use the new supervisor
    result = analyze_product(test_url)
    print(result)