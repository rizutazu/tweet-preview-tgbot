import httpx
import json
import logging

API = "https://api.vxtwitter.com"
RETRY_COUNT_MAX = 3
client: httpx.AsyncClient = httpx.AsyncClient()
logger = logging.getLogger("vxtwitter")

async def queryAPI(tweet_id: str) -> dict[str, any] | None:

    """
    get tweet info of given tweet_id, or None
    result format:
    {
        "media_extended": [
            {
                "thumbnail_url": "url",
                "type": "video" | "gif",
                "url": "url"
            },
            {
                "thumbnail_url": "url",
                "type": "image",
                "url": "url",

                // image has extra fields:
                "size": {
                    "height": 206,
                    "width": 194
                }
            }
        ],
        "text": "some text",
        "tweetURL": "https://twitter.com/xxx/status/xxx",
        "user_name": "display name",
        "user_screen_name": "screen_name"
    }
    """

    q = f"{API}/{tweet_id}"

    retry = 0

    while (retry < RETRY_COUNT_MAX):
        try:
            # query the api
            response = await client.get(q)
            response.raise_for_status()
            response_content = json.loads(response.text)

        # well the server failed or sth, return
        except httpx.HTTPStatusError:
            logger.warning(f"vxtwitter api: http status code {response.status_code}")
            return None
        # network issue, retry
        except (httpx.NetworkError, httpx.TimeoutException):
            logger.warning(f"vxtwitter api: network error, retry count = {retry}")
            retry += 1
            continue
        # failed link will respond with a html webpage
        except json.JSONDecodeError:
            logger.warning(f"vxtwitter api: might be bad link: {tweet_id}")
            return None
        # what hell
        except Exception as e:
            logger.critical(f"vxtwitter api: {type(e)}: {str(e)}")
            return None

        try:
            # check whether certain key exist
            for media in response_content["media_extended"]:
                _ = media["url"]
                _ = media["thumbnail_url"]
                if media["type"] == "image":
                    _ = media["size"]["height"]
                    _ = media["size"]["width"]
            r = {
                "media_extended": response_content["media_extended"],
                "text": response_content["text"],
                "tweetURL": response_content["tweetURL"],
                "user_name": response_content["user_name"],
                "user_screen_name": response_content["user_screen_name"],
            }
            return r
        except KeyError as e:
            logger.critical(f"vxtwitter api: result does not contain expected key: {str(e)}")
            return None

    logger.warning("vxtwitter api: exceed retry count max")
    return None