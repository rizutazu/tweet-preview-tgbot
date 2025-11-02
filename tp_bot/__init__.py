import logging
import os

logging.basicConfig(
    format="[%(levelname)s][%(asctime)s][%(name)s]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=logging.WARNING
)

MY_LOGGERS = ["vxtwitter", "handler", "main", "filter"]

if os.getenv("DEBUG_TGBOT") != None:
    for name in MY_LOGGERS:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)