from typing import Any
import httpx
from mcp.server.fastmcp import FastMCP
import logging
import os
import anthropic

# Configure logging to file
log_file = os.path.join(os.path.dirname(__file__), 'weather_server.log')
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename=log_file,
    filemode='a'  # append mode
)
logger = logging.getLogger(__name__)

# Also log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

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
async def get_outfit(tempurature: float, windSpeed: float, windDirection: float, deatiledForecast: str):
    """ get outfit based on the weather"""
    logger.info(f'Getting outfit based on weather')
    
    client = anthropic.Anthropic()
    
    query = f"""
    Temperature: {tempurature}
    Wind Speed: {windSpeed}
    Wind Direction: {windDirection}
    Detailed Forecast: {deatiledForecast}
    
    """
    
    message = {
        "role": "user",
        "content": query
    }
    
    response = client.messages.create(
        
        model = "claude-3-5-sonnet-20241022",
        max_tokens = 1000,
        messages = message

    )
    return response
    
    
    

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
        
        logger.info(f"Successfully retrieved forecast for coordinates: {latitude}, {longitude}")
        return "\n---\n".join(forecasts)
    except Exception as e:
        logger.error(f"Error processing forecast data: {str(e)}", exc_info=True)
        logger.error(f"Full forecast data: {forecast_data}")
        return "Error processing forecast data"



if __name__ == "__main__":
    logger.info("Starting weather server")
    mcp.run(transport='stdio')
    
    
    