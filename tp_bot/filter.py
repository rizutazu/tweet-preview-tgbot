from telegram.ext import filters
from telegram import Update
import logging

from .fetchconfig import getAllowedIds

logger = logging.getLogger("filter")
allowed_ids = getAllowedIds()

def filterAllowedIds(update: Update) -> bool:

    """
    filter user id for message/inline query.
    return: `True` : allowed to use
    """

    if len(allowed_ids) == 0:
        logger.info("empty filter, pass")
        return True
    
    id: int
    if update.message != None:
        id = update.message.chat_id    
    elif update.inline_query != None:
        id = update.inline_query.from_user.id
    else:
        logger.warning("got update with neither message nor inline_query")
        return False
    if id in allowed_ids:
        logger.info(f"user id {id} in {allowed_ids}, pass")
        return True
    
    logger.warning(f"user id {id} not in {allowed_ids}, not allowed ")
    return False