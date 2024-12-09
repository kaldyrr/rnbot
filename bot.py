#py 3.13.0
import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import nltk
from nltk.tokenize import word_tokenize
from rapidfuzz import process
from transliterate import translit
'''import openai
openai.api_key = "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"
'''
nltk.data.path.append(r'C:\Users\vadim\AppData\Roaming\nltk_data')
nltk.download('punkt')
API_TOKEN = '7908700715:AAHtgQnR0HmmRIo-kRMfHkox1-SloNkqMFc'
bot = telebot.TeleBot(API_TOKEN)
SHEET_NAME = 'Rn'
CREDENTIALS_FILE = 'credentials.json'
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_name(CREDENTIALS_FILE, scope)
client = gspread.authorize(credentials)
sheet = client.open(SHEET_NAME).sheet1 
rows = sheet.get_all_values()
product_data = []
for row in rows[1:]:
    product_data.append({
        "product_name": row[0].strip().lower(),  
        "stock": int(row[1]) if row[1].isdigit() else 0, 
        "price": row[2] if len(row) > 2 else None 
    })

'''@bot.message_handler(commands=['get_chat_id'])
def send_chat_id(message):
    user_id = message.chat.id
    bot.send_message(user_id, f"Ваш chat_id: {user_id}")'''

'''
"""                                ИНТЕГРАЦИЯ AI                              """


def query_openai(prompt, model="gpt-3.5-turbo"):
    """
    Отправляет запрос в OpenAI API и возвращает ответ.
    """
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "system", "content": "Ты помощник для обработки запросов по товарам."},
                      {"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        return response["choices"][0]["message"]["content"].strip()
    except Exception as e:
        print(f"Ошибка при работе с OpenAI API: {e}")
        return "Извините, я не понял. Попробуйте снова."

# Пример: обработка пользовательского запроса
def handle_user_query_with_openai(user_input):
    """
    Обрабатывает запрос пользователя с помощью OpenAI и возвращает результат.
    """
    prompt = f"""
    У меня есть база товаров. Я ищу товар, который соответствует запросу: "{user_input}".
    Пожалуйста, подбери наиболее подходящие результаты из базы данных.
    Вот пример формата базы: 
    - Товар: Kasta Смородина , Цена: 500, Остаток: 1555
    - Товар: Iceberg Дыня Малина , Цена: 800, Остаток: 15
    """
    return query_openai(prompt)

def get_relevant_products_from_ai(user_input):
    # Генерируем строку с товарами
    product_list = "\n".join([f"- Товар: {p['product_name']}, Цена: {p['price']}, Остаток: {p['stock']}" for p in product_data])

    # Генерируем запрос для OpenAI
    prompt = f"""
    У меня есть база товаров:
    {product_list}

    Пользователь ищет: "{user_input}".
    Помоги выбрать подходящие товары из базы.
    """
    return query_openai(prompt)

@bot.message_handler(func=lambda message: True)
def process_order_with_ai_and_db(message):
    user_input = message.text
    user_id = message.chat.id

    # Получаем результат из OpenAI
    ai_response = get_relevant_products_from_ai(user_input)

    # Отправляем пользователю результат
    bot.send_message(user_id, f"По вашему запросу я нашел:\n\n{ai_response}")


@bot.message_handler(func=lambda message: True)
def process_order_with_openai(message):
    user_input = message.text
    user_id = message.chat.id

    # Отправляем запрос в OpenAI
    ai_response = handle_user_query_with_openai(user_input)

    # Показываем результат пользователю
    bot.send_message(user_id, f"Вот что я нашел по вашему запросу:\n\n{ai_response}")


"""                                ИНТЕГРАЦИЯ AI3                             """
'''
#Меню
def send_main_menu(user_id):
    """
    Отправляет главное меню с кнопками.
    """
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    markup.add(
        KeyboardButton("📚 Каталог"),
        KeyboardButton("🛒 Корзина")
    )
    bot.send_message(user_id, "Выберите действие:", reply_markup=markup)

#грузим каталог
def get_catalog():
    catalog = {}
    for product in product_data:
        category = product['product_name'].split()[0]
        if category not in catalog:
            catalog[category] = []
        catalog[category].append(product)
    return catalog

def send_categories(user_id, message_id=None):
    catalog = get_catalog()
    markup = InlineKeyboardMarkup()
    for category in catalog.keys():
        markup.add(InlineKeyboardButton(category, callback_data=f"category_{category}"))
    message_text = "Выберите категорию:"
    if message_id:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=message_text,
            reply_markup=markup
        )
    else:
        bot.send_message(user_id, message_text, reply_markup=markup)
def send_products_in_category(user_id, category, message_id=None):
    catalog = get_catalog()
    products = catalog.get(category, [])
    if not products:
        bot.send_message(user_id, "В этой категории пока нет товаров.")
        return
    message = f"📦 Товары в категории *{category}*:\n"
    markup = InlineKeyboardMarkup(row_width=1)
    for product in products:
        product_name = product['product_name']
        price = product['price']
        stock = product['stock']

        message += f"- {product_name} (Цена: {price}, Остаток: {stock})\n"
        markup.add(InlineKeyboardButton(f"Купить {product_name}", callback_data=f"buy_{product_name}"))
    
    # Кнопка возврата к категориям
    markup.add(InlineKeyboardButton("⬅️ Назад к категориям", callback_data="back_to_categories"))

    if message_id:
        bot.edit_message_text(
            chat_id=user_id,
            message_id=message_id,
            text=message,
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        bot.send_message(user_id, message, reply_markup=markup, parse_mode="Markdown")

def normalize_product_name(name):
    return translit(name, reversed=True).lower() 

def analyze_query_nltk(user_input):
    words = word_tokenize(user_input.lower())  
    items = []
    current_quantity = None
    product_parts = []

    for word in words:
        if word.isdigit():  
            if current_quantity and product_parts:
                product_name = " ".join(product_parts).strip()
                items.append({"quantity": current_quantity, "product": product_name})
                product_parts = []  
            current_quantity = int(word)  
        else:
            product_parts.append(word)  

    if current_quantity and product_parts:
        product_name = " ".join(product_parts).strip()
        items.append({"quantity": current_quantity, "product": product_name})

    return items

def check_availability(extracted_items):
    available_items = []
    unavailable_items = []
    product_list = [normalize_product_name(row['product_name']) for row in product_data]
    for item in extracted_items:
        normalized_input = normalize_product_name(item["product"])
        best_match, score, *_ = process.extractOne(normalized_input, product_list)
        if score >= 70:  # Условие: если совпадение >= 70%
            # Найдём продукт в product_data
            best_match_name = product_data[product_list.index(best_match)]['product_name']
            product_info = next((p for p in product_data if p['product_name'] == best_match_name), None)
            if product_info:
                if product_info['stock'] >= item["quantity"]:
                    available_items.append({
                        "product": best_match_name,
                        "quantity": item["quantity"],
                        "price": product_info['price']
                    })
                else:
                    unavailable_items.append(
                        f"{item['product']} (доступно только {product_info['stock']})"
                    )
        else:
            unavailable_items.append(item["product"])
    return available_items, unavailable_items
user_cart = {}
user_cart_message = {}
def add_to_cart(user_id, item):
    if user_id not in user_cart:
        user_cart[user_id] = []
    existing_item = next((i for i in user_cart[user_id] if i['product'] == item['product']), None)
    product_info = next((p for p in product_data if p['product_name'] == item['product']), None)
    if not product_info:
        return False  
    available_stock = product_info['stock']
    if existing_item:
        if existing_item['quantity'] + item['quantity'] > available_stock:
            return False  # Нельзя добавить
        existing_item['quantity'] += item['quantity']
    else:
        if item['quantity'] > available_stock:
            return False  # Нельзя добавить
        user_cart[user_id].append(item)
    return True

def calculate_cart(user_id):
    cart = user_cart.get(user_id, [])
    total = 0
    details = []
    for item in cart:
        price = item['price'].replace('₽', '').replace(' ', '').strip()
        
        try:
            price = int(price)
        except ValueError:
            price = 0
        
        total += price * item['quantity']
        details.append(f"{item['quantity']} x {item['product']} (Цена: {price} ₽)")
    
    return total, details

def remove_from_cart(user_id, product_name):
    if user_id in user_cart:
        user_cart[user_id] = [item for item in user_cart[user_id] if item['product'] != product_name]
        return True
    return False

def clear_cart(user_id):
    if user_id in user_cart:
        user_cart[user_id] = []
        return True
    return False

def update_stock(product_name, quantity):
    for row_idx, row in enumerate(rows[1:], start=2):
        if row[0].strip().lower() == product_name:
            stock = int(row[1]) - quantity
            sheet.update_cell(row_idx, 2, max(0, stock))
            return

def process_quantity(message, product_name):

    user_id = message.chat.id
    try:
        quantity = int(message.text)
        if quantity <= 0:
            raise ValueError("Количество должно быть положительным числом.")

        product_info = next((p for p in product_data if p['product_name'] == product_name), None)
        if product_info and product_info['stock'] >= quantity:
            item = {
                "product": product_name,
                "quantity": quantity,
                "price": product_info['price']
            }
            add_to_cart(user_id, item)

            if user_id in user_cart_message:
                send_cart_buttons(user_id, user_cart_message[user_id])
            else:
                msg = bot.send_message(user_id, "📦 Ваша корзина:")
                user_cart_message[user_id] = msg.message_id
                send_cart_buttons(user_id, msg.message_id)

            bot.send_message(user_id, f"✅ {quantity} шт. '{product_name}' добавлено в корзину.")
        else:
            bot.send_message(user_id, f"❌ Недостаточно товара '{product_name}' на складе.")
    except ValueError:
        bot.send_message(user_id, "❌ Введите корректное количество.")

def send_cart_buttons(user_id, message_id=None):

    cart = user_cart.get(user_id, [])
    if not cart:
        bot.edit_message_text(
            chat_id=user_id, 
            message_id=message_id, 
            text="❌ Ваша корзина пуста!",
            reply_markup=None
        )
        return

    total, details = calculate_cart(user_id)
    order_details = "\n".join(details)
    message_text = f"📦 Ваш заказ:\n{order_details}\n\nИтого: {total} ₽"

    markup = InlineKeyboardMarkup(row_width=1)

    for item in cart:
        product_name = item['product']
        markup.add(InlineKeyboardButton(f"🗑 Удалить {product_name}", callback_data=f"remove_{product_name}"))

    markup.add(
        InlineKeyboardButton("🛒✅ Оформить заказ", callback_data="confirm_order"),
        InlineKeyboardButton("❌ Очистить корзину", callback_data="clear_cart")
    )

    if message_id:
        bot.edit_message_text(
            chat_id=user_id, 
            message_id=message_id, 
            text=message_text, 
            reply_markup=markup
        )
    else:
        bot.send_message(user_id, message_text, reply_markup=markup)


#отправление заказов в лички менеджеров
def notify_manager(user_id, username, order_details, total):
    manager_ids = [434412508,]  # Чат ID всех менеджеров Артур - 673456311 , Вадим - 434412508
    contact_info = f"@{username}" if username else f"ID: {user_id}"
    
    for manager_id in manager_ids:
        try:
            bot.send_message(
                manager_id,
                f"🛒 Новый заказ от пользователя {contact_info}:\n{order_details}\nИтого: {total} ₽"
            )
        except telebot.apihelper.ApiTelegramException as e:
            print(f"Ошибка при отправке сообщения менеджеру {manager_id}: {e}")

#Обработчики бота -------------------------------------------------------------------------
#------------------------------------------------------------------------------------------

@bot.message_handler(commands=['start'])
def handle_start(message):

    user_id = message.chat.id
    bot.send_message(user_id, "Добро пожаловать! Кнопкой снизу можно открыть каталог, при заказе обязательно указывать количество товара! Например 4 касты смородина")
    send_main_menu(user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("category_"))
def handle_category_selection(call):

    category = call.data.split("_", 1)[1]  # Получаем название категории
    send_products_in_category(call.message.chat.id, category, message_id=call.message.message_id)

@bot.callback_query_handler(func=lambda call: call.data == "back_to_categories")
def handle_back_to_categories(call):

    send_categories(call.message.chat.id, message_id=call.message.message_id)

@bot.message_handler(func=lambda message: message.text == "🛒 Корзина")
def handle_cart_button(message):

    user_id = message.chat.id
    if user_id not in user_cart or not user_cart[user_id]:
        bot.send_message(user_id, "❌ Ваша корзина пуста!")
        return
    total, details = calculate_cart(user_id)
    order_details = "\n".join(details)
    message_text = f"📦 Ваш заказ:\n{order_details}\n\nИтого: {total} ₽"

    markup = InlineKeyboardMarkup(row_width=1)
    for item in user_cart[user_id]:
        product_name = item['product']
        markup.add(InlineKeyboardButton(f"🗑 Удалить {product_name}", callback_data=f"remove_{product_name}"))
    markup.add(
        InlineKeyboardButton("🛒✅ Оформить заказ", callback_data="confirm_order"),
        InlineKeyboardButton("❌ Очистить корзину", callback_data="clear_cart")
    )
    # Отправляем сообщение с корзиной
    bot.send_message(user_id, message_text, reply_markup=markup)

@bot.message_handler(commands=['catalog'])
def show_catalog(message):
    send_categories(message.chat.id)

@bot.message_handler(func=lambda message: "📚 каталог" in message.text.lower())
def handle_catalog_button(message):
    show_catalog(message)
    
@bot.message_handler(func=lambda message: True)
def process_order(message):
    user_input = message.text
    user_id = message.chat.id
    extracted_items = analyze_query_nltk(user_input)
    available_items, unavailable_items = check_availability(extracted_items)
    for item in available_items:
        add_to_cart(user_id, item)
    if available_items:
        total, details = calculate_cart(user_id)
        order_details = "\n".join(details)
        send_cart_buttons(user_id)
    else:
        bot.send_message(user_id, "❌ Не удалось найти товары: " + ", ".join(unavailable_items))
        if unavailable_items:
            bot.send_message(user_id, "Возможно, вы имели в виду:\n" + "\n".join([f"{item} (предложение)" for item in unavailable_items]))

# Оформление заказа
@bot.callback_query_handler(func=lambda call: call.data == "confirm_order")
def handle_confirm_order(call):

    user_id = call.message.chat.id
    username = call.from_user.username

    if user_id not in user_cart or not user_cart[user_id]:
        bot.answer_callback_query(call.id, "❌ Ваша корзина пуста!")
        return

    total, details = calculate_cart(user_id)
    order_details = "\n".join(details)

    # Обновление остатков
    for item in user_cart[user_id]:
        update_stock(item['product'], item['quantity'])

    clear_cart(user_id)

    # Уведомление пользователя
    bot.edit_message_text(
        chat_id=user_id,
        message_id=call.message.message_id,
        text=f"✅ Заказ передан менеджеру для подтверждения!\n\n{order_details}\nИтого: {total} ₽"
    )

    # Уведомление менеджеров
    notify_manager(user_id, username, order_details, total)

    send_main_menu(user_id)

@bot.callback_query_handler(func=lambda call: call.data.startswith("remove_"))
def handle_remove_item(call):
    user_id = call.message.chat.id
    product_name = call.data.split("remove_", 1)[1]

    if remove_from_cart(user_id, product_name):
        bot.answer_callback_query(call.id, f"Товар '{product_name}' удалён из корзины.")
        send_cart_buttons(user_id, call.message.message_id)
    else:
        bot.answer_callback_query(call.id, f"Товар '{product_name}' не найден в корзине.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy_product(call):
    user_id = call.message.chat.id
    product_name = call.data.split("buy_", 1)[1]

    product_info = next((p for p in product_data if p['product_name'] == product_name), None)
    if not product_info:
        bot.answer_callback_query(call.id, "❌ Товар не найден!")
        return

    msg = bot.send_message(user_id, f"Сколько единиц '{product_name}' вы хотите купить?")
    bot.register_next_step_handler(msg, process_quantity, product_name)
    bot.answer_callback_query(call.id)

@bot.callback_query_handler(func=lambda call: call.data == "clear_cart")
def handle_clear_cart(call):
    user_id = call.message.chat.id
    if clear_cart(user_id):
        bot.answer_callback_query(call.id, "Корзина очищена!")

        if user_id in user_cart_message:
            bot.edit_message_text(
                chat_id=user_id,
                message_id=user_cart_message[user_id],
                text="❌ Корзина пуста!",
                reply_markup=None
            )
            del user_cart_message[user_id]
    else:
        bot.answer_callback_query(call.id, "Корзина уже пуста.")


bot.polling()
