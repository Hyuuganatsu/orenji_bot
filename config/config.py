import os

APPLICABLE_RATE_TYPES = {"JPY":"🇯🇵", "AUD":"🇦🇺", "USD":"🇺🇸", "SGD":"🇸🇬", "CAD": "🇨🇦", "EUR": "🇪🇺", "GBP": "🇬🇧"}

ACCOUNT = int(os.environ["ACCOUNT"])
BACKEND_URL = "http://backend:{}/".format(os.environ["BACKEND_PORT"])
TWITTER_BEARER_KEY = os.environ["TWITTER_BEARER_KEY"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
LOG_FILE_PATH = os.environ["LOG_FILE_PATH"]