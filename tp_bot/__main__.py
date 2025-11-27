from telegram.ext import Application, CommandHandler, InlineQueryHandler, MessageHandler, filters
from telegram import BotCommand, Update
import logging
import asyncio

from .handler import start, help, inlineQuery, textInput, errorHandler
from .fetchconfig import getToken

logger = logging.getLogger("main")

def main():

    # get token & build application
    token = getToken()
    if token == "":
        logger.fatal("no token provided")
        exit(1)
    
    application = Application.builder().token(token).build()

    # set bot command list
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(application.bot.set_my_commands([
            BotCommand("start", "start bot"),
            BotCommand("help", "get help")
        ]))
    except:
        logger.warning("set command failed")

    # add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(InlineQueryHandler(inlineQuery))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, textInput))
    application.add_error_handler(errorHandler, block=False)

    # start polling
    logger.info("start polling")
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)

if __name__ == "__main__":
    main()