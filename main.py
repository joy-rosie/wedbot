import csv
import datetime
from zoneinfo import ZoneInfo
from typing import NoReturn, Optional
import os
import logging

import telegram
from dotenv import load_dotenv

_ = load_dotenv()

TIMEDELTA_THRESHOLD = datetime.timedelta(minutes=1)
DATETIME_TEST = datetime.datetime(year=2000, month=1, day=1)

FILENAME = 'plan.csv'
DELIMITER = ','
FORMAT_DATETIME = '%Y-%m-%d %H:%M'
INDEX_DATETIME_NOTIFICATION = 0
INDEX_DATETIME_EVENT = 1
INDEX_NAME_EVENT = 2
INDEX_DETAILS_EVENT = 3
TIMEZONE = ZoneInfo('Europe/London')

NAME_TELEGRAM_BOT_TOKEN = 'TELEGRAM_BOT_TOKEN'
NAME_TELEGRAM_CHAT_ID = 'TELEGRAM_CHAT_ID'

logging.basicConfig(format='%(asctime)s %(message)s')


def main() -> NoReturn:

    logging.info('Running main')

    now = get_now()

    bot = get_telegram_bot()

    pinned_message_text = get_pinned_message_text(bot=bot)

    logging.info(f"Opening file {FILENAME}")
    with open(FILENAME) as csvfile:
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
    chat = bot.get_chat()
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

    text = parse_row_to_message_text(row=row)
    logging.info(f'Parsed message text from row:\n{text=}')

    if gone_past_pinned_message:
        logging.info("We have gone past the pinned message so trying to send")
        try_send(bot=bot, row=row, now=now, text=text)
    else:
        logging.info("Not gone past the pinned message so not going to try to send")

    if text == pinned_message_text:
        logging.info(
            'Parsed text from row matches the pinned message so updating gone_past_pinned_message to True'
        )
        gone_past_pinned_message = True

    return gone_past_pinned_message


def parse_row_to_message_text(row: list[str]) -> str:
    if row[INDEX_NAME_EVENT] == '':
        return 'test'
    else:
        return f'''{row[INDEX_NAME_EVENT]} at {row[INDEX_DATETIME_EVENT]}:

{row[INDEX_DETAILS_EVENT]}
'''


def get_datetime_notification(row: list[str]) -> datetime.datetime:
    return (
        datetime.datetime
        .strptime(row[INDEX_DATETIME_NOTIFICATION], FORMAT_DATETIME)
        .astimezone(tz=TIMEZONE)
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
    # if now > datetime_notification:
    if True:

        # Send message through telegram bot
        logging.info(f'Trying to send a message using environment variable {NAME_TELEGRAM_CHAT_ID}')
        message = bot.send_message(chat_id=os.environ[NAME_TELEGRAM_CHAT_ID], text=text)

        # Pin the message
        message_id = message.message_id
        logging.info(f'Pinning message with {message_id=}')
        bot.pin_chat_message(message.message_id)
    else:
        logging.info('Will not try to send a message as time does not work')


if __name__ == '__main__':
    main()
