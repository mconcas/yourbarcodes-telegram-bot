import os

TELEGRAM_BOT_TOKEN: str = os.environ["TELEGRAM_BOT_TOKEN"]

OPENSEARCH_HOST: str = os.environ.get("OPENSEARCH_HOST", "opensearch")
OPENSEARCH_PORT: int = int(os.environ.get("OPENSEARCH_PORT", "9200"))

# Optional: HTTPS URL where webapp/scanner.html is served.
# Telegram WebApps require HTTPS. Leave empty to disable the in-chat scanner button.
WEBAPP_URL: str = os.environ.get("WEBAPP_URL", "")

LOG_LEVEL: str = os.environ.get("LOG_LEVEL", "INFO")
