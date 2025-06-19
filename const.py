"""Constants for the Bestway Spa integration."""
DOMAIN = "bestway_spa"

# Configuration keys
CONF_APPID = "appid"
CONF_APPSECRET = "appsecret"
CONF_DEVICE_ID = "device_id"
CONF_PRODUCT_ID = "product_id"
CONF_REGISTRATION_ID = "registration_id"
CONF_VISITOR_ID = "visitor_id"
CONF_CLIENT_ID = "client_id"

# Default values
DEFAULT_NAME = "Bestway Spa"

# API endpoints
API_BASE_URL = "https://smarthub-eu.bestwaycorp.com/api"
API_VISITOR_ENDPOINT = f"{API_BASE_URL}/enduser/visitor"
API_THING_SHADOW_ENDPOINT = f"{API_BASE_URL}/device/thing_shadow"
API_COMMAND_ENDPOINT = f"{API_BASE_URL}/device/command"

# Heater states
HEATER_STATE_OFF = 0
HEATER_STATE_HEATING = 2
HEATER_STATE_PASSIVE = 4

# Temperature limits
MIN_TEMP = 1
MAX_TEMP = 40 