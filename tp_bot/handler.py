import logging
import telegram.constants
from telegram import (Update, InlineQueryResultPhoto, InlineQueryResultVideo, InlineQueryResultArticle,
                      InputTextMessageContent,
                      InputMediaPhoto, InputMediaVideo)
from telegram.ext import ContextTypes
from telegram.error import NetworkError
from uuid import uuid4

from .parse import parseTweetUrl, parseApiResultText
from .vxtwitter import queryAPI
from .filter import filterAllowedIds

logger = logging.getLogger("handler")
help_message = """
Usage: 
  - Send a tweet link to me,
    e.g., "https://twitter.com/X/status/1983605575444516947"
  - Inline mode: type "@this_bot tweet link" at any chat

Support "twitter.com", "x.com", "fixupx.com", and more.
Source code available at https://github.com/rizutazu/tweet-preview-tgbot.
""".strip("\n")
# max retry count when encountered network error
RETRY_COUNT_MAX = 2

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """
    /start handler
    """

    if not filterAllowedIds(update):
        return

    await update.message.reply_text("Hi, this is a tweet preview bot.\n" + help_message, disable_web_page_preview=True)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """
    /help handler
    """

    if not filterAllowedIds(update):
        return

    await update.message.reply_text(help_message, disable_web_page_preview=True)

async def inlineQuery(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """
    inline query handler
    """

    if not filterAllowedIds(update):
        return

    # check query input
    query = update.inline_query.query
    if query == "":
        logger.info("empty inline query")
        return

    # check && parse url
    tweet_id = parseTweetUrl(query)
    if tweet_id == "":
        logger.info(f"invalid inline query {query}")
        return
    
    logger.info(f"start handling inline query {query}")

    # query api for tweet info
    tweet = await queryAPI(tweet_id, use_jpg_url=True)
    if tweet == None:
        logger.info(f"{tweet_id}: api returned None")
        return

    medias = tweet["media_extended"]

    # pure text
    if len(medias) == 0:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Pure text",
                input_message_content=InputTextMessageContent(
                    message_text=parseApiResultText(tweet, 4096),
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                    disable_web_page_preview=True
                )
            )
        ]
    # with media
    else:
        results = []
        for media in medias:
            # image
            if media["type"] == "image":
                results.append(InlineQueryResultPhoto(
                    id=str(uuid4()),
                    photo_url=media["url"],
                    thumbnail_url=media["thumbnail_url"],
                    photo_width=media["size"]["width"],
                    photo_height=media["size"]["height"],
                    caption=parseApiResultText(tweet, 1024),
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                ))
            # video and gif are treated as same, coz twitter use mp4 to store gif...
            elif media["type"] in ["video", "gif"]:
                results.append(InlineQueryResultVideo(
                    id=str(uuid4()),
                    video_url=media["url"],
                    mime_type="video/mp4",
                    thumbnail_url=media["thumbnail_url"],
                    title=media["type"],
                    caption=parseApiResultText(tweet, 1024),
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                ))
            else:
                logger.critical(f"unknown media type {media['type']}")
    
    # i hate handling network error
    retry = 0
    while retry < RETRY_COUNT_MAX:
        try:
            if len(results) > 0:
                await update.inline_query.answer(results)
                logger.info(f"handled inline query {query}, media count = {len(results)}")
            else:
                logger.warning("all media have unknown type, answer nothing")
            return
        except NetworkError as e:
            retry += 1
            logger.warning(f"error on handling inline query: {e}, retry = {retry}")
    logger.warning("reach retry count max")

async def textInput(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """
    handler for user input
    """

    if not filterAllowedIds(update):
        return

    # check input
    query = update.message.text
    if query == "":
        # this branch might not be possible?
        logger.info("empty user input")
        return

    # check && parse url
    tweet_id = parseTweetUrl(query)
    if tweet_id == "":
        logger.info(f"invalid user input: '{query}'")
        return

    logger.info(f"start handling user input {query}")

    # query api for tweet info
    tweet = await queryAPI(tweet_id)
    if tweet == None:
        logger.info(f"{tweet_id}: api returned none")
        return

    medias = tweet["media_extended"]

    # there is no way to add spolier in inline query
    is_sensitive = tweet["possibly_sensitive"]

    # to merge different reply_* function call into one try block
    reply_func: str["" | "markdown_v2" | "photo" | "video" | "media_group"] = ""
    reply_media_group = []

    # pure text
    if len(medias) == 0:
        reply_func = "markdown_v2"
    # with media
    else:
        # one media => [reply_photo, reply_video]
        if len(medias) == 1:
            if medias[0]["type"] == "image":
                reply_func = "photo"
            elif medias[0]["type"] in ["video", "gif"]:
                reply_func = "video"
            else:
                # reply_func = ""
                logger.critical(f"unknown media type {medias[0]['type']}")
        # multiple => reply_media_group, require >= 2 items, so
        else:
            for media in medias:
                if media["type"] == "image":
                    reply_media_group.append(InputMediaPhoto(
                        media=media["url"],
                        has_spoiler=is_sensitive
                    ))
                elif media["type"] in ["video", "gif"]:
                    reply_media_group.append(InputMediaVideo(
                        media=media["url"],
                        has_spoiler=is_sensitive
                    ))
                else:
                    logger.critical(f"unknown media type {media['type']}")
            # require at least 2
            if len(reply_media_group) >= 2:
                reply_func = "media_group"
    
    retry = 0
    while retry < RETRY_COUNT_MAX:
        try:
            if reply_func == "markdown_v2":
                # text len limit 4096
                await update.message.reply_markdown_v2(parseApiResultText(tweet, 4096), disable_web_page_preview=True)
                logger.info(f"handled user input {query}, media count = {len(medias)}")
            elif reply_func == "photo":
                await update.message.reply_photo(
                    photo=medias[0]["url"],
                    caption=parseApiResultText(tweet, 1024),
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                    has_spoiler=is_sensitive
                )
                logger.info(f"handled user input {query}, media count = {len(medias)}")
            elif reply_func == "video":
                # caption len limit 1024
                await update.message.reply_video(
                    video=medias[0]["url"],
                    caption=parseApiResultText(tweet, 1024),
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2,
                    has_spoiler=is_sensitive
                )
                logger.info(f"handled user input {query}, media count = {len(medias)}")
            elif reply_func == "media_group":
                await update.message.reply_media_group(
                    media=reply_media_group,
                    caption=parseApiResultText(tweet, 1024),
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                )
                logger.info(f"handled user input {query}, media count = {len(reply_media_group)}")
            else:
                logger.critical("all media have unknown type, reply nothing")
            return
        except NetworkError as e:
            retry += 1
            logger.warning(f"error on handling user input: {e}, retry = {retry}")
    logger.warning("reach retry count max")

async def errorHandler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:

    """
    handler for exception
    """

    e = context.error
    if type(e) == NetworkError:
        logger.warning(f"telegram network error")
    else:
        logger.critical(f"unexpected exception happened: {type(e)}", exc_info=context.error)
    
    