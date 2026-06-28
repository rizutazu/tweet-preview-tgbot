# Tweet preview bot

A Telegram bot for tweet content preview.

Features:
- Send link and get the result
- Inline mode: "@this_bot tweet_link"
- Can parse common alternative domains like `vxtwitter.com` / `fixupx.com` ...
- Private deploy: only selected users can use this bot

## Deploy guide

### Using docker

1. Create a new bot from `@BotFather`, **remember to enable inline mode**
2. Create `env_file` from example template: `cp env_file.example env_file` , file name should be `env_file` exactly
3. Modify `env_file` to match your requirements:

```bash
# A list of user IDs which can use this bot, separated by comma, user ID of yourself can be found in @userinfobot.
# If this list is empty, then everyone can use this bot.
# We DO NOT recommend empty list, as this implementation relies on third-party API, this might leads to abuse
export ALLOWED_IDS="114514, 1919"

# your bot token, got from bot father
export TOKEN="114514:aabbccdd"
```

These are environment variables that will be used, DO NOT omit `export` keyword

4. Start the service: run `make up` . Your system should have `make` & `docker` & `git` installed

Run `make update` to update this repository, rebuild & restart the service

Run `make up` to make changed `env_file` to become effective

### Manually

Python 3.12 is required, there is no guarantee on other versions.

1. Install dependencies: `pip install -r requirements.txt`
2. Setup environment variables, please refer to guides mentioned above. E.g., bash: prepare your `env_file` , then run `source env_file` 
3. Start the service: run `python -m tp_bot`

## Known limits

Currently, this bot can only send video of size less than 20MB, which is a limit of Telegram API when sending video by remote URL.

## Credits

[BetterTwitFix](https://github.com/dylanpdx/BetterTwitFix): This bot is implemented by using `api.vxtwitter.com` API, thank you!