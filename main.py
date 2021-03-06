import csv
import datetime
import logging
import os
import sys
from typing import NoReturn, Optional
from zoneinfo import ZoneInfo
import pathlib
import difflib

import telegram
from dotenv import load_dotenv

_ = load_dotenv()

FILENAME = 'plan.csv'
DELIMITER = '|'
FORMAT_DATETIME = '%Y-%m-%d %H:%M'
INDEX_DATETIME_NOTIFICATION = 0
INDEX_DATETIME_EVENT = 1
INDEX_NAME_EVENT = 2
INDEX_DETAILS_EVENT = 3
TIMEZONE = ZoneInfo('Europe/London')

NAME_TELEGRAM_BOT_TOKEN = 'TELEGRAM_BOT_TOKEN'
NAME_TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'

CHAT_ID = os.environ[NAME_TELEGRAM_CHAT_ID]
TIMEOUT = 30

LOGGING_LEVEL = logging.INFO


def setup_logging():
    root = logging.getLogger()
    root.setLevel(LOGGING_LEVEL)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(LOGGING_LEVEL)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    if sys.platform == "linux" or sys.platform == "linux2":
        file_handler = logging.FileHandler('/tmp/main.log')
        file_handler.setLevel(LOGGING_LEVEL)
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)


setup_logging()


def main() -> NoReturn:
    logging.info('Running main')

    now = get_now()

    bot = get_telegram_bot()

    pinned_message_text = get_pinned_message_text(bot=bot)

    logging.info(f"Opening file {FILENAME}")
    path_file = pathlib.Path(__file__).parent.resolve().joinpath(FILENAME)
    with open(path_file) as csvfile:
        reader = csv.reader(csvfile, delimiter=DELIMITER)

        logging.info(f'Headers: {next(reader)}')

        gone_past_pinned_message = False

        logging.info(f'Looping through rows...')
        for row in reader:
            gone_past_pinned_message = work_on_row(
                bot=bot,
                row=row,
                now=now,
                gone_past_pinned_message=gone_past_pinned_message,
                pinned_message_text=pinned_message_text,
            )


def get_now() -> datetime.datetime:
    now = datetime.datetime.now(tz=TIMEZONE)
    logging.info(f'{now=}')
    return now


def get_telegram_bot() -> telegram.Bot:
    logging.info(f'Trying to create bot using environment variable {NAME_TELEGRAM_BOT_TOKEN}')
    bot = telegram.Bot(token=os.environ[NAME_TELEGRAM_BOT_TOKEN])
    logging.info(f'Created bot using environment variable {NAME_TELEGRAM_BOT_TOKEN}')
    return bot


def get_pinned_message_text(bot: telegram.Bot) -> Optional[str]:
    logging.info(f'Trying to get the pinned messaged from {CHAT_ID=}')

    chat = bot.get_chat(chat_id=CHAT_ID, timeout=TIMEOUT)
    pinned_message = chat.pinned_message

    pinned_message_text = None
    if pinned_message is not None:
        pinned_message_text = pinned_message.text

    logging.info(f'{pinned_message_text=}')

    return pinned_message_text


def work_on_row(
        bot: telegram.Bot,
        row: list[str],
        now: datetime.datetime,
        gone_past_pinned_message: bool,
        pinned_message_text: str,
) -> bool:
    logging.info(f'{gone_past_pinned_message=}')
    logging.info(f'{row=}')

    text = parse_row_to_message_text(row=row)

    if gone_past_pinned_message:
        logging.info('We have gone past the pinned message so trying to send')
        try_send(bot=bot, row=row, now=now, text=text)
    else:
        logging.info('Not gone past the pinned message so not going to try to send')

    if compare_text_equals(pinned=pinned_message_text, parsed=text):
        logging.info('Parsed text from row matches the pinned message so updating gone_past_pinned_message to True')
        gone_past_pinned_message = True

    return gone_past_pinned_message


def parse_row_to_message_text(row: list[str]) -> str:
    if row[INDEX_NAME_EVENT] == '':
        text = row[INDEX_DETAILS_EVENT]
    else:
        details = row[INDEX_DETAILS_EVENT].replace('\\n', '\n')
        text = f'''{row[INDEX_NAME_EVENT]} at {row[INDEX_DATETIME_EVENT]}:

{details}'''

    logging.info(f'Parsed message text from row: {text=}')

    return text


def compare_text_equals(pinned: str, parsed: str) -> bool:
    differences = [li for li in difflib.ndiff(pinned, parsed) if li[0] != ' ']
    logging.info(f'Comparing pinned versus parsed: {differences=}')
    return pinned == parsed


def get_datetime_notification(row: list[str]) -> datetime.datetime:
    return (
        datetime.datetime
        .strptime(row[INDEX_DATETIME_NOTIFICATION], FORMAT_DATETIME)
        .replace(tzinfo=TIMEZONE)
    )


def try_send(
        bot: telegram.Bot,
        row: list[str],
        now: datetime.datetime,
        text: str,
) -> NoReturn:
    # Parse the notification datetime
    datetime_notification = get_datetime_notification(row)

    logging.info(f'Comparing {now=} with {datetime_notification=}')
    # If condition is hit then we send a message with the row contents
    if now > datetime_notification:

        # Send message through telegram bot
        logging.info(f'Trying to send a message using {CHAT_ID=}')
        message = bot.send_message(chat_id=CHAT_ID, text=text)

        # Unpin all previously pinned messages
        bot.unpin_all_chat_messages(chat_id=CHAT_ID)

        # Pin the message
        message_id = message.message_id
        logging.info(f'Pinning message with {message_id=}')
        bot.pin_chat_message(chat_id=CHAT_ID, message_id=message_id)
    else:
        logging.info('Will not try to send a message as now is not past the latest notification datetime in the plan')


if __name__ == '__main__':
    main()
