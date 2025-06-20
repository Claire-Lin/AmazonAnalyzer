import os
from typing import Optional, Dict, Any, TypedDict, Annotated
from datetime import datetime
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

try:
    from .session_context import get_session_id
    from .websocket_utils import send_websocket_notification_sync
    from .data_collector import data_collector_agent
    from .market_analyzer import market_analyzer_agent
    from .optimization_advisor import optimization_advisor_agent
except ImportError:
    from session_context import get_session_id
    from websocket_utils import send_websocket_notification_sync
    from data_collector import data_collector_agent
    from market_analyzer import market_analyzer_agent
    from optimization_advisor import optimization_advisor_agent

# Load environment variables from project root
env_path = os.path.join(os.path.dirname(__file__), '..', '.env')
load_dotenv(env_path)
print(f"Supervisor OPENAI_API_KEY loaded: {'Yes' if os.getenv('OPENAI_API_KEY') else 'No'}")

# Import WebSocket manager for real-time updates
try:
    import sys
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from services.websocket_manager import websocket_manager
except ImportError:
    websocket_manager = None

# Initialize model
model = ChatOpenAI(
    model="gpt-4o",
    api_key=os.getenv("OPENAI_API_KEY"),
    temperature=0.1
)

# Define the state schema for the supervisor workflow
class SupervisorState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]
    product_url: str
    session_id: Optional[str]
    collected_data: Optional[str]
    market_analysis: Optional[str]
    optimization_results: Optional[str]
    workflow_status: str
    current_phase: str
    error_message: Optional[str]

