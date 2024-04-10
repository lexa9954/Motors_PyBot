import requests
import telebot
from telebot import apihelper


URL = 'http://10.21.199.88/php_app_query.php?query='
BOT_TOKEN = '6956463991:AAHMWaqjs3ZiOlDGYcWnrRsFcgwsbklqUv8'
apihelper.proxy = {'https':'amt_portal:Welcome%4012345@10.21.199.198:8080'}


def send_request(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Поднимает исключение, если статус не 200
        return response.text
    except requests.exceptions.HTTPError as http_err:
        print(f'HTTP error occurred: {http_err}')  # Например, "404 Not Found" или "500 Internal Server Error".
    except requests.exceptions.ConnectionError:
        print('Что-то пошло не так, возможно отсутствует интернет соединение.')
    except Exception as err:
        print(f'Произошла ошибка: {err}')
    return None

def execute_query(query, col):
    str_response = send_request(query)  # Используем функцию send_request, определенную ранее
    if not str_response:
        return None

    rows = str_response.split('&')
    response = []

    for row in rows:
        if row:  # проверяем, не пустая ли строка
            col_row = row.split(';')
            response.append(col_row[:col] if len(col_row) >= col else col_row + [''] * (col - len(col_row)))

    return response if response else None

def execute_query_read(query, col):
    # предполагается, что `query` - это URL для запроса
    str_response = send_request(query)
    response = str_response.split(';')

    if str_response == "":
        return None
    else:
        return response
    

def get_image(status):
    if status == 'Установлен':
        return './img/install.png'
    
    elif status == 'Резерв':
        return './img/reserve.png'
    
    elif status == 'На ремонте':
        return './img/repair.png'
    
    elif status == 'Списан':
        return './img/off.png'
    
    else: return './img/engine1.jpg'


def select_user(tabnumber):
    query = f'''SELECT first_name, tabnumbersap, chat_id, permission
                        FROM peoples
                        INNER JOIN log_auth_var 
                        ON peoples.id = log_auth_var.id_people 
                        WHERE tabnumbersap={tabnumber}'''
    response = execute_query_read(URL+query, 4)
    return response
    

def get_admins():
    query = '''SELECT peoples.id, first_name, last_name, tabnumbersap, chat_id FROM peoples 
                        INNER JOIN log_auth_var ON peoples.id = log_auth_var.id_people 
                        WHERE permission="ADMIN"'''
    response = execute_query(URL+query, 5)
    return response


def get_vehicle_by_number(inv_num):
    query = f'''SELECT inventory_num, name_mat, power, voltage, aggregete_name, status_name FROM materials
                        INNER JOIN motors ON motors.id_mat = materials.id
                        INNER JOIN motor_objects ON motor_objects.motor_id = motors.id
                        INNER JOIN all_aggregates ON all_aggregates.id = motor_objects.aggregate_id
                        INNER JOIN all_status ON all_status.id = motor_objects.status_id
                        WHERE inventory_num={inv_num}'''
    response = execute_query_read(URL+query, 6)
    return response


def get_vehicle_by_power(kw, status):
    if status == '*':
        query = f'''SELECT inventory_num, name_mat, power, voltage, aggregete_name, status_name FROM materials
                        INNER JOIN motors ON motors.id_mat = materials.id
                        INNER JOIN motor_objects ON motor_objects.motor_id = motors.id
                        INNER JOIN all_aggregates ON all_aggregates.id = motor_objects.aggregate_id
                        INNER JOIN all_status ON all_status.id = motor_objects.status_id
                        WHERE power={kw}'''
    else:
        query = f'''SELECT inventory_num, name_mat, power, voltage, aggregete_name, status_name FROM materials
                        INNER JOIN motors ON motors.id_mat = materials.id
                        INNER JOIN motor_objects ON motor_objects.motor_id = motors.id
                        INNER JOIN all_aggregates ON all_aggregates.id = motor_objects.aggregate_id
                        INNER JOIN all_status ON all_status.id = motor_objects.status_id
                        WHERE power={kw} AND motor_objects.status_id={status}'''
    response = execute_query(URL+query, 6)
    return response


def change_status(inv_num, status):
    query = f'''UPDATE motor_objects
                        INNER JOIN motors ON motors.id = motor_objects.motor_id
                        INNER JOIN materials ON materials.id = motors.id_mat
                        SET status_id = {status}
                        WHERE motor_objects.inventory_num = {inv_num}'''
    response = execute_query_read(URL+query, 1)
    return response


def insert_history_status(inv_num, chat_id, status_id, state):
    motorObj_id = execute_query_read(URL+f'SELECT id FROM motor_objects WHERE inventory_num = {inv_num}', 1)
    people_id = execute_query_read(URL+f'SELECT id_people FROM log_auth_var WHERE chat_id = {chat_id}', 1)
    query = f'''INSERT INTO history_motor_status (motorObject_id, date_status, people_id, status_id, state_id) 
                VALUES ({motorObj_id[0]}, CURRENT_DATE(), {people_id[0]}, {status_id}, {state})'''
    response = execute_query(URL+query, 1)

    people = execute_query_read(URL+f'SELECT First_name, Last_name FROM peoples WHERE id = {people_id[0]}', 2)
    status = execute_query_read(URL+f'SELECT status_name FROM all_status WHERE id = {status_id}', 1)
    time = execute_query_read(URL+f'SELECT CURRENT_DATE(), CURRENT_TIME()', 2)

    text = f'{time[0]} | {time[1]}\n<b>{people[0]} {people[1]}</b>\nустановил статус двигателя <u>F-{inv_num}</u> на "{status[0]}"'
    insert_telegram_commands(text)
    print(text)
    print('-------------------------------------')
    
    return response


def insert_telegram_commands(text):
    query = f'''INSERT INTO telegram_commands (bot_id, text)
                VALUES ('{BOT_TOKEN}','{text}')'''
    response = execute_query_read(URL+query, 1)

    return response
    

def sign_up(chat_id, tabel):
    people_id_list = execute_query(URL+f'SELECT id_people, chat_id FROM log_auth_var', 2)
    user_id = execute_query_read(URL+f'SELECT id FROM peoples WHERE tabnumbersap = {tabel}', 1)

    for people in people_id_list:
        if user_id[0] not in people[0]:
            execute_query(URL+f'''INSERT INTO log_auth_var (id_people, activate, password, first_pass, chat_id)
                                VALUES ({user_id[0]}, 1, 123, 1, {chat_id})''', 1)
            print(f'Зарегистрировался пользователь ТАБ. № {tabel}')
            break


def add_chat_id(chat_id, tabel):
    query = f'''UPDATE log_auth_var
                        INNER JOIN peoples ON peoples.id = log_auth_var.id_people
                        SET chat_id = {chat_id}
                        WHERE peoples.TabNumberSAP = {tabel}'''
    response = execute_query_read(URL+query, 1)
    print(f'Добавлен chat_id для пользователя ТАБ. № {tabel}')
    return response


def check_chat_id(chat_id): # Проверка есть ли chat_id пользователя в БД
    chat_ids = execute_query(URL+f'SELECT chat_id FROM log_auth_var', 1)
    
    for id in chat_ids:
        if chat_id == id[0]:
            return True
    
    return False


def check_user_true(tabel):  # Проверка существует ли вообще пользователь
    query = f'''SELECT tabnumbersap FROM peoples WHERE tabel = {tabel}'''
    response = execute_query(URL+query, 1)

    if response[0][0].startswith('<br'):
        return False
    else: return True

def notification_message():
    txt = execute_query(URL+'SELECT text FROM telegram_commands WHERE viewed = 0', 1)

    execute_query(URL+'UPDATE telegram_commands SET viewed = 1 WHERE viewed = 0', 1)

    return txt