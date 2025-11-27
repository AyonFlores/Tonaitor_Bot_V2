# utils/api.py
import time
import aiohttp
import json

ANILIST_URL = "https://graphql.anilist.co"

# --- CACHE CONFIGURATION ---
# Simple dictionary to store results: { "unique_key": (timestamp, data) }
_CACHE = {}
# How long to keep data? (e.g., 30 minutes)
CACHE_TTL = 30 * 60


class RateLimitError(Exception):
    def __init__(self, wait_time):
        self.wait_time = wait_time


async def fetch_anilist(session: aiohttp.ClientSession, query: str, variables: dict):
    # 1. GENERATE CACHE KEY
    # We turn the variables dict into a string so it can be used as a key
    var_string = json.dumps(variables, sort_keys=True)
    cache_key = f"{query}{var_string}"

    # 2. CHECK CACHE
    current_time = time.time()
    if cache_key in _CACHE:
        timestamp, cached_data = _CACHE[cache_key]
        # If the data is younger than the TTL, return it immediately
        if current_time - timestamp < CACHE_TTL:
            return cached_data
        else:
            # If data is old, delete it
            del _CACHE[cache_key]

    # 3. FETCH NEW DATA (If not in cache)
    try:
        async with session.post(ANILIST_URL, json={'query': query, 'variables': variables}) as response:

            # Handle Rate Limit (429)
            if response.status == 429:
                reset_ts = int(response.headers.get("X-RateLimit-Reset", time.time() + 60))
                wait_seconds = max(1, reset_ts - int(time.time()))
                raise RateLimitError(wait_seconds)

            # Handle Success (200)
            if response.status == 200:
                data = await response.json()
                result = data.get('data')

                # 4. SAVE TO CACHE
                if result:
                    _CACHE[cache_key] = (current_time, result)

                return result
            else:
                print(f"AniList API Error: {response.status}")
                return None

    except RateLimitError:
        raise  # Re-raise for the command to catch
    except Exception as e:
        print(f"Request Failed: {e}")
        return None