class AmazonAnalysisSupervisor:
    """
    LangGraph-based supervisor agent that orchestrates the complete Amazon product analysis workflow.
    
    Workflow:
    1. Data Collection: data_collector_agent
    2. Market Analysis: market_analyzer_agent  
    3. Optimization Advisory: optimization_advisor_agent
    """
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or get_session_id()
        self.graph = self._build_graph()
    
    def _send_notification(self, session_id: str, status: str, progress: float, 
                          current_task: str, thinking_step: str = "", error_message: str = ""):
        """Send WebSocket notification if available"""
        if websocket_manager and session_id:
            try:
                send_websocket_notification_sync(
                    websocket_manager=websocket_manager,
                    session_id=session_id,
                    agent_name="supervisor",
                    status=status,
                    progress=progress,
                    current_task=current_task,
                    thinking_step=thinking_step,
                    error_message=error_message
                )
            except Exception as e:
                print(f"WebSocket notification failed: {e}")
    
    
    def data_collection_node(self, state: SupervisorState) -> SupervisorState:
        """Node 1: Data Collection Phase"""
        print("="*80)
        print("PHASE 1: DATA COLLECTION")
        print("="*80)
        
        session_id = state.get("session_id", self.session_id)
        product_url = state["product_url"]
        
        self._send_notification(
            session_id=session_id,
            status="working",
            progress=0.1,
            current_task="Starting data collection",
            thinking_step=f"Analyzing product: {product_url}"
        )
        
        try:
            print(f"Collecting data for: {product_url}")
            
            # Run data collector agent
            agent_response = data_collector_agent.invoke({
                "messages": [{"role": "user", "content": product_url}]
            })
            
            # Extract the final message content
            collected_data = ""
            if agent_response and "messages" in agent_response:
                for msg in agent_response["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        collected_data = msg.content
            
            if collected_data:
                self._send_notification(
                    session_id=session_id,
                    status="working",
                    progress=0.33,
                    current_task="Data collection complete",
                    thinking_step="Successfully collected main product and competitor data"
                )
                print(f"✅ Data collection successful ({len(collected_data)} characters)")
                
                return {
                    **state,
                    "collected_data": collected_data,
                    "current_phase": "data_collection_complete",
                    "workflow_status": "data_collection_success"
                }
            else:
                raise Exception("No data collected from data_collector_agent")
                
        except Exception as e:
            error_msg = f"Data collection failed: {str(e)}"
            print(f"❌ {error_msg}")
            self._send_notification(
                session_id=session_id,
                status="error",
                progress=0.0,
                current_task="Data collection failed",
                error_message=error_msg
            )
            
            return {
                **state,
                "current_phase": "data_collection_failed",
                "workflow_status": "failed",
                "error_message": error_msg
            }
    
    def market_analysis_node(self, state: SupervisorState) -> SupervisorState:
        """Node 2: Market Analysis Phase"""
        print("\n" + "="*80)
        print("PHASE 2: MARKET ANALYSIS")
        print("="*80)
        
        session_id = state.get("session_id", self.session_id)
        collected_data = state["collected_data"]
        
        self._send_notification(
            session_id=session_id,
            status="working",
            progress=0.4,
            current_task="Starting market analysis",
            thinking_step="Analyzing product positioning and competitive landscape"
        )
        
        try:
            print("Running market analysis...")
            
            # Prepare clear instructions for market analyzer
            analysis_instruction = f"""
Please perform comprehensive market analysis on the following data:

1. First, call product_analysis tool with the main product data
2. Then, call competitor_analysis tool with main product and competitor data

Data to analyze:
{collected_data}

Please execute both analysis tools to provide complete market insights.
"""
            
            # Run market analyzer agent
            agent_response = market_analyzer_agent.invoke({
                "messages": [{"role": "user", "content": analysis_instruction}]
            })
            
            # Extract the final message content
            market_analysis = ""
            if agent_response and "messages" in agent_response:
                for msg in agent_response["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        market_analysis = msg.content
            
            if market_analysis:
                self._send_notification(
                    session_id=session_id,
                    status="working",
                    progress=0.66,
                    current_task="Market analysis complete",
                    thinking_step="Generated product and competitor analysis"
                )
                print(f"✅ Market analysis successful ({len(market_analysis)} characters)")
                
                return {
                    **state,
                    "market_analysis": market_analysis,
                    "current_phase": "market_analysis_complete",
                    "workflow_status": "market_analysis_success"
                }
            else:
                raise Exception("No analysis results from market_analyzer_agent")
                
        except Exception as e:
            error_msg = f"Market analysis failed: {str(e)}"
            print(f"❌ {error_msg}")
            self._send_notification(
                session_id=session_id,
                status="error",
                progress=0.33,
                current_task="Market analysis failed",
                error_message=error_msg
            )
            
            return {
                **state,
                "current_phase": "market_analysis_failed",
                "workflow_status": "failed",
                "error_message": error_msg
            }
    
    def optimization_advisory_node(self, state: SupervisorState) -> SupervisorState:
        """Node 3: Optimization Advisory Phase"""
        print("\n" + "="*80)
        print("PHASE 3: OPTIMIZATION ADVISORY")
        print("="*80)
        
        session_id = state.get("session_id", self.session_id)
        collected_data = state["collected_data"]
        market_analysis = state["market_analysis"]
        
        self._send_notification(
            session_id=session_id,
            status="working",
            progress=0.7,
            current_task="Starting optimization advisory",
            thinking_step="Generating positioning and optimization strategies"
        )
        
        try:
            print("Running optimization advisory...")
            
            # Prepare comprehensive input for optimization advisor
            optimization_input = f"""
Please provide comprehensive optimization recommendations based on the following:

COLLECTED PRODUCT DATA:
{collected_data}

MARKET ANALYSIS RESULTS:
{market_analysis}

Please use both tools:
1. market_positioning - to develop strategic positioning recommendations
2. product_optimizer - to create specific optimization strategies

Focus on actionable recommendations for Amazon marketplace success.
"""
            
            # Run optimization advisor agent
            agent_response = optimization_advisor_agent.invoke({
                "messages": [{"role": "user", "content": optimization_input}]
            })
            
            # Extract the final message content
            optimization_results = ""
            if agent_response and "messages" in agent_response:
                for msg in agent_response["messages"]:
                    if hasattr(msg, 'content') and msg.content:
                        optimization_results = msg.content
            
            if optimization_results:
                self._send_notification(
                    session_id=session_id,
                    status="completed",
                    progress=1.0,
                    current_task="Complete analysis finished",
                    thinking_step="Successfully generated optimization recommendations"
                )
                print(f"✅ Optimization advisory successful ({len(optimization_results)} characters)")
                
                return {
                    **state,
                    "optimization_results": optimization_results,
                    "current_phase": "optimization_complete",
                    "workflow_status": "completed"
                }
            else:
                raise Exception("No optimization results from optimization_advisor_agent")
                
        except Exception as e:
            error_msg = f"Optimization advisory failed: {str(e)}"
            print(f"❌ {error_msg}")
            self._send_notification(
                session_id=session_id,
                status="error",
                progress=0.66,
                current_task="Optimization advisory failed",
                error_message=error_msg
            )
            
            return {
                **state,
                "current_phase": "optimization_failed",
                "workflow_status": "failed",
                "error_message": error_msg
            }
    
    def should_continue_after_data_collection(self, state: SupervisorState) -> str:
        """Conditional edge: decide whether to continue after data collection"""
        if state["workflow_status"] == "data_collection_success":
            return "market_analysis_node"
        else:
            return END
    
    def should_continue_after_market_analysis(self, state: SupervisorState) -> str:
        """Conditional edge: decide whether to continue after market analysis"""
        if state["workflow_status"] == "market_analysis_success":
            return "optimization_advisory_node"
        else:
            return END
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow"""
        
        # Create the graph
        workflow = StateGraph(SupervisorState)
        
        # Add nodes (avoid conflicts with state keys)
        workflow.add_node("data_collection_node", self.data_collection_node)
        workflow.add_node("market_analysis_node", self.market_analysis_node)
        workflow.add_node("optimization_advisory_node", self.optimization_advisory_node)
        
        # Add edges
        workflow.add_edge(START, "data_collection_node")
        workflow.add_conditional_edges(
            "data_collection_node",
            self.should_continue_after_data_collection
        )
        workflow.add_conditional_edges(
            "market_analysis_node", 
            self.should_continue_after_market_analysis
        )
        workflow.add_edge("optimization_advisory_node", END)
        
        # Compile the graph
        return workflow.compile()
    
    def run_analysis(self, product_url: str) -> Dict[str, Any]:
        """Run the complete analysis workflow using LangGraph"""
        print("AMAZON PRODUCT ANALYSIS SUPERVISOR (LangGraph)")
        print("="*80)
        print(f"Product URL: {product_url}")
        print(f"Session ID: {self.session_id}")
        print("="*80)
        
        # Initialize state
        initial_state = {
            "messages": [],
            "product_url": product_url,
            "session_id": self.session_id,
            "collected_data": None,
            "market_analysis": None,
            "optimization_results": None,
            "workflow_status": "initialized",
            "current_phase": "starting",
            "error_message": None
        }
        
        self._send_notification(
            session_id=self.session_id,
            status="working",
            progress=0.0,
            current_task="Initializing analysis",
            thinking_step="Starting complete Amazon product analysis workflow"
        )
        
        # Run the workflow
        final_state = self.graph.invoke(initial_state)
        
        # Final summary
        print("\n" + "="*80)
        print("WORKFLOW COMPLETION SUMMARY")
        print("="*80)
        
        phase1_success = final_state.get('collected_data') is not None
        phase2_success = final_state.get('market_analysis') is not None  
        phase3_success = final_state.get('optimization_results') is not None
        
        print(f"✅ Phase 1 (Data Collection): {'SUCCESS' if phase1_success else 'FAILED'}")
        print(f"✅ Phase 2 (Market Analysis): {'SUCCESS' if phase2_success else 'FAILED'}")
        print(f"✅ Phase 3 (Optimization): {'SUCCESS' if phase3_success else 'FAILED'}")
        print(f"🔄 Final Status: {final_state.get('workflow_status', 'unknown')}")
        
        if final_state.get('error_message'):
            print(f"❌ Error: {final_state['error_message']}")
        
        if phase1_success and phase2_success and phase3_success:
            print("\n🎉 COMPLETE WORKFLOW SUCCESS!")
        
        return final_state
    
    def get_final_report(self, state: Dict[str, Any]) -> str:
        """Generate a comprehensive final report from the workflow state"""
        if state.get('workflow_status') != 'completed':
            return f"Analysis incomplete. Status: {state.get('workflow_status', 'unknown')}"
        
        timestamp = str(datetime.now())
        
        report = f"""
# Amazon Product Analysis Report (LangGraph Workflow)
Generated: {timestamp}
Session: {state.get('session_id', 'unknown')}
Product URL: {state.get('product_url', 'unknown')}

## Executive Summary
Complete analysis workflow executed successfully using LangGraph:
- Data Collection ✅
- Market Analysis ✅ 
- Optimization Advisory ✅

## Phase 1: Data Collection Results
{state.get('collected_data', 'No data')[:1000]}...

## Phase 2: Market Analysis Results  
{state.get('market_analysis', 'No analysis')[:1000]}...

## Phase 3: Optimization Recommendations
{state.get('optimization_results', 'No recommendations')[:1000]}...

---
Report generated by LangGraph Amazon Analysis Supervisor
"""
        return report

# Create supervisor instance
def create_supervisor(session_id: Optional[str] = None) -> AmazonAnalysisSupervisor:
    """Create a new LangGraph supervisor instance"""
    return AmazonAnalysisSupervisor(session_id=session_id)

# Convenience function for direct use
def run_complete_amazon_analysis(product_url: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Run complete Amazon product analysis workflow using LangGraph
    
    Args:
        product_url: Amazon product URL to analyze
        session_id: Optional session ID for tracking
    
    Returns:
        Dictionary with final workflow state
    """
    supervisor = create_supervisor(session_id)
    return supervisor.run_analysis(product_url)

# Main function for testing
def main():
    """Test the LangGraph supervisor with example URL"""
    test_url = "https://www.amazon.com/dp/B08SWDN5FS/ref=sspa_dk_detail_0?pd_rd_i=B08SWDN5FS&pd_rd_w=7ooYl&content-id=amzn1.sym.953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_p=953c7d66-4120-4d22-a777-f19dbfa69309&pf_rd_r=QB4D7523XBB2S2P11T3F&pd_rd_wg=eG4PU&pd_rd_r=92e66331-65b5-401b-99e2-b3cb92faefd6&s=toys-and-games&sp_csd=d2lkZ2V0TmFtZT1zcF9kZXRhaWwy&th=1"
    
    supervisor = create_supervisor()
    final_state = supervisor.run_analysis(test_url)
    
    # Display final report
    print("\n" + "="*80)
    print("FINAL REPORT")
    print("="*80)
    report = supervisor.get_final_report(final_state)
    print(report)
    
    return final_state

# Export function for main.py compatibility
def analyze_product(product_url: str, session_id: Optional[str] = None) -> Dict[str, Any]:
    """
    Main entry point for product analysis - compatible with main.py
    
    Args:
        product_url: Amazon product URL to analyze
        session_id: Optional session ID for tracking
    
    Returns:
        Dictionary with analysis results
    """
    try:
        supervisor = create_supervisor(session_id)
        final_state = supervisor.run_analysis(product_url)
        
        # Check if workflow completed successfully
        if final_state.get('workflow_status') == 'completed':
            return {
                "success": True,
                "session_id": session_id,
                "product_url": product_url,
                "data_collection": final_state.get('collected_data'),
                "market_analysis": final_state.get('market_analysis'),
                "optimization_results": final_state.get('optimization_results'),
                "final_report": supervisor.get_final_report(final_state)
            }
        else:
            return {
                "success": False,
                "error": final_state.get('error_message', 'Analysis workflow failed'),
                "session_id": session_id,
                "product_url": product_url,
                "workflow_status": final_state.get('workflow_status')
            }
    except Exception as e:
        return {
            "success": False,
            "error": f"Analysis execution failed: {str(e)}",
            "session_id": session_id,
            "product_url": product_url
        }

if __name__ == "__main__":
    main()