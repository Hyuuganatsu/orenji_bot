import os

APPLICABLE_RATE_TYPES = {"JPY":"🇯🇵", "AUD":"🇦🇺", "USD":"🇺🇸", "SGD":"🇸🇬", "CAD": "🇨🇦", "EUR": "🇪🇺"}

ACCOUNT = int(os.environ["ACCOUNT"])
BACKEND_URL = "http://backend:{}/".format(os.environ["BACKEND_PORT"])
TWITTER_BEARER_KEY = os.environ["TWITTER_BEARER_KEY"]