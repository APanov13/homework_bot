from http import HTTPStatus
import time
import requests
import telegram
import logging
from dotenv import load_dotenv
import os

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DATE_ZERO = 1655919707

RETRY_TIME = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}

HOMEWORK_STATUSES = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='program.log',
    level=logging.DEBUG
)

logger = logging.getLogger(__name__)


class BotException(Exception):
    """Мои исключения."""

    pass


# ФУНКЦИЯ ИСПРАВНА
def check_tokens():
    """Проверка токенов на работоспособность."""
    if PRACTICUM_TOKEN is None:
        logging.error('Ошибка связанная с PRACTICUM_TOKEN')
        return False
    if TELEGRAM_TOKEN is None:
        logging.error('Ошибка связанная с TELEGRAM_TOKEN')
        return False
    if TELEGRAM_CHAT_ID is None:
        logging.error('Ошибка связанная с PTELEGRAM_CHAT_ID')
        return False
    return True


# ФУНКЦИЯ ИСПРАВНА
def get_api_answer(current_timestamp):
    """Получение ответа от API ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code == HTTPStatus.OK:
        return response.json()
    elif response.status_code != HTTPStatus.OK:
        logging.error(
            f'Сбой работы. Ответ сервера {response.status_code}')
        send_message(
            f'Сбой работы. Ответ сервера {response.status_code}')

# Вариант на обед пятницы
# def check_response(response):
#     logging.debug('Логирование входа в блок')
#     if not isinstance(response['homeworks'], list):
#         raise BotException('Запрос не является списком')
#     if response['homeworks'] is None:
#         raise BotException('Домашки нет')
#     logging.debug('Логирование выхода из блока')
#     return response['homeworks'][0]

# ФУНКЦИЯ ИСПРАВНА
# def parse_status(homework):
#     homework_name = homework['homework_name']
#     homework_status = homework['status']
#     verdict = HOMEWORK_STATUSES[homework_status]
#     return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_response(response: list) -> list:
    """Проверяет ответ API на корректность."""
    logging.debug("Проверка ответа API на корректность")
    if 'error' in response:
        if 'error' in response['error']:
            raise BotException(
                f"{response['error']['error']}"
            )

    if 'code' in response:
        raise BotException(
            f"{response['message']}"
        )

    if response['homeworks'] is None:
        raise BotException("Задания не обнаружены")

    if not isinstance(response['homeworks'], list):
        raise BotException("response['homeworks'] не является списком")
    logging.debug("API проверен на корректность")
    return response['homeworks']


def parse_status(homework: dict) -> str:
    """Извлекает из домашки статус работы."""
    logging.debug(f"Парсим домашнее задание: {homework}")
    homework_name = homework['homework_name']
    homework_status = homework['status']

    if homework_status not in HOMEWORK_STATUSES:
        raise BotException(
            "Обнаружен новый статус, отсутствующий в списке!"
        )

    verdict = HOMEWORK_STATUSES[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


# ФУНКЦИЯ ИСПРАВНА
def send_message(bot, message):
    """Отправляет сообщение в телегу."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение отправлено: {message}')
    except BotException:
        logging.error('Сообщение не было отправленно')
        return 'Не удалось отправить сообщение.'


def main():
    """Основная логика работы бота."""
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = DATE_ZERO
    # current_timestamp = int(time.time())
    if check_tokens() is False:
        logging.critical('Отсутствует обязательная переменная окружения.')
        print('Проверь что все ключи правильные')
        quit()
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            if homework:
                message = parse_status(homework)
                send_message(bot, message)
            time.sleep(RETRY_TIME)

        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            print(message)
            time.sleep(RETRY_TIME)
        else:
            message = parse_status(homework)
            print(message)
            send_message(bot, message)
            time.sleep(RETRY_TIME)

    # while True:
    #     try:
    #         response = get_api_answer(current_timestamp)
    #         homework = check_response(response)
    #         logging.info(f'Получили список работ {homework}')
    #         if len(homework) > 0:
    #             send_message(bot, parse_status(homework[0]))
    #         logging.info('Заданий нет')
    #         current_timestamp = response['current_date']
    #         time.sleep(RETRY_TIME)

    #     except Exception as error:
    #         logging.error(f'Сбой в работе программы: {error}')
    #         send_message(bot, f'Сбой в работе программы: {error}')
    #         time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()


#     bot = Bot(token=TELEGRAM_TOKEN)
# current_timestamp = int(time.time())

# check_tokens()
# while True:
#         try:
#             response = get_api_answer(current_timestamp)
#             homework = check_response(response)
#             current_timestamp = homework[0].get('current_date')
#         except KeyError as error:
#             logging.error(f'Error while getting list of homeworks: {error}')
#             print('Error while getting list of homeworks')
#             time.sleep(RETRY_TIME)
#             continue
#         except Exception as error:
#             logging.error(f'Error while getting list of homeworks: {error}')
#             message = 'Сбой в работе программы'
#             print(message)
#             time.sleep(RETRY_TIME)
#             continue
#         else:
#             message = parse_status(homework)
#             send_message(bot, message)
#             time.sleep(RETRY_TIME)
