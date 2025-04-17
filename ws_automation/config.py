# Configuration module for WordPress automation scripts
# Handles environment variables, configuration validation, and settings management

import os
from dotenv import load_dotenv, find_dotenv
from dataclasses import dataclass
import pathlib

# Get the current file's directory and construct path to .env file
current_dir = pathlib.Path(__file__).parent.resolve()
env_path = current_dir / '.env'

# Debug information about .env file location
print(f"Looking for .env file at: {env_path}")
print(f"File exists: {env_path.exists()}")

# Attempt to locate the .env file
dotenv_path = find_dotenv(str(env_path))
print(f"Found dotenv at: {dotenv_path}")

# Load environment variables from .env file, allowing override of existing variables
load_dotenv(dotenv_path=env_path, override=True)

# Debug output of environment variables (masking sensitive data)
print("\nRaw environment variables:")
for key in ['WP_URL', 'WP_USERNAME', 'WP_PASSWORD', 'OPENAI_API_KEY', 'PLAYWRIGHT_HEADLESS', 'PLAYWRIGHT_SLOW_MO']:
    value = os.getenv(key)
    if key in ['WP_PASSWORD', 'OPENAI_API_KEY']:
        value = '********' if value else 'Not set'
    print(f"{key}: {value}")

# Data class for WordPress-specific configuration
@dataclass
class WordPressConfig:
    username: str = os.getenv('WP_USERNAME')  # WordPress admin username
    password: str = os.getenv('WP_PASSWORD')  # WordPress admin password
    url: str = os.getenv('WP_URL')           # WordPress site URL

# Data class for AI-related configuration (OpenAI)
@dataclass
class AIConfig:
    openai_api_key: str = os.getenv('OPENAI_API_KEY')  # OpenAI API key for GPT integration

# Data class for Playwright browser automation settings
@dataclass
class PlaywrightConfig:
    headless: bool = True          # Whether to run browser in headless mode
    slow_mo: int = 100            # Delay between actions in milliseconds
    timeout: int = 30000          # Default timeout for operations in milliseconds

# Main configuration class that combines all settings
class Config:
    wp = WordPressConfig()        # WordPress settings
    ai = AIConfig()               # AI settings
    playwright = PlaywrightConfig()  # Browser automation settings

    @classmethod
    def validate(cls):
        """
        Validate that all required environment variables are set.
        Raises ValueError if any required variables are missing.
        """
        missing_vars = []
        
        # Check for required WordPress variables
        if not cls.wp.username:
            missing_vars.append('WP_USERNAME')
        if not cls.wp.password:
            missing_vars.append('WP_PASSWORD')
        if not cls.wp.url:
            missing_vars.append('WP_URL')
        if not cls.ai.openai_api_key:
            missing_vars.append('OPENAI_API_KEY')
            
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Create a global config instance for use across the application
config = Config()

# When run directly, validate and display configuration
if __name__ == "__main__":
    try:
        config.validate()
        print("Configuration loaded successfully!")
        print("\nCurrent settings:")
        print(f"WordPress URL: {config.wp.url}")
        print(f"WordPress Username: {config.wp.username}")
        print(f"WordPress Password: {'*' * 8 if config.wp.password else 'Not set'}")
        print(f"OpenAI API Key: {'*' * 8 if config.ai.openai_api_key else 'Not set'}")
        print(f"\nPlaywright Settings:")
        print(f"Headless Mode: {config.playwright.headless}")
        print(f"Slow Mo: {config.playwright.slow_mo}ms")
        print(f"Timeout: {config.playwright.timeout}ms")
    except ValueError as e:
        print(f"\nConfiguration Error: {e}")
        print("\nPlease set up your .env file with the required variables.") 