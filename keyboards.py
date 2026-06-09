from aiogram.types import (
    ReplyKeyboardMarkup, 
    KeyboardButton, 
    InlineKeyboardMarkup, 
    InlineKeyboardButton
)


def get_main_keyboard(is_admin_user=False):
    """Главная клавиатура"""
    buttons = [
        [KeyboardButton(text="🐾 Категории товаров")],
        [KeyboardButton(text="🛒 Корзина"), KeyboardButton(text="📦 Мои заказы")],
        [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="ℹ️ Помощь")]
    ]
    
    if is_admin_user:
        buttons.append([KeyboardButton(text="🔧 Админ-панель")])
    
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_categories_keyboard(categories):
    """Клавиатура с категориями"""
    keyboard = []
    row = []
    
    for i, cat in enumerate(categories):
        row.append(KeyboardButton(text=f"{cat['icon']} {cat['category_name']}"))
        if len(row) == 2 or i == len(categories) - 1:
            keyboard.append(row)
            row = []
    
    keyboard.append([KeyboardButton(text="◀️ Главное меню")])
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_products_keyboard(products):
    """Клавиатура с товарами (инлайн)"""
    keyboard = []
    
    for product in products:
        keyboard.append([
            InlineKeyboardButton(
                text=f"{product['name']} - {product['price']}₽", 
                callback_data=f"product_{product['product_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="◀️ Назад к категориям", callback_data="back_to_categories")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_product_detail_keyboard(product_id):
    """Клавиатура для деталей товара"""
    keyboard = [
        [
            InlineKeyboardButton(text="➖", callback_data=f"dec_{product_id}"),
            InlineKeyboardButton(text="1", callback_data=f"qty_{product_id}_1"),
            InlineKeyboardButton(text="➕", callback_data=f"inc_{product_id}")
        ],
        [
            InlineKeyboardButton(text="🛒 Добавить в корзину", callback_data=f"add_{product_id}")
        ],
        [
            InlineKeyboardButton(text="◀️ Назад к товарам", callback_data=f"back_to_products_{product_id}")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_cart_keyboard(cart_items):
    """Клавиатура для корзины"""
    keyboard = []
    
    for item in cart_items:
        keyboard.append([
            InlineKeyboardButton(
                text=f"❌ {item['name']} x{item['quantity']}",
                callback_data=f"remove_{item['cart_id']}"
            )
        ])
    
    keyboard.append([InlineKeyboardButton(text="🔄 Очистить корзину", callback_data="clear_cart")])
    keyboard.append([InlineKeyboardButton(text="✅ Оформить заказ", callback_data="checkout")])
    keyboard.append([InlineKeyboardButton(text="◀️ Продолжить покупки", callback_data="continue_shopping")])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_orders_keyboard(orders):
    """Клавиатура для истории заказов"""
    keyboard = []
    
    for order in orders:
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'shipped': '🚚',
            'delivered': '✅',
            'cancelled': '❌'
        }.get(order['status'], '📦')
        
        keyboard.append([
            InlineKeyboardButton(
                text=f"{status_emoji} Заказ #{order['order_id']} - {order['total_amount']}₽",
                callback_data=f"order_{order['order_id']}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard) if keyboard else None


def get_admin_keyboard():
    """Клавиатура для админ-панели"""
    keyboard = [
        [KeyboardButton(text="➕ Добавить товар")],
        [KeyboardButton(text="📋 Список товаров")],
        [KeyboardButton(text="📦 Все заказы")],
        [KeyboardButton(text="👥 Пользователи")],
        [KeyboardButton(text="◀️ Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_admin_orders_keyboard(orders):
    """Клавиатура для заказов в админ-панели"""
    keyboard = []
    
    for order in orders:
        keyboard.append([
            InlineKeyboardButton(
                text=f"Заказ #{order['order_id']} - {order['first_name']}",
                callback_data=f"admin_order_{order['order_id']}"
            )
        ])
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_admin_order_actions_keyboard(order_id):
    """Клавиатура действий с заказом для админа"""
    keyboard = [
        [
            InlineKeyboardButton(text="⏳ В обработке", callback_data=f"status_{order_id}_processing"),
            InlineKeyboardButton(text="🚚 Отправлен", callback_data=f"status_{order_id}_shipped")
        ],
        [
            InlineKeyboardButton(text="✅ Доставлен", callback_data=f"status_{order_id}_delivered"),
            InlineKeyboardButton(text="❌ Отменён", callback_data=f"status_{order_id}_cancelled")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_contact_keyboard():
    """Клавиатура для запроса контакта"""
    keyboard = [
        [KeyboardButton(text="📱 Отправить номер телефона", request_contact=True)],
        [KeyboardButton(text="◀️ Главное меню")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)


def get_address_keyboard():
    """Клавиатура для запроса адреса"""
    keyboard = [
        [KeyboardButton(text="◀️ Отмена")]
    ]
    return ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)