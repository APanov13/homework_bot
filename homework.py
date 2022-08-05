import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import BotException

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

DATE_ZERO = 1659640107

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


def check_tokens():
    """Проверка токенов на работоспособность."""
    true_tokens = (PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)
    return all(true_tokens)


def get_api_answer(current_timestamp):
    """Получение ответа от API ."""
    timestamp = current_timestamp or int(time.time())
    params = {'from_date': timestamp}
    logging.info('Начат процесс запроса к API')
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != HTTPStatus.OK:
        raise BotException(f'Сбой работы.Ответ сервера {response.status_code}')
    logging.info('Процесс запроса к API завершен успешно')
    return response.json()


def check_response(response: list) -> list:
    """Проверяет ответ API на корректность."""
    logging.debug('Проверка ответа API на корректность')
    logging.debug(f'входящий тип данных в ф-ю check_response:{type(response)}')
    if 'error' in response:
        if 'error' in response['error']:
            raise BotException(
                f"{response['error']['error']}"
            )

    if 'code' in response:
        raise BotException(
            f"{response['message']}"
        )
    if not isinstance(response, dict):
        raise TypeError(
            'В ответе от API под ключом "homeworks" пришел не словарь.'
            f' response = {response}.'
        )

    homeworks = response.get('homeworks')

    if not isinstance(homeworks, list):
        raise KeyError(
            'В ответе от API под ключом "homeworks" пришел не список.'
            f' response = {response}.'
        )
    if not isinstance(response, dict):
        raise BotException('response не словарь!')
    if response['homeworks'] is None:
        raise BotException('Задания не обнаружены')
    if not isinstance(response['homeworks'], list):
        raise BotException('response[homeworks] не является списком')
    logging.debug('API проверен на корректность')
    return homeworks


def parse_status(homework):
    """Извлекает из домашки статус работы."""
    logging.debug(f'Парсим домашнее задание: {homework}')
    logging.debug(f'входящий тип данных в ф-ю parse_status: {type(homework)}')
    if 'homework_name' not in homework:
        raise KeyError('Ошибка ключа "homework_name"')
    elif 'status' not in homework:
        raise KeyError('Ошибка ключа "status"')

    homework_name = homework['homework_name']

    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES:
        raise BotException(
            'Обнаружен новый статус, отсутствующий в списке!'
        )

    verdict = HOMEWORK_STATUSES[homework_status]
    logging.debug('Парсинг прошел успешно')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def send_message(bot, message):
    """Отправляет сообщение в телегу."""
    logging.info('Начат процесс отправки сообщения в Телеграм')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Сообщение отправлено: {message}')
    except BotException:
        logging.error('Сообщение не было отправленно')
        return 'Не удалось отправить сообщение.'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logging.critical('Отсутствует обязательная переменная окружения.')
        sys.exit('Токены упали')
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    current_timestamp = DATE_ZERO

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homework = check_response(response)
            logging.debug(
                f'выходящий тип данных из ф-ии check_response:{type(homework)}'
            )
            if len(homework) > 0:
                send_message(bot, parse_status(homework[0]))
        except Exception as error:
            logging.error(f'Сбой в работе программы: {error}')
            message = f'Сбой в работе программы: {error}'
            print(message)
        else:
            message = parse_status(homework)
            print(message)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
