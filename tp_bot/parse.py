from urllib.parse import urlparse
from telegram.helpers import escape_markdown
import re

supported_domain = [
    "twitter.com",
    "x.com",
    "vxtwitter.com",
    "fixvx.com",
    "fxtwitter.com",
    "fixupx.com",
    "girlcockx.com",    # ?
]
# ref: https://github.com/dylanpdx/BetterTwitFix/blob/main/utils.py
# to remove "https://t.co/bla" in "some-user-content https://t.co/bla", or "https://t.co/bla", if exist
# it seems like "https://t.co/bla" cannot be user intented text content, 
# because, if the path of the "t.co" link is not root, it will be replaced by its display link,
    # e.g., "t.co/a" => "twitter.com/adlleong" (wow)
# but "t.co" / "t.co/?arg=1" can be user intended however
# assuming t.co link path contains a-z & A-Z & 0-9 only
end_tco_regex = re.compile(r"^((.|\n)*?) *?https:\/\/t\.co\/[a-zA-Z0-9]+?$")

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
    
    # remove t.co links at the end of a string
    # ref: https://github.com/dylanpdx/BetterTwitFix/blob/main/utils.py
    text = r['text']
    match = end_tco_regex.search(text)
    if match != None:
        text = match.group(1)

    text = text.strip()
    if text != "":
        for line in text.split("\n"):
            result += f">{escape_markdown(line, 2)}\n"
    return result