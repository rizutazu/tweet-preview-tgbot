import httpx
import json
import logging

API = "https://api.vxtwitter.com"
RETRY_COUNT_MAX = 2
client: httpx.AsyncClient = httpx.AsyncClient()
logger = logging.getLogger("vxtwitter")

async def queryAPI(tweet_id: str) -> dict[str, any] | None:

    """
    get tweet info of given tweet_id, or None
    tweet_id format: "username/status/numbers",
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
        "user_screen_name": "screen_name",

        // if api does not return this key, assume false
        "possibly_sensitive": False,
    }
    """

    q = f"{API}/{tweet_id}"

    retry = 0
    while retry < RETRY_COUNT_MAX:
        try:
            # query the api
            response = await client.get(q)
            response.raise_for_status()
            response_content = json.loads(response.text)

        # well the server failed or sth, return
        except httpx.HTTPStatusError:
            logger.warning(f"http status code {response.status_code}")
            return None
        # network issue, retry
        except (httpx.NetworkError, httpx.TimeoutException):
            retry += 1
            logger.warning(f"network error, retry count = {retry}")
            continue
        # failed link will respond with a html webpage
        except json.JSONDecodeError:
            logger.warning(f"might be bad link: {tweet_id}")
            return None
        # what hell
        except Exception as e:
            logger.critical(f"unexpected exception: {type(e)}: {str(e)}")
            return None

        try:
            # check whether certain key exist
            media_extended = []
            for media in response_content["media_extended"]:
                m = {
                    "type": media["type"],
                    "url": media["url"] + "?format=jpg&name=orig",  # original size
                    "thumbnail_url": media["thumbnail_url"],
                }
                # image has size field
                if media["type"] == "image":
                    m["size"] = {
                        "height":  media["size"]["height"],
                        "width": media["size"]["width"]
                    }
                media_extended.append(m)
            r = {
                "media_extended": media_extended,
                "text": response_content["text"],
                "tweetURL": response_content["tweetURL"],
                "user_name": response_content["user_name"],
                "user_screen_name": response_content["user_screen_name"],
                "possibly_sensitive": response_content.get("possibly_sensitive", False)
            }
            return r
        except KeyError as e:
            logger.critical(f"result does not contain expected key: {str(e)}")
            return None

    logger.warning("reach retry count max")
    return None