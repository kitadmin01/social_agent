# WordPress Automation with Playwright and LangChain

This project provides automation tools for WordPress using Playwright and LangChain, focusing on SEO optimization and content management tasks.

## Features

- Automated WordPress login
- Yoast SEO interface interaction
- Content analysis and optimization
- Headless browser automation with Playwright
- AI-powered content suggestions with LangChain

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install
```

3. Create a `.env` file with your credentials:
```
WP_USERNAME=your_username
WP_PASSWORD=your_password
WP_URL=your_wordpress_site_url
OPENAI_API_KEY=your_openai_api_key
```

## Usage

Run the main script:
```bash
python main.py
```

## Project Structure

- `main.py`: Main automation script
- `config.py`: Configuration and environment variables
- `requirements.txt`: Project dependencies
- `.env`: Environment variables (not tracked in git)

## Contributing

Feel free to submit issues and enhancement requests. 