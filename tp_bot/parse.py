from urllib.parse import urlparse
from telegram.helpers import escape_markdown

supported_domain = [
    "twitter.com",
    "x.com",
    "vxtwitter.com",
    "fixvx.com",
    "fxtwitter.com",
    "fixupx.com",
    "girlcockx.com",    # ?
]

def parseTweetUrl(query: str) -> str:

    """
    check if `query` is a valid twitter link, 
    if so, return its tweet id, or return empty string

    e.g. 
    - "twitter.com/aaa/status/114514" => "aaa/status/114514"
    - "x.com/aaa/status/114514/photo/2" => "aaa/status/114514"
    """

    # convert query to make it starts with "https://" or "http://"
    if not (query.startswith("https://") or query.startswith("http://")):
        query = "https://" + query

    try:
        r = urlparse(query)
        if r.netloc.lstrip("www.") in supported_domain:
            # remove leading and ending "/", then split
            paths = r.path.removeprefix("/").removesuffix("/").split("/")
            
            # must match "username/status/number" pattern:
            # 1. at least 3
            # 2. 0: not empty, 1: "status", 2: number
            if len(paths) < 3:
                return ""
            if (not paths[0]) or (paths[1] != "status"):
                return ""
            _ = int(paths[2])   # if not number/empty => exception
            
            return paths[0] + "/" + paths[1] + "/" + paths[2]
    except:
        return ""

    return ""

def parseApiResultText(r: dict[str, any]) -> str:

    """
    convert api result text (text part of given tweet) into markdown v2 text
    """

    result = escape_markdown(f"{r['tweetURL']}\n", 2)
    result += f"[{escape_markdown(r['user_name'], 2)}]({escape_markdown('https://twitter.com/'+r["user_screen_name"], 2)}):\n"
    if r['text'] != "":
        for line in r['text'].split("\n"):
            result += f">{escape_markdown(line, 2)}\n"
    return result