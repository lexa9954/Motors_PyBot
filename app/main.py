from telebot import types
import cfg
import keyboards
from os import path
import threading
import time
from datetime import datetime, timedelta
import re


bot = cfg.telebot.TeleBot(cfg.BOT_TOKEN, parse_mode='HTML')

# Создание вложенного словаря с пользователями для присвоения им статуса "Онлайн" или "Оффлайн"
# {tabel : { status : offline }, ...}
users = {}
for i in cfg.get_auth_tabel():
    key = f'{i[1]}'
    users[key] = {'status':'offline', 'last_activity_time': datetime.now().strftime("%H:%M:%S")}

inactive_timeout = timedelta(minutes=60)


#  """РАБОТА БОТА ПРИ ИСПОЛЬЗОВАНИИ КОМАНДЫ /start"""
@bot.message_handler(commands=['start'])
def start(message):
    mesg = bot.send_message(message.chat.id, text="Введите табельный номер")
    bot.register_next_step_handler(mesg, auth)


# """АВТОРИЗАЦИЯ ПОЛЬЗОВАТЕЛЯ"""
@bot.message_handler(content_types=['text'])
def auth(message):
    chat_id = str(message.chat.id)
    if chat_id not in users:
        users[str(message.chat.id)] = {'status':'offline', 'last_activity_time': datetime.now().strftime("%H:%M:%S")}
        print(
            f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} Пользователь (chat_id - {str(message.chat.id)}) добавлен в users (не из log_auth_var)")

    else:
        pass
    
    for id in users:
        if chat_id == id:
            if users[id]['status'] == 'offline':
                if message.text.isdigit():
                    tabel = message.text
                    user = cfg.select_user(tabel)
                    if user[0].startswith('<br') or user is None: # Если пользователь не существует в log_auth_var
                        if cfg.check_user_true(tabel):
                            cfg.sign_up(chat_id, tabel)
                            auth(message)
                            try:
                                bot.send_message(message.chat.id, text=f"Здравствуйте, <b>{user[0]}!</b>\n\nВыберите услугу", reply_markup=keyboards.kb_main_menu())
                            except cfg.telebot.apihelper.ApiTelegramException as e:
                                pass
                            users[id]['status'] = 'online' # Задаем статус пользователя "онлайн"
                            print(
                                f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} Подключился пользователь {' '.join(user)}")

                            break
                        else:
                            bot.send_message(message.chat.id, text='Такого работника нет в моей базе данных. Обратитесь к вашему руководству')
                    elif user[2] == '': # Если chat_id пустой
                        if cfg.check_chat_id(chat_id) == False:
                            cfg.add_chat_id(message.chat.id, tabel)
                            bot.send_message(message.chat.id,text=f"Здравствуйте, <b>{user[0]}!</b>\n\nВыберите услугу", reply_markup = keyboards.kb_main_menu())
                            users[id]['status'] = 'online'
                            print(
                                f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} Подключился пользователь {' '.join(user)}")

                            break
                        else: bot.send_message(message.chat.id, text=f'У вас уже есть аккаунт. Не пытайтесь притворяться!')
                    else:
                        if user[2] == id:
                            bot.send_message(message.chat.id,text=f"Здравствуйте, <b>{user[0]}!</b>\n\nВыберите услугу", reply_markup = keyboards.kb_main_menu())
                            users[id]['status'] = 'online'
                            print(
                                f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} Подключился пользователь ({' | '.join(user)})")
                            break
                        else:
                            bot.send_message(message.chat.id, text='Введите свой табельный номер!')
                else:
                    bot.send_message(message.chat.id, text='Таб. номер содержит только цифры!')
            else:
                menu_builder(message)
    
    update_user_activity(str(message.chat.id))


#  """ПОСТРОЕНИЕ МЕНЮ ПОСЛЕ АВТОРИЗАЦИИ ПОЛЬЗОВАТЕЛЯ"""
def menu_builder(message):
    for id in users:
        if str(message.chat.id) == id:
            if users[id]['status'] == 'online':
                if message.text == '🔍 Поиск электродвигателя':
                    bot.send_message(message.chat.id, text='По какому критерию?', reply_markup = keyboards.search_criteria())

                elif message.text == '🌐 Обзор установленных двигателей':
                    bot.send_message(message.chat.id, text='Эта функция временно не доступна.')

                elif message.text == 'Поиск по инвентарному номеру':
                    msg = bot.send_message(message.chat.id, text='Введите инвентарный номер двигателя.', reply_markup = keyboards.btn_back())
                    bot.register_next_step_handler(msg, find_by_number)

                elif message.text == 'Поиск по мощности':
                    msg = bot.send_message(message.chat.id, text='Введите желаемую мощность (кВт).', reply_markup = keyboards.btn_back())
                    bot.register_next_step_handler(msg, find_by_power_first_step)

                elif message.text == '🔙 Назад':
                    bot.send_message(message.chat.id, text='Назад', reply_markup = keyboards.kb_main_menu())

                else: 
                    bot.send_message(message.chat.id, text='Я не понимаю. Выберите функцию на всплывающей клавиатуре.')


#  """ФУНКЦИЯ ПОИСКА ПО ИНВЕНТАРНОМУ НОМЕРУ ДВИГАТЕЛЯ"""
def find_by_number(message):
    inv_num = message.text
    if inv_num.isdigit():
        vehicle = cfg.get_vehicle_by_number(inv_num)
        if len(vehicle[0][0]) < 100 or vehicle is not None: # Проверка на пустой ответ от БД
            bot.send_photo(message.chat.id, 
                            #photo = open(f'{path.join(path.dirname(__file__), f'{cfg.get_image(vehicle[5])}')}', 'rb'), caption=f'<b>Инв. №: <u> F-{vehicle[0]} </u>\nНаименование: <u> {vehicle[1]} </u>\nМощность: <u> {vehicle[2]}кВт </u>\nВольтаж: <u> {vehicle[3]}В </u>\nМестоположение: <u> {vehicle[4]} </u>\nСтатус: <u> {vehicle[5]} </u></b>',
                           # Открытие файла с фотографией
                           photo=open(f'{cfg.get_image(vehicle[5])}', 'rb'),
                           # Создание подписи к фотографии
                           caption=f"<b>Инв. №: <u> F-{vehicle[0]} </u>\nНаименование: <u> {vehicle[1]} </u>\nМощность: <u> {vehicle[2]}кВт </u>\nВольтаж: <u> {vehicle[3]}В </u>\nМестоположение: <u> {vehicle[4]} </u>\nСтатус: <u> {vehicle[5]} </u></b>",

                           reply_markup=keyboards.ikb_vehicle())
            bot.send_message(message.chat.id, text='Отлично. Что дальше?', reply_markup = keyboards.search_criteria())
        else: 
            msg = bot.send_message(message.chat.id, text='Нет такого двигателя. Может вы ошиблись?\nНапишите ещё раз.')
            bot.register_next_step_handler(msg, find_by_number)
    else:
        if message.text == '🔙 Назад':
            bot.send_message(message.chat.id, text='Назад', reply_markup = keyboards.kb_main_menu())
        else:
            msg = bot.send_message(message.chat.id, text='Введите числовое значение')
            bot.register_next_step_handler(msg, find_by_number)


#  """ФУНКЦИЯ ДЛЯ ПОИСКА ДВИГАТЕЛЕЙ ПО МОЩНОСТИ (ввод мощности)"""
def find_by_power_first_step(message):
    global kw
    kw = message.text
    if kw.replace('.','',1).isdigit():
        msg = bot.send_message(message.chat.id, text='Выберите необходимый статус', reply_markup = keyboards.kb_search_by_status())
        bot.register_next_step_handler(msg, find_by_power_second_step)
    else:
        if message.text == '🔙 Назад':
            bot.send_message(message.chat.id, text='Назад', reply_markup = keyboards.kb_main_menu())
        else:
            msg = bot.send_message(message.chat.id, text='Введите числовое значение мощности!')
            bot.register_next_step_handler(msg, find_by_power_first_step)


#  """ФУНКЦИЯ ДЛЯ ПОИСКА ДВИГАТЕЛЕЙ ПО МОЩНОСТИ (выбор статуса)"""
def find_by_power_second_step(message):
    global status
    if message.text == 'Установленные':
        status = 5
    elif message.text == 'В резерве':
        status = 1
    elif message.text == 'На ремонте':
        status = 10
    elif message.text == 'Списанные':
        status = 6
    elif message.text == 'Все':
        status = '*'
    else:
        status = 0

    find_by_power_final_step(message)


#  """ФУНКЦИЯ ДЛЯ ПОИСКА ДВИГАТЕЛЕЙ ПО МОЩНОСТИ (вывод по заданным критериям)"""
def find_by_power_final_step(message):
    if status != 0:
        vehicle_list = cfg.get_vehicle_by_power(kw, status)
        if len(vehicle_list[0][0]) < 100 or vehicle_list is not None: # То же, что и в find_by_number()
            bot.send_message(message.chat.id, text=f'Список двигателей мощностью {kw} кВт:', reply_markup = keyboards.kb_main_menu())
            for vehicle in vehicle_list:
                # open(f'{path.join(path.dirname(__file__), f'{cfg.get_image(vehicle[5])}')}', 'rb') - для localhost
                bot.send_photo(message.chat.id,
                               photo=open(f'{cfg.get_image(vehicle[5])}', 'rb'),
                               caption=f'<b>Инв. №: <u> F-{vehicle[0]} </u>\nНаименование: <u> {vehicle[1]} </u>\nМощность: <u> {vehicle[2]}кВт </u>\nВольтаж: <u> {vehicle[3]}В </u>\nМестоположение: <u> {vehicle[4]} </u>\nСтатус: <u> {vehicle[5]} </u></b>',
                               reply_markup = keyboards.ikb_vehicle())
        else: 
            bot.send_message(message.chat.id, text='Нет двигателей по выбранным критериям!', reply_markup = keyboards.kb_main_menu())
    else:
        msg = bot.send_message(message.chat.id, text='Я тебя не понимаю. Выберите критерий из всплывающей клавиатуры')
        bot.register_next_step_handler(msg, find_by_power_second_step)


#  """КОЛЛБЕКИ НА ИЗМЕНЕНИЕ СТАТУСА ДВИГАТЕЛЯ"""
@bot.callback_query_handler(func = lambda call: True)
def change_status(call):
    if call.data == 'mainmenu':
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup = keyboards.ikb_vehicle())

    if call.data == 'change_status':
        if 'Инструкции' not in call.message.caption:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup = keyboards.vehicle_status_change(0))
        else:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup = keyboards.vehicle_status_change(1))

    if call.data == 'get_more':
        if 'Инструкции' in call.message.caption:
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup = keyboards.ikb_vehicle())
        else:
            get_more(call, call.message.message_id, call.message.caption)

    for id in users:
        if str(call.message.chat.id) == id:
            if users[id]['status'] == 'online':
                if call.data == 'take_place':
                    inv_num = call.message.caption.split()[2][2:]
                    cfg.change_status(inv_num, 5)
                    cfg.insert_history_status(inv_num, call.message.chat.id, 5, 1)
                    bot.send_message(call.message.chat.id, text=f'<b>Двигатель <u> F-{inv_num} </u>\nУстановлен статус <u> "Установлен" </u></b>')

                if call.data == 'repair':
                    inv_num = call.message.caption.split()[2][2:]
                    cfg.change_status(inv_num, 10)
                    cfg.insert_history_status(inv_num, call.message.chat.id, 10, 1)
                    bot.send_message(call.message.chat.id, text=f'<b>Двигатель <u> F-{inv_num} </u>\nУстановлен статус <u> "На ремонте" </u></b>')

                if call.data == 'reserve':
                    inv_num = call.message.caption.split()[2][2:]
                    cfg.change_status(inv_num, 1)
                    cfg.insert_history_status(inv_num, call.message.chat.id, 1, 1)
                    bot.send_message(call.message.chat.id, text=f'<b>Двигатель <u> F-{inv_num} </u>\nУстановлен статус <u> "В резерве" </u></b>')

                if call.data == 'off':
                    inv_num = call.message.caption.split()[2][2:]
                    cfg.change_status(inv_num, 6)
                    cfg.insert_history_status(inv_num, call.message.chat.id, 6, 1)
                    bot.send_message(call.message.chat.id, text=f'<b>Двигатель <u> F-{inv_num} </u>\nУстановлен статус <u> "Списан" </u></b>')
            else: 
                    bot.send_message(call.message.chat.id, text='У вас нет доступа!\n\nВойдите, чтобы изменять данные')


#  """ФУНКЦИЯ РЕАГИРУЮЩАЯ НА НАЖАТИЕ КНОПКИ ПОДРОБНЕЕ"""
def get_more(call, message_id, old_text):
    url = 'https://google.kz'
    more = f'Инструкции: {url}\nComing soon...'

    markup = types.InlineKeyboardMarkup()
    status_btn = types.InlineKeyboardButton('Изменить статус', callback_data='change_status')
    markup.add(status_btn)

    # open(f'{path.join(path.dirname(__file__), './img/engine1.jpg')}', "rb") - для localhost
    media = types.InputMediaPhoto(open(f"{cfg.get_image('any_status')}", "rb"), caption=old_text + '\n' + more)
    bot.edit_message_media(media , call.message.chat.id, message_id, reply_markup = markup)


#  """ФУНКЦИЯ ОПОВЕЩЕНИЯ АДМИНИСТРАТОРОВ ОБ ИЗМЕНЕНИЯХ"""
def notify_admin(txt=''):
    print(f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} БОТ ЗАПУЩЕН")

    while True:
        admin_list = cfg.get_admins()
        txt = cfg.notification_message()
        if txt[0][0].startswith('<br') or txt is None: # Пустое текстовое оповещение
            pass
        else:
            print(re.sub(r'<[^>]*>', '', txt[0][0]).replace('\n', ' ')) # Убираем HTML теги и переносы для вывода в консоль в одну строку
            pass
            
            for admin in admin_list:
                try:
                    for m in txt:
                        bot.send_message(admin[4], text=m[0])
                except:
                    print(
                        f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} ERROR: {admin[1]} {admin[2]} не оповещен. Отсутствует или неверно указан chat_id в таблице log_auth_var")

                    continue

        check_and_disconnect_inactive_users()
        time.sleep(15) # Время проверки новых сообщений/изменений


#  """ФУНКЦИЯ ПРОВЕРКИ НЕАКТИВНЫХ ПОЛЬЗОВАТЕЛЕЙ"""
def check_and_disconnect_inactive_users():
    current_time = datetime.now().time()

    for user, activity in users.items():
        if activity['status'] == 'online':
            last_activity_time = activity['last_activity_time']
            time_difference = datetime.combine(datetime.today(), current_time) - datetime.combine(datetime.today(), last_activity_time)
            if time_difference > inactive_timeout:
                activity['status'] = 'offline'
                print(f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} Пользователь {user} отключен по причине неактивности")


#  """ФУНКЦИЯ ОБНОВЛЕНИЯ ПОСЛЕДНЕЙ АКТИВНОСТИ ПОЛЬЗОВАТЕЛЯ"""
def update_user_activity(user):
    users[user]['last_activity_time'] = datetime.now().time()


if __name__ == '__main__':
    t1 = threading.Thread(target=bot.infinity_polling)
    t2 = threading.Thread(target=notify_admin)
    t1.start()
    t2.start()
    t1.join()
    t2.join()