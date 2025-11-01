# read from .env file
import os
from dotenv import load_dotenv

load_dotenv()

LOGGING_LEVEL = os.getenv("LOGGING_LEVEL") if os.getenv("LOGGING_LEVEL") else "INFO"
INTERVAL_MINUTE = int(os.getenv("INTERVAL_MINUTE") if os.getenv("INTERVAL_MINUTE") else 10)

BROWSER_MAX_TAB_NUMBER = int(os.getenv("BROWSER_MAX_TAB_NUMBER") if os.getenv("BROWSER_MAX_TAB_NUMBER") else 2)
BROWSER_HEADLESS = False if os.getenv("BROWSER_HEADLESS") == "false" else True 
BROWSER_USER_AGENT = os.getenv("BROWSER_USER_AGENT") if os.getenv("BROWSER_USER_AGENT") else "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36"
BROWSER_USER_AGENT_MOBILE = os.getenv("BROWSER_USER_AGENT_MOBILE") if os.getenv("BROWSER_USER_AGENT_MOBILE") else "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.7103.88 Mobile Safari/537.36"

FACEBOOK_LOGIN_URL = os.getenv("FACEBOOK_LOGIN_URL") if os.getenv("FACEBOOK_LOGIN_URL") else "https://www.facebook.com/login/"
FACEBOOK_EMAIL = os.getenv("FACEBOOK_EMAIL")
FACEBOOK_PASSWORD = os.getenv("FACEBOOK_PASSWORD")
