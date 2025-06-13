import asyncio
from typing import Optional
from contextlib import AsyncExitStack

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

class MCPClient:
    def __init__(self):
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic()
        # Add state management
        self.last_forecast = None
        self.conversation_history = []
        logger.info("MCPClient initialized")
        

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP Server"""
        logger.info(f"Connecting to server script: {server_script_path}")
        
        is_python = server_script_path.endswith('.py')
        is_js = server_script_path.endswith('.js')
        
        if not (is_python or is_js):
            raise ValueError("Server script must be a .py or .js file")
        
        command = "python" if is_python else "node"
        server_params = StdioServerParameters(
            command = command,
            args = [server_script_path],
            env = None
        )
        
        
        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
        self.stdio, self.write = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))
        
        await self.session.initialize()
        
        response = await self.session.list_tools()
        tools = response.tools
        logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
        
        
    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        # Skip empty queries
        if not query.strip():
            return "Please provide a query or type 'quit' to exit."
            
        logger.debug(f"Processing query: {query}")
        
        # Add the query to conversation history
        self.conversation_history.append({"role": "user", "content": query})
        
        response = await self.session.list_tools()
        
        available_tools = [{
            "name": tool.name,
            "description": tool.description,
            "input_schema": tool.inputSchema
        } for tool in response.tools
        ] 
        logger.debug(f"Available tools: {available_tools}")
        
        try:
            response = self.anthropic.messages.create(
                model = "claude-3-5-sonnet-20241022",
                max_tokens = 1000,
                messages = self.conversation_history,
                tools=available_tools
            )
            
            # Initialize assistant's message content
            assistant_content = []
            
            for content in response.content:
                if content.type == 'text':
                    assistant_content.append({
                        "type": "text",
                        "text": content.text
                    })
                elif content.type == 'tool_use':
                    tool_name = content.name
                    tool_args = content.input
                    logger.debug(f"Using tool: {tool_name} with args: {tool_args}")
                    
                    result = await self.session.call_tool(tool_name, tool_args)
                    
                    # Store forecast data if this was a forecast request
                    if tool_name == 'get_forecast' and result.content:
                        self.last_forecast = result.content
                        logger.info("Stored forecast data for future reference")
                        # Extract text content from forecast result (handling list of TextContent)
                        forecast_text = result.content[0].text if result.content and hasattr(result.content[0], 'text') else str(result.content)
                        # Add the forecast to the assistant's content
                        assistant_content.append({
                            "type": "text",
                            "text": forecast_text
                        })
                    
                    # If this was a forecast request, automatically get outfit recommendations
                    if tool_name == 'get_forecast' and result.content:
                        logger.info("Getting outfit recommendations based on forecast")
                        
                        # Pass the forecast data directly as a string
                        forecast_text = result.content[0].text if result.content and hasattr(result.content[0], 'text') else str(result.content)
                        
                        outfit_result = await self.session.call_tool('get_outfit', {'forecast_data': forecast_text})
                        # Extract text content from outfit result (handling list of TextContent)
                        outfit_text = outfit_result.content[0].text if outfit_result.content and hasattr(outfit_result.content[0], 'text') else str(outfit_result.content)
                        # Add the outfit recommendations to the assistant's content
                        assistant_content.append({
                            "type": "text",
                            "text": f"\n[Getting outfit recommendations based on the forecast]\n{outfit_text}"
                        })
                    
                    # Add tool use to assistant's content (but not the raw result)
                    assistant_content.append({
                        "type": "tool_use",
                        "name": tool_name,
                        "input": tool_args
                    })
            
            # Add the complete assistant response to conversation history
            self.conversation_history.append({
                "role": "assistant",
                "content": assistant_content
            })
            
            # Extract the final text from the assistant's content
            final_text = []
            for content in assistant_content:
                if isinstance(content, dict) and content.get("type") == "text":
                    final_text.append(content["text"])
            
            return "\n".join(final_text) if final_text else "I apologize, but I didn't receive a proper response. Please try again."
            
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return f"Error: {str(e)}"
    
    
    async def chat_loop(self):
        """Run an interactive chat loop"""
        logger.info("Starting chat loop")
        logger.info("Type your queries or 'quit' to exit.")
        
        while True:
            try:
                query = input("\nQuery: ").strip()
                
                if query.lower() == 'quit':
                    logger.info("User requested to quit")
                    break
                
                response = await self.process_query(query)
                print("\n" + response)
                
            except Exception as e:
                logger.error(f"Error in chat loop: {str(e)}", exc_info=True)
                print(f"\nError: {str(e)}")
                
    async def cleanup(self):
        """Clean up resources"""
        logger.info("Cleaning up resources")
        await self.exit_stack.aclose()
        
        
async def main():
    """Initialize and run the MCP client with the provided server script path."""
    if len(sys.argv) < 2:
        logger.error("No server script path provided")
        print("usage: python client.py <path_to_server_script>")
        sys.exit(1)
        
    client = MCPClient()
    
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    finally:
        await client.cleanup()
        
if __name__ == "__main__":
    import sys
    asyncio.run(main())
    