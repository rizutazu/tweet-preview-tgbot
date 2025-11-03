import logging
import os

MY_LOGGERS = ["vxtwitter", "handler", "main", "filter"]

l = max([len(x) for x in MY_LOGGERS])
logging.basicConfig(
    format=f"[%(levelname)7s][%(asctime)s][%(name){l}s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARNING
)

if os.getenv("DEBUG_TGBOT") != None:
    for name in MY_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)