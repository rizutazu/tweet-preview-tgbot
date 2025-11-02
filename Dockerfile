FROM python:3.12-alpine

WORKDIR /usr/src/tweet-preview-tgbot

COPY . /usr/src/tweet-preview-tgbot

RUN python3 -m pip install --no-cache-dir -r requirements.txt

CMD python3 -u -m tp_bot