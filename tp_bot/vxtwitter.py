import httpx
import json
import logging
import re

API = "https://api.vxtwitter.com"
RETRY_COUNT_MAX = 2
client: httpx.AsyncClient = httpx.AsyncClient()
logger = logging.getLogger("vxtwitter")
# match "https://pbs.twimg.com/media/xxx.extension"
# 1st capturing group is "https://pbs.twimg.com/media/xxx", 2nd capturing group is ".extension"
pbs_twimg_regex = re.compile(r"^(https:\/\/pbs\.twimg\.com\/media\/[a-zA-Z0-9]+)(\.[a-z]+)$")

async def queryAPI(tweet_id: str, use_jpg_url: bool=False) -> dict[str, any] | None:

    """
    get tweet info of given tweet_id, or None
    parameters:
    - tweet_id: "username/status/numbers",
    - use_jpg_url: specify whether "url" field should be a link of jpg image(`InlineQueryResultPhoto` requires it)
    
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
                url = convertPbsTwimgUrl(media["url"], use_jpg_url)
                if url == "":
                    logger.critical(f"media url {media['url']} does not have expected format")
                    return None
                m = {
                    "type": media["type"],
                    "url": url,
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

def convertPbsTwimgUrl(url: str, use_jpg_url: bool) -> str:

    """
    convert stuff like "https://pbs.twimg.com/media/xxx.jpg" 
    to "https://pbs.twimg.com/xxx.jpg?name=orig", to reach maximal image quality.

    parameters:
    - url: the stuff mentioned above
    - use_jpg_url: Whether to make sure the link is a jpg image.   \
    If the original image is not a jpg image, "?format=jpg&name=orig" will return 404,  \
    "?format=jpg&name=large" is the only choice. \
    Ref: https://gist.github.com/Colerar/80da426728e38a907cc811ac821bf307 \
    """

    match = pbs_twimg_regex.search(url)
    if match == None or match.group(1) == "":
        return ""
    
    if use_jpg_url and match.group(2) != ".jpg":
        return match.group(1) + "?format=jpg&name=large"
    else:
        return url + "?name=orig"