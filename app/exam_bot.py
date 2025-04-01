import threading
import time
import  keyboards_exam
from datetime import datetime

from datetime import datetime


import cfg
from pyexpat.errors import messages
from telebot import TeleBot

from auth import auth, users  # Импортируем auth и users

# Инициализация бота с токеном из cfg
bot = TeleBot(cfg.BOT_TOKEN_EXAM, parse_mode='HTML')
url = cfg.URL

# Обработчик всех текстовых сообщений
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_id = str(message.chat.id)

    # Проверяем авторизацию пользователя
    if user_id not in users or users[user_id]['status'] == 'offline':
        ask_for_tabel_number(message)
        return

    # Определяем роль пользователя
    user_role = users[user_id].get('role', 'user')

    # Генерация клавиатуры в зависимости от роли
    if user_role == 'admin':
        reply_markup = keyboards_exam.kb_admin_menu()  # Клавиатура для админов
    else:
        reply_markup = keyboards_exam.kb_user_menu()  # Клавиатура для пользователей

    # Ответ на сообщение
    if message.text == 'Не прошедшие аттестацию ❗':
        show_overdue(message)
    elif message.text == 'Подлежащие аттестации в этом месяце ⏳':
        show_submit_list(message)
    else:
        bot.send_message(message.chat.id, "Что Вас интересует:", reply_markup=reply_markup)

# Обработка кнопки "Показать просрочки"
def show_overdue(message):
    bot.send_message(message.chat.id, 'Выбор экзамена', reply_markup=keyboards_exam.kb_select_exam(), parse_mode='HTML')

# Обработка кнопки "Кому необходимо сдать"
def show_submit_list(message):
    bot.send_message(message.chat.id, "Вот список тех, кому необходимо сдать...")



# Функция для запроса табельного номера
def ask_for_tabel_number(message):
    # Отправляем сообщение и ждем ввода табельного номера
    mesg = bot.send_message(message.chat.id, text="Введите табельный номер:")

    # Регистрируем шаг для ввода табельного номера
    bot.register_next_step_handler(mesg, handle_tabel_number)


# Обработчик ввода табельного номера
def handle_tabel_number(message):
    # Обрабатываем табельный номер и возвращаем результат из функции auth()
    result = auth(message)  # Вызов функции auth, которая возвращает сообщение для отправки

    # Если в result есть сообщение, то отправляем его обратно пользователю
    if 'info' in result:
        bot.send_message(message.chat.id, result['info'], reply_markup=keyboards_exam.kb_main_menu_user(), parse_mode='HTML')



def check_user_exam():
    query = '''SELECT 
    peoples.id AS people_id,
    COALESCE(org_structure_groups.group_name, 'Не указано') AS group_name,
    COALESCE(org_structure_positions.position_name, 'Не указана') AS position_name,
    COALESCE(org_structure_positions.id, 0) AS position_id,
    COALESCE(elect_group, 0) AS elect_group,
    COALESCE(log_auth_var.chat_id, 0) AS chat_id,
    COALESCE(Exam_date.Protocol_num, 'Не указан') AS Protocol_num,
    COALESCE(peoples.first_name, 'Без имени') AS first_name,
    COALESCE(peoples.last_name, 'Без фамилии') AS last_name,
    COALESCE(peoples.second_name, '-') AS second_name,
    Exam_typeQuest.Type_quest_text AS Type_quest_text,
    COALESCE(Exam_date.type_quest_id, 0) AS type_quest_id,
    COALESCE(Exam_date.success_quest_percent, 0) AS success_quest_percent,
    COALESCE(Exam_date.last_date, '1900-01-01') AS last_date,
    Exam_date.time_exam,
    peoples.TabNumberSap,
    CASE
        WHEN CURDATE() >= DATE_ADD(Exam_date.last_date, INTERVAL 1 YEAR) THEN 'Просрочено'
        WHEN CURDATE() >= DATE_ADD(Exam_date.last_date, INTERVAL 11 MONTH) THEN 'Остался месяц или меньше'
        WHEN Exam_date.success_quest_percent < 70 THEN 'Не сдал экзамен'
        ELSE 'Успешно'
    END AS exam_status,
    COALESCE(org_structure.org_structure_id, 0) AS org_structure_id
FROM 
    Exam_date
JOIN 
    peoples ON peoples.id = Exam_date.people_id
JOIN 
    Exam_typeQuest ON Exam_typeQuest.id = Exam_date.type_quest_id
LEFT JOIN 
    org_structure ON org_structure.id = peoples.str_org_structure
LEFT JOIN 
    org_structure_positions ON org_structure_positions.id = org_structure.str_pos_id
LEFT JOIN 
    org_structure_groups ON org_structure_groups.id = org_structure.str_group_id
LEFT JOIN 
    log_auth_var ON log_auth_var.id_people = peoples.id
WHERE 
    Exam_date.last_date = (
        SELECT MAX(Exam_date2.last_date)
        FROM Exam_date AS Exam_date2
        WHERE Exam_date2.people_id = peoples.id
        AND Exam_date2.type_quest_id = Exam_date.type_quest_id
    )
    AND peoples.status_id != 1
    AND peoples.elect_group != 1 
    AND peoples.elect_group != 5
    AND Exam_date.type_quest_id != 4
    AND Exam_date.type_quest_id != 3
    AND peoples.status_id = 0 
    
    AND (
        Exam_date.success_quest_percent < 70
        OR CURDATE() >= DATE_ADD(Exam_date.last_date, INTERVAL 1 YEAR)
        OR CURDATE() >= DATE_ADD(Exam_date.last_date, INTERVAL 11 MONTH)
    )
ORDER BY 
    Exam_date.last_date DESC;
'''

    try:
        users_exam = cfg.execute_query(url+query, 18)
        print("Результат выполнения запроса:")
        #print(users_exam)
        if not users_exam:
            print("Данные отсутствуют.")
        return users_exam
    except Exception as e:
        print("Ошибка при выполнении запроса:", e)
        return ''

def format_date(date_str,fail):
    from datetime import datetime

    # Преобразование строки в объект datetime
    date_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    date_obj_plus_one_year = date_obj
    if fail !=True:
        try:
            # Добавляем 1 год
            date_obj_plus_one_year = date_obj.replace(year=date_obj.year + 1)
        except ValueError:
            # Если дата 29 февраля (високосный год), переместить на 28 февраля
            date_obj_plus_one_year = date_obj.replace(year=date_obj.year + 1, day=28)

    # Форматирование новой даты (день.месяц.год)
    return date_obj_plus_one_year.strftime("%d.%m.%Y")  # Пример: "13.12.2025"


def get_fails_message(type_msg, org_structure_id):
    exam_fails = check_user_exam()
    if exam_fails:  # Проверяем, что результат не пустой
        # Заголовок сообщения
        header = "📋 Список пользователей на сдачу экзаменов по электробезопасности:\n\n"

        # Инициализируем таблицы
        overdue_table = "<b>❗ Не прошедшие аттестацию:</b>\n<pre>"
        overdue_table += f"{'ФИО':<20} | {'Дата':<10}\n"
        overdue_table += f"{'-' * 20} | {'-' * 10}\n"

        soon_expire_table = "<b>⚠️ Подлежащие аттестации в этом месяце:</b>\n<pre>"
        soon_expire_table += f"{'ФИО':<20} | {'Дата':<10}\n"
        soon_expire_table += f"{'-' * 20} | {'-' * 10}\n"

        for fail in exam_fails:
            # Формат ФИО: "Фамилия И.О."
            fio = f"{fail[8]} {fail[7][0]}.{fail[9][0]}."
            if len(fio) > 20:  # Урезаем ФИО, если слишком длинное
                fio = fio[:17] + "..."

            success_percent = float(fail[12])

            if success_percent >= 70:
                date = format_date(fail[13], False)  # Форматируем дату
            else:
                date = format_date(fail[13], True)  # Форматируем дату и прибавляем 1 год

            # Добавляем в нужную таблицу в зависимости от статуса
            if fail[16] == 'Просрочено':
                overdue_table += f"{fio:<20} | {date:<10}\n"
            elif fail[16] == 'Остался месяц или меньше':
                soon_expire_table += f"{fio:<20} | {date:<10}\n"

        overdue_table += "</pre>\n\n" if "ФИО" not in overdue_table else "</pre>"
        soon_expire_table += "</pre>" if "ФИО" not in soon_expire_table else "</pre>"

        # Объединяем сообщение
        return header + overdue_table + soon_expire_table
    else:
        return "✅ Все экзамены сданы вовремя!"

#  """ФУНКЦИЯ ОПОВЕЩЕНИЯ АДМИНИСТРАТОРОВ ОБ ИЗМЕНЕНИЯХ"""
def notify_users():
    print(f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} БОТ ЗАПУЩЕН")

    while True:
            # Уведомляем администраторов
            admin_list = cfg.get_admins()
            for admin in admin_list:
                try:
                    messages = get_fails_message("admins",-1)
                    print("Уведомление в бот " + admin[1] + " " + admin[2])
                    print(messages)
                    bot.send_message(admin[4], text=messages, parse_mode="HTML")
                    #for message in messages:
                        #print("Уведомление в бот "+admin[1]+" "+admin[2])
                        #print(message)
                        #bot.send_message(admin[4], text=message, parse_mode="HTML")
                except Exception as e:
                    print(
                        f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} "
                        f"ERROR: Администратор {admin[1]} {admin[2]} не оповещён. Ошибка: {e}")
                    continue
            # Уведомляем пользователей
            people_list = cfg.get_people()
            for people in people_list:
                try:
                    messages = get_fails_message("peoples",people[5])
                    print("Уведомление в бот " + people[1] + " " + people[2])
                    print(messages)
                    bot.send_message(people[4], text=messages, parse_mode="HTML")
                    #print(f"Пользователь {people[1]} {people[2]} оповещён.")
                    #for message in messages:
                        #print("Уведомление в бот "+people[1]+" "+people[2])
                        #print(message)
                        #bot.send_message(people[4], text=message, parse_mode="HTML")
                except Exception as e:
                    print(
                        f"{datetime.now().date()} | {datetime.now().strftime('%H:%M:%S')} "
                        f"ERROR: Пользователь {people[1]} {people[2]} не оповещён. Ошибка: {e}")
                    continue
            # Задержка перед следующим циклом (проверка раз в час)
            time.sleep(86400)  # Проверка раз в час

# Запуск бота
def run_bot():
    print("БОТ ЭКЗАМЕН НАЧАЛ РАБОТУ.....")
    try:
        notify = threading.Thread(target=notify_users)
        notify.start()
        bot.infinity_polling()  # Запуск бесконечного опроса без потоков
        notify.join()
    except KeyboardInterrupt:
        print("БОТ ЭКЗАМЕН ОСТАНОВЛЕН")




# Запуск бота при выполнении файла
if __name__ == '__main__':
    run_bot()