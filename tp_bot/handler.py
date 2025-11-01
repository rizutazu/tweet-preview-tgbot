import logging
import telegram.constants
from telegram import (Update, InlineQueryResultPhoto, InlineQueryResultVideo, InlineQueryResultArticle,
                      InputTextMessageContent,
                      InputMediaPhoto, InputMediaVideo)
from telegram.ext import ContextTypes
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
""".strip("\n")

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
        logger.info(f"invalid inline query '{query}'")
        return

    # query api for tweet info
    tweet = await queryAPI(tweet_id)
    if tweet == None:
        logger.info(f"{tweet_id}: api returned none")
        return

    # prepare text content, markdown v2 format
    text_content = parseApiResultText(tweet)

    medias = tweet["media_extended"]

    # pure text
    if len(medias) == 0:
        results = [
            InlineQueryResultArticle(
                id=str(uuid4()),
                title="Pure text",
                input_message_content=InputTextMessageContent(
                    message_text=text_content,
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
                    caption=text_content,
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
                    caption=text_content,
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                ))
            else:
                logger.critical(f"unknown media type {media['type']}")

    logger.info(f"parsed inline query {query}, media count = {len(medias)}")
    await update.inline_query.answer(results)

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
        await update.message.reply_text("invalid input: not a twitter link")
        return

    # query api for tweet info
    tweet = await queryAPI(tweet_id)
    if tweet == None:
        logger.info(f"{tweet_id}: api returned none")
        await update.message.reply_text("retrieve tweet info failed")
        return

    text_content = parseApiResultText(tweet)

    medias = tweet["media_extended"]

    # pure text
    if len(medias) == 0:
        await update.message.reply_markdown_v2(text_content, disable_web_page_preview=True)
    # with media
    else:
        # one media => [reply_photo, reply_video]
        if len(medias) == 1:
            if medias[0]["type"] == "image":
                await update.message.reply_photo(
                    photo=medias[0]["url"],
                    caption=text_content,
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                )
            elif medias[0]["type"] in ["video", "gif"]:
                await update.message.reply_video(
                    video=medias[0]["url"],
                    caption=text_content,
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                )
            else:
                logger.critical(f"unknown media type {medias[0]['type']}")
        # multiple => reply_media_group, require >= 2 items, so
        else:
            reply_media_group = []
            for media in medias:
                if media["type"] == "image":
                    reply_media_group.append(InputMediaPhoto(
                        media=media["url"]
                    ))
                elif media["type"] in ["video", "gif"]:
                    reply_media_group.append(InputMediaVideo(
                        media=media["url"]
                    ))
                else:
                    logger.critical(f"unknown media type {medias[0]['type']}")
            if len(reply_media_group) >= 2:
                await update.message.reply_media_group(
                    media=reply_media_group,
                    caption=text_content,
                    parse_mode=telegram.constants.ParseMode.MARKDOWN_V2
                )

    logger.info(f"parsed user input {query}, media count = {len(medias)}")
