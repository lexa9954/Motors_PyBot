from datetime import datetime
import cfg  # Ваш модуль работы с базой данных
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')

# Глобальный словарь для хранения информации о пользователях
users = {}

def auth(message):
    chat_id = str(message.chat.id)
    user_input = message.text.strip()  # Убираем пробелы в начале и конце

    # Инициализируем пользователя, если его нет в словаре
    if chat_id not in users:
        users[chat_id] = {'status': 'offline', 'last_activity_time': datetime.now().strftime("%H:%M:%S")}
        logging.info(f"Добавлен новый пользователь: chat_id={chat_id}")

    # Обрабатываем статус
    if users[chat_id]['status'] == 'offline':
        return handle_offline_user(chat_id, user_input, message)
    else:
        logging.info(f"Пользователь уже авторизован: chat_id={chat_id}")
        return send_message("Вы уже авторизованы!", 'keyboards.kb_main_menu()')


def handle_offline_user(chat_id, user_input, message):
    """Обработка пользователей со статусом 'offline'."""
    if user_input.isdigit():
        tabel = user_input
        user = cfg.select_user(tabel)

        if user is None:
            if cfg.check_user_true(tabel):  # Если пользователь существует
                cfg.sign_up(message.chat.id, tabel)
                return send_message(f"Здравствуйте, <b>{user[0]}</b>!\n\nВыберите услугу", 'keyboards.kb_main_menu()', chat_id, status='online')
            else:
                return send_message("Такого работника нет в базе. Обратитесь к вашему руководству.", 'keyboard_retry')

        # Проверка длины результата
        if len(user) > 2:
            if not user[2]:  # Если chat_id пустой
                if not cfg.check_chat_id(message.chat.id):
                    cfg.add_chat_id(message.chat.id, tabel)
                    return send_message(f"Здравствуйте, <b>{user[0]}</b>!\n\nВыберите услугу", 'keyboards.kb_main_menu()', chat_id, status='online')
                else:
                    return send_message("У вас уже есть аккаунт. Не пытайтесь притворяться!", 'keyboard_retry')
            elif user[2] == chat_id:
                return send_message(f"Здравствуйте, <b>{user[0]}</b>!\n\nВыберите услугу", 'keyboards.kb_main_menu()', chat_id, status='online')
            else:
                return send_message("Этот табельный номер привязан к другому пользователю. Введите свой табельный номер!", 'keyboard_retry')

        return send_message("Ошибка в данных пользователя. Попробуйте ещё раз.", 'keyboard_retry')

    else:
        return send_message("Табельный номер должен содержать только цифры!", 'keyboard_retry')


def send_message(info, message_type, chat_id=None, status=None):
    """Упрощает возврат сообщений и обновление статуса."""
    if chat_id and status:
        users[chat_id]['status'] = status
        users[chat_id]['last_activity_time'] = datetime.now().strftime("%H:%M:%S")
        logging.info(f"Обновление статуса пользователя: chat_id={chat_id}, status={status}")

    return {
        'info': info,
        'type': message_type
    }