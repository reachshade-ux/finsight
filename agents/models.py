from functools import cached_property
from google.adk.models import Gemini
from google.genai import Client
from google.genai import types
import asyncio
from google.adk.tools import AgentTool

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

class RateLimitedAgentTool(AgentTool):
    async def run_async(self, *, args, tool_context):
        # Execute the sub-agent
        result = await super().run_async(args=args, tool_context=tool_context)
        # Sleep for 12 seconds after the agent runs to pace API requests below the 5 RPM limit
        await asyncio.sleep(12.0)
        return result
