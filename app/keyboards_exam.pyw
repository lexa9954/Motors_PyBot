from telebot import types

def kb_main_menu_admin():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width = 1)
    item1 = types.KeyboardButton('Показать список неаттестованных работников')
    markup.add(item1)

    return markup

def kb_main_menu_user():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width = 1)
    item1 = types.KeyboardButton('Когда мне сдавать экзамен?')
    markup.add(item1)

    return markup

def kb_main_menu_boss_user():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width = 1)
    item1 = types.KeyboardButton('Показать список моих неаттестованных работников')
    item2 = types.KeyboardButton('Когда мне сдавать экзамен?')
    markup.add(item1,item2)

    return markup

def exam_done_bt(people_id, type_quest_id):
    markup = types.InlineKeyboardMarkup()
    item1 = types.InlineKeyboardButton('Я сдал экзамен', callback_data=f'exam_done|{people_id}|{type_quest_id}')
    markup.add(item1)
    
    return markup