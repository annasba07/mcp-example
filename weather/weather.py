from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import logging
import os
import anthropic
from dotenv import load_dotenv
from pathlib import Path

# Get the weather directory (where .env should be)
weather_dir = Path(__file__).parent
env_path = weather_dir / '.env'

# Load environment variables from weather directory
load_dotenv(env_path)
logger = logging.getLogger(__name__)

# Configure logging to file
log_file = os.path.join(os.path.dirname(__file__), 'weather_server.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # append mode
)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

# Log the environment file path for debugging
logger.debug(f"Looking for .env file at: {env_path}")
if env_path.exists():
    logger.debug("Found .env file")
else:
    logger.warning(f".env file not found at {env_path}")

mcp = FastMCP("weather")



# Constants
NWS_API_BASE = "https://api.weather.gov"
USER_AGENT = "weather-app/1.0"


async def make_nws_request(url: str) -> dict[str, Any] | None:
    """Make a request to be the NWS API with proper error handling"""
    logger.debug(f"Making NWS request to: {url}")
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/geo+json"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url, headers=headers, timeout = 30.0)
            response.raise_for_status()
            logger.debug(f"Successful response from NWS API: {response.status_code}")
            return response.json()
        except Exception as e:
            logger.error(f"Error making NWS request: {str(e)}", exc_info=True)
            return None
        

def format_alert(feature: dict) -> str:
    """Format an alert feature into a readable string."""
    try:
        props = feature["properties"]
        return f"""

Event: {props.get('event', 'Unknown')}
Area: {props.get('areaDesc', 'Unknown')}
Severity: {props.get('severity', 'Unknown')}
Description: {props.get('description', 'No description available')}
Instructions: {props.get('instruction', 'No specific instructions provided')}

"""
    except Exception as e:
        logger.error(f"Error formatting alert: {str(e)}", exc_info=True)
        return "Error formatting alert data"


@mcp.tool()
async def get_alerts(state: str) -> str:
    """ Get weather alerts for a US state"""
    logger.info(f"Getting alerts for state: {state}")
    
    url = f"{NWS_API_BASE}/alerts/active/area/{state}"
    data = await make_nws_request(url)
    
    if not data or "features" not in data:
        logger.warning(f"No alerts found for state: {state}")
        return "Unable to fetch alerts or no alerts found"
    
    alerts = [format_alert(feature) for feature in data["features"]]
    logger.info(f"Found {len(alerts)} alerts for state: {state}")
    return "\n---\n".join(alerts)


@mcp.tool()
async def get_outfit(forecast_data: str) -> str:
    """Get outfit recommendations based on the weather forecast"""
    logger.info('Getting outfit based on weather forecast')
    
    # Get API key from environment
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if not api_key:
        logger.error("ANTHROPIC_API_KEY not found in environment variables")
        return "Error: Anthropic API key not configured. Please set ANTHROPIC_API_KEY in your .env file."
    
    logger.debug("Successfully loaded Anthropic API key")
    
    try:
        # Create client with explicit API key
        client = anthropic.Anthropic(api_key=api_key)
        logger.debug("Successfully created Anthropic client")
        
        query = f"""
        Based on the following weather forecast, suggest an appropriate outfit:
        
        {forecast_data}
        
        Please provide specific clothing recommendations based on the temperature, wind conditions, and forecast.
        """
        
        message = {
            "role": "user",
            "content": query
        }
        
        logger.debug("Sending request to Anthropic API")
        response = client.messages.create(
            model="claude-3-5-sonnet-20241022",
            max_tokens=1000,
            messages=[message]
        )
        logger.debug("Successfully received response from Anthropic API")
        # Return just the text string
        logger.info(response.content[0].text)
        return str(response.content[0].text)
    
    except Exception as e:
        logger.error(f"Error getting outfit recommendations: {str(e)}", exc_info=True)
        return f"Error getting outfit recommendations: {str(e)}"


@mcp.tool()
async def get_forecast(latitude: float, longitude: float) -> str:
    """Get weather forecast for a location"""
    logger.info(f"Getting forecast for coordinates: {latitude}, {longitude}")
    
    points_url = f"{NWS_API_BASE}/points/{latitude},{longitude}"
    points_data = await make_nws_request(points_url)
    
    if not points_data:
        logger.error(f"Failed to get points data for coordinates: {latitude}, {longitude}")
        return "Unable to fetch forecast data for this location"
    
    forecast_url = points_data["properties"]["forecast"]
    forecast_data = await make_nws_request(forecast_url)
    
    if not forecast_data:
        logger.error(f"Failed to get forecast data from URL: {forecast_url}")
        return "Unable to fetch detailed forecast."
    
    try:
        logger.debug(f"Forecast data structure: {forecast_data.keys()}")
        logger.debug(f"Forecast properties structure: {forecast_data['properties'].keys()}")
        periods = forecast_data["properties"]["periods"]
        forecasts = []
        for period in periods[:5]:
            forecast = f"""
            {period['name']}:
            Temperature: {period['temperature']}°{period['temperatureUnit']}
            Wind: {period['windSpeed']} {period['windDirection']}
            Forecast: {period['detailedForecast']}
"""
            forecasts.append(forecast)
        
        result = "\n---\n".join(forecasts)
        logger.info(f"Forecast result type: {type(result)}")
        logger.info(f"Forecast result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error processing forecast data: {str(e)}", exc_info=True)
        logger.error(f"Full forecast data: {forecast_data}")
        return "Error processing forecast data"



if __name__ == "__main__":
    logger.info("Starting weather server")
    mcp.run(transport='stdio')
    
    
    