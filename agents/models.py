from functools import cached_property
from google.adk.models import Gemini
from google.genai import Client
from google.genai import types

class RateLimitedGemini(Gemini):
    @cached_property
    def api_client(self) -> Client:
        # Increase attempts to 15 and set initial delay to 6 seconds
        # to handle strict free-tier rate limits (e.g. 5 RPM)
        retry_options = types.HttpRetryOptions(
            attempts=15,
            initial_delay=6.0,
            max_delay=60.0
        )
        http_options = types.HttpOptions(retry_options=retry_options)
        return Client(http_options=http_options)
