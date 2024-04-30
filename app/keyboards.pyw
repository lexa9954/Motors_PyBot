from telebot import types

def kb_main_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width = 1)
    item1 = types.KeyboardButton('🔍 Поиск электродвигателя')
    item2 = types.KeyboardButton('🌐 Обзор установленных двигателей')
    markup.add(item1, item2)

    return markup

def search_criteria():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    item1 = types.KeyboardButton('Поиск по инвентарному номеру')
    item2 = types.KeyboardButton('Поиск по мощности')
    item3 = types.KeyboardButton('🔙 Назад')
    markup.add(item1, item2, item3)

    return markup

def btn_back():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1, one_time_keyboard=True)
    item1 = types.KeyboardButton('🔙 Назад')
    markup.add(item1)

    return markup

def kb_search_by_status():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=3)
    item1 = types.KeyboardButton('Установленные')
    item2 = types.KeyboardButton('В резерве')
    item3 = types.KeyboardButton('На ремонте')
    item4 = types.KeyboardButton('Списанные')
    item5 = types.KeyboardButton('Все')
    markup.add(item1, item2, item3, item4, item5)

    return markup

def ikb_vehicle():
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton('Изменить статус', callback_data='change_status')
    item2 = types.InlineKeyboardButton('Подробнее', callback_data='get_more')
    markup.add(item1, item2)

    return markup

def vehicle_status_change(answer):
    markup = types.InlineKeyboardMarkup(row_width=3)
    item1 = types.InlineKeyboardButton('Установить', callback_data='take_place')
    item2 = types.InlineKeyboardButton('В ремонт', callback_data='repair')
    item3 = types.InlineKeyboardButton('В резерв', callback_data='reserve')
    item4 = types.InlineKeyboardButton('Списать', callback_data='off')
    item5 = types.InlineKeyboardButton('🔙 Назад', callback_data='mainmenu')
    markup.add(item1, item2, item3, item4)
    if answer == 0:
        markup.add(item5)

    return markup