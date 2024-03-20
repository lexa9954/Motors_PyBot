from telebot import types
import cfg
import keyboards
from os import path
import threading
import time

bot = cfg.telebot.TeleBot(cfg.BOT_TOKEN, parse_mode='HTML')
user_online = False

print('БОТ ЗАПУЩЕН')

@bot.message_handler(commands=['start'])
def start(message):
    mesg = bot.send_message(message.chat.id, text="Введите табельный номер")
    bot.register_next_step_handler(mesg, auth)



@bot.message_handler(content_types=['text'])
def auth(message):
    global user_online
    if not user_online:
        if message.text.isdigit():
            tabel = message.text
            user = cfg.select_user(tabel)
            if user is None: # Если пользователь не существует в log_auth_var
                if cfg.check_user_true(tabel):
                    cfg.sign_up(str(message.chat.id), tabel)
                    bot.send_message(message.chat.id,text=f"Здравствуйте, <b>{user[0]}!</b>\n\nВыберите услугу", reply_markup = keyboards.kb_main_menu())
                    user_online = True
                else:
                    bot.send_message(message.chat.id, text='Такого работника нет в моей базе данных. Обратитесь к вашему руководству')
            elif user[2] == '': # Если chat_id пустой
                if cfg.check_chat_id(str(message.chat.id)) == False:
                    cfg.add_chat_id(message.chat.id, tabel)
                    bot.send_message(message.chat.id,text=f"Здравствуйте, <b>{user[0]}!</b>\n\nВыберите услугу", reply_markup = keyboards.kb_main_menu())
                    user_online = True
                else: bot.send_message(message.chat.id, text=f'У вас уже есть аккаунт. Не пытайтесь притворяться!')
            else:
                bot.send_message(message.chat.id,text=f"Здравствуйте, <b>{user[0]}!</b>\n\nВыберите услугу", reply_markup = keyboards.kb_main_menu())
                user_online = True
        else:
            bot.send_message(message.chat.id, text='Таб. номер содержит только цифры!')
    else:
        menu_builder(message)


def menu_builder(message):
    global user_online
    if user_online:  # Проверка на авторизацию
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


def find_by_number(message):
    inv_num = message.text
    if inv_num.isdigit():
        vehicle = cfg.get_vehicle_by_number(inv_num)
        if vehicle is None:
            bot.send_photo(
                message.chat.id,
                photo=open(f'{path.join(path.dirname(__file__), cfg.get_image(vehicle[5]))}', 'rb'),
                caption=f'<b>Инв. №: <u> F-{vehicle[0]} </u>\nНаименование: <u> {vehicle[1]} </u>\nМощность: <u> {vehicle[2]}кВт </u>\nВольтаж: <u> {vehicle[3]}В </u>\nМестоположение: <u> {vehicle[4]} </u>\nСтатус: <u> {vehicle[5]} </u></b>',
                reply_markup=keyboards.ikb_vehicle()
            )
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


# Группа функций(3) для пошагового поиска по мощности 
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

def find_by_power_final_step(message):
    if status != 0:
        vehicle_list = cfg.get_vehicle_by_power(kw, status)
        if vehicle_list is None:
            bot.send_message(message.chat.id, text=f'Список двигателей мощностью {kw} кВт:', reply_markup = keyboards.kb_main_menu())
            for vehicle in vehicle_list:
                bot.send_photo(
                    message.chat.id,
                    photo=open(f"{path.join(path.dirname(__file__), cfg.get_image(vehicle[5]))}", "rb"),
                    caption=f"<b>Инв. №: <u> F-{vehicle[0]} </u>\nНаименование: <u> {vehicle[1]} </u>\nМощность: <u> {vehicle[2]}кВт </u>\nВольтаж: <u> {vehicle[3]}В </u>\nМестоположение: <u> {vehicle[4]} </u>\nСтатус: <u> {vehicle[5]} </u></b>",
                    reply_markup=keyboards.ikb_vehicle()
                )
        else: 
            bot.send_message(message.chat.id, text='Нет двигателей по выбранным критериям!', reply_markup = keyboards.kb_main_menu())
    else:
        msg = bot.send_message(message.chat.id, text='Я тебя не понимаю. Выберите критерий из всплывающей клавиатуры')
        bot.register_next_step_handler(msg, find_by_power_second_step)




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

    if user_online:
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


def get_more(call, message_id, old_text):  # Функция реагирующая на нажатие кнопки "Подробнее"
    url = 'https://google.kz'
    more = f'Инструкции: {url}\nComing soon...'

    markup = types.InlineKeyboardMarkup()
    status_btn = types.InlineKeyboardButton('Изменить статус', callback_data='change_status')
    markup.add(status_btn)

    media = types.InputMediaPhoto(open(f"{path.join(path.dirname(__file__), './img/engine1.jpg')}", "rb"),
                                  caption=old_text + '\n' + more)
    bot.edit_message_media(media , call.message.chat.id, message_id, reply_markup = markup)


def notify_admin(txt=None):  # Оповещения админов
    while True:
        print("Получение списка администраторов...")
        admin_list = cfg.get_admins()  # Получаем список администраторов из конфигурации
        print("Список администраторов:", admin_list)

        print("Получение текста уведомления...")
        txt = cfg.notification_message()  # Получаем текст уведомления из конфигурации
        print("Текст уведомления:", txt)
        if txt is None:
            print("Пропускаем отправку.")
        # Проверяем, начинается ли первое уведомление с тега <br>. Если да, ничего не делаем.
        else:
            # Для каждого администратора в списке администраторов отправляем каждое уведомление из списка уведомлений.
            for admin in admin_list:
                for m in txt:
                    print(f"Отправка сообщения админу {admin[4]}:", m[0])
                    bot.send_message(admin[4], text=m[0])
                    print("Сообщение успешно отправлено.")

        # Ожидаем 15 секунд перед повторным выполнением
        print("Ожидание 15 секунд перед следующим оповещением...")
        time.sleep(15)


if __name__ == '__main__':
    t1 = threading.Thread(target=bot.polling)
    t2 = threading.Thread(target=notify_admin)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    print('БОТ ЗАПУЩЕН')