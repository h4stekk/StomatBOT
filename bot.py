import telebot
import sqlite3

# Підключення до бази даних SQLite
db = sqlite3.connect('appointments.db')
cursor = db.cursor()

# Створення таблиці для записів на прийом
cursor.execute('''
    CREATE TABLE IF NOT EXISTS appointments(
        id INTEGER PRIMARY KEY,
        user_id INTEGER,
        info TEXT
    )
''')
db.commit()

# Токен вашого бота
bot = telebot.TeleBot('6966032832:AAEmMho8Q_FAZ5EH4xR_QhNa7wZg5lZw408')

# Створення списку для зберігання дат та часів, встановлених адміном
admin_appointments = []

# Пароль адміна
admin_password = "159753"  # Замініть "159753" на власний пароль

# Стан для перевірки авторизації адміна
waiting_for_info = {}

# Функція для обробки введення паролю адміном
def admin_login(message):
    user_id = message.chat.id
    password = message.text.strip()

    if password == admin_password:
        admin_panel(message)
    else:
        bot.send_message(user_id, "Невірний пароль для доступу до адмін-панелі.")

# Функція для обробки вибору дій в адмін-панелі
def admin_actions(message):
    user_id = message.chat.id
    if message.text == 'Додати запис на прийом':
        msg = bot.send_message(user_id, "Введіть нову дату та час для запису:")
        bot.register_next_step_handler(msg, process_admin_input)
    elif message.text == 'Вийти з адмін панелі':
        admin_appointments.clear()
        waiting_for_info.pop(user_id, None)  # Видаляємо очікування команди для цього користувача
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton('Записатися на прийом'), telebot.types.KeyboardButton('Подивитися запис'))
        bot.send_message(user_id, "Ви вийшли з адмін панелі.", reply_markup=markup)
    elif message.text == 'Переглянути всі записи':
        view_all_appointments(message)
    else:
        bot.send_message(user_id, "Невідома команда.")


# Перевірка пароля адміна
def check_admin_password(message):
    user_id = message.chat.id
    if message.text == admin_password:
        admin_appointments.clear()
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(telebot.types.KeyboardButton('Додати запис на прийом'), telebot.types.KeyboardButton('Вийти з адмін панелі'), telebot.types.KeyboardButton('Переглянути всі записи'))
        msg = bot.send_message(user_id, "Ви увійшли до адмін панелі. Оберіть дію:", reply_markup=markup)
        bot.register_next_step_handler(msg, admin_actions)
    else:
        bot.send_message(user_id, "Неправильний пароль. Спробуйте ще раз.")

# Обробник дій в адмін панелі
@bot.message_handler(commands=['admin'])
def admin_panel(message):
  waiting_for_info[message.chat.id] = True
  markup = telebot.types.ReplyKeyboardRemove()
  msg = bot.send_message(message.chat.id, "Введіть пароль:", reply_markup=markup)
  bot.register_next_step_handler(msg, check_admin_password)


# Функція для обробки введення нової дати та часу адміном
def process_admin_input(message):
    new_appointment = message.text
    admin_appointments.append(new_appointment)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Додати запис на прийом'), telebot.types.KeyboardButton('Вийти з адмін панелі'), telebot.types.KeyboardButton('Переглянути всі записи'))
    bot.send_message(message.chat.id, f"Дата та час {new_appointment} додані для запису.", reply_markup=markup)
    waiting_for_info.pop(message.chat.id, None)

# Функція для перегляду всіх записів на прийом
def view_all_appointments(message):
    user_id = message.chat.id

    # Створення нового з'єднання з базою даних для цього конкретного виклику
    db = sqlite3.connect('appointments.db')
    cursor = db.cursor()

    # Отримання всіх записів на прийом з бази даних
    cursor.execute("SELECT * FROM appointments")
    appointments = cursor.fetchall()

    db.close()  # Закриваємо з'єднання після використання

    if appointments:
        appointments_list = "\n".join(str(appointment

) for appointment in appointments)
        bot.send_message(user_id, f"Всі записи на прийом:\n{appointments_list}")
    else:
        bot.send_message(user_id, "У базі даних немає записів на прийом.")

# Обробник команди /start для звичайного користувача та адміна
@bot.message_handler(commands=['start'])
def start(message):
    user_id = message.chat.id
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(telebot.types.KeyboardButton('Записатися на прийом'), telebot.types.KeyboardButton('Подивитися запис'))
    bot.send_message(user_id, "Ви увійшли знову.", reply_markup=markup)

# Обробник кнопки "Записатися на прийом"
@bot.message_handler(func=lambda message: message.text == 'Записатися на прийом')
def make_appointment(message):
    if admin_appointments:
        markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
        for appointment in admin_appointments:
            markup.add(telebot.types.KeyboardButton(appointment))

        msg = bot.send_message(message.chat.id, "Оберіть дату та час для запису:", reply_markup=markup)
        bot.register_next_step_handler(msg, process_appointment_choice)
    else:
        bot.send_message(message.chat.id, "Адмін ще не встановив доступні дати та часи для запису.")

# Обробник вибору дати та часу для запису користувачем
def process_appointment_choice(message):
    user_id = message.chat.id
    appointment_choice = message.text

    if appointment_choice in admin_appointments:
        waiting_for_info[user_id] = appointment_choice
        msg = bot.send_message(user_id, "Будь ласка, введіть своє ПІБ:")
        bot.register_next_step_handler(msg, process_user_name)
    else:
        bot.send_message(user_id, "Будь ласка, оберіть доступну дату та час для запису.")

# Обробник введення ПІБ користувача
def process_user_name(message):
    user_id = message.chat.id
    user_name = message.text

    waiting_for_info[user_id] += f"\nПІБ: {user_name}"
    msg = bot.send_message(user_id, "Будь ласка, введіть свій номер телефону:")
    bot.register_next_step_handler(msg, process_phone_number)

# Обробник введення номеру телефону користувача
def process_phone_number(message):
    user_id = message.chat.id
    phone_number = message.text

    waiting_for_info[user_id] += f"\nНомер телефону: {phone_number}"

    # Отримання інформації про запис користувача
    appointment_info = waiting_for_info.pop(user_id)

    # Створення нового з'єднання з базою даних для цього конкретного виклику
    db = sqlite3.connect('appointments.db')
    cursor = db.cursor()

    cursor.execute("INSERT INTO appointments (user_id, info) VALUES (?, ?)", (user_id, appointment_info))
    db.commit()
    db.close()  # Закриваємо з'єднання після використання

    bot.send_message(user_id, f"Ви успішно записалися на прийом:\n{appointment_info}")


# Обробник кнопки "Подивитися запис"
@bot.message_handler(func=lambda message: message.text == 'Подивитися запис')
def view_appointments(message):
    user_id = message.chat.id

    # Створення нового з'єднання з базою даних для цього конкретного виклику
    db = sqlite3.connect('appointments.db')
    cursor = db.cursor()

    # Отримання записів користувача за його ID
    cursor.execute("SELECT info FROM appointments WHERE user_id = ?", (user_id,))
    appointments = cursor.fetchall()

    db.close()  # Закриваємо з'єднання після використання

    if appointments:
        appointments_list = "\n".join(str(appointment[0]) for appointment in appointments)
        bot.send_message(user_id, f"Ваші записи на прийом:\n{appointments_list}")
    else:
        bot.send_message(user_id, "Ви ще не маєте записів на прийом.")
# Запуск бота
bot.polling()
