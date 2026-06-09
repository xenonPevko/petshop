import logging
from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery, ReplyKeyboardRemove
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database import (
    add_user, get_user, update_user_info, init_db,
    get_all_categories, get_products_by_category, get_product_by_id, get_all_products,
    add_product, delete_product, update_product_stock,
    add_to_cart, get_cart, remove_from_cart, update_cart_quantity, clear_cart,
    create_order, get_user_orders, get_order_items, get_all_orders, update_order_status,
    add_admin, is_admin
)
from keyboards import (
    get_main_keyboard, get_categories_keyboard, get_products_keyboard,
    get_product_detail_keyboard, get_cart_keyboard, get_orders_keyboard,
    get_admin_keyboard, get_admin_orders_keyboard, get_admin_order_actions_keyboard,
    get_contact_keyboard, get_address_keyboard
)
from config import ADMIN_SECRET_CODE

router = Router()
logger = logging.getLogger(__name__)


# ==================== СОСТОЯНИЯ ДЛЯ FSM ====================

class AddProductStates(StatesGroup):
    waiting_for_category = State()
    waiting_for_name = State()
    waiting_for_description = State()
    waiting_for_price = State()
    waiting_for_stock = State()


class CheckoutStates(StatesGroup):
    waiting_for_phone = State()
    waiting_for_address = State()


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def format_price(price):
    return f"{price:,.0f}".replace(",", " ")


# ==================== КОМАНДЫ ДЛЯ ВСЕХ ПОЛЬЗОВАТЕЛЕЙ ====================

@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    existing_user = get_user(user.id)
    
    if not existing_user:
        add_user(user.id, user.first_name)
    
    await message.answer(
        f"🐾 Привет, {user.first_name}!\n\n"
        "Добро пожаловать в зоомагазин «Хвостик»!\n\n"
        "🐶 У нас вы найдёте:\n"
        "• Качественные корма\n"
        "• Безопасные игрушки\n"
        "• Удобные аксессуары\n"
        "• Средства гигиены\n\n"
        "Используй кнопки меню для покупок!",
        reply_markup=get_main_keyboard(is_admin(message.from_user.id))
    )


@router.message(F.text == "◀️ Главное меню")
async def back_to_main(message: Message):
    await message.answer(
        "Главное меню:",
        reply_markup=get_main_keyboard(is_admin(message.from_user.id))
    )


@router.message(F.text == "🐾 Категории товаров")
async def show_categories(message: Message):
    categories = get_all_categories()
    
    if not categories:
        await message.answer("Категории временно недоступны")
        return
    
    await message.answer(
        "Выберите категорию товаров:",
        reply_markup=get_categories_keyboard(categories)
    )


@router.message(lambda msg: msg.text and any(
    msg.text.endswith(cat['category_name']) 
    for cat in get_all_categories()
))
async def show_products_by_category(message: Message):
    # Извлекаем название категории из кнопки (убираем эмодзи)
    full_text = message.text
    category_name = full_text.split(" ", 1)[-1] if " " in full_text else full_text
    
    categories = get_all_categories()
    selected_category = None
    
    for cat in categories:
        if cat['category_name'] == category_name:
            selected_category = cat
            break
    
    if not selected_category:
        await message.answer("Категория не найдена")
        return
    
    products = get_products_by_category(selected_category['category_id'])
    
    if not products:
        await message.answer(f"В категории «{category_name}» пока нет товаров")
        return
    
    await message.answer(
        f"📦 Товары в категории «{category_name}»:",
        reply_markup=get_products_keyboard(products)
    )


@router.callback_query(F.data.startswith("product_"))
async def show_product_detail(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    product = get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден", show_alert=True)
        return
    
    text = (
        f"📦 *{product['name']}*\n\n"
        f"📝 {product['description']}\n\n"
        f"💰 Цена: {format_price(product['price'])}₽\n"
        f"📦 В наличии: {product['stock']} шт.\n\n"
        f"Выберите количество и добавьте в корзину:"
    )
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_product_detail_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("inc_"))
async def increase_quantity(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    
    # Получаем текущий callback message и извлекаем текущее количество
    message_text = callback.message.text
    lines = message_text.split("\n")
    
    current_qty = 1
    for line in lines:
        if "Количество:" in line:
            try:
                current_qty = int(line.split(":")[-1].strip())
            except:
                pass
            break
    
    new_qty = current_qty + 1
    
    # Обновляем текст сообщения
    new_text = []
    for line in lines:
        if "Количество:" in line:
            new_text.append(f"Количество: {new_qty}")
        elif "Добавьте" in line:
            pass
        else:
            new_text.append(line)
    
    new_text.append(f"\nВыберите количество и добавьте в корзину:")
    
    await callback.message.edit_text(
        "\n".join(new_text),
        parse_mode="Markdown",
        reply_markup=get_product_detail_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("dec_"))
async def decrease_quantity(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    
    message_text = callback.message.text
    lines = message_text.split("\n")
    
    current_qty = 1
    for line in lines:
        if "Количество:" in line:
            try:
                current_qty = int(line.split(":")[-1].strip())
            except:
                pass
            break
    
    new_qty = max(1, current_qty - 1)
    
    new_text = []
    for line in lines:
        if "Количество:" in line:
            new_text.append(f"Количество: {new_qty}")
        elif "Добавьте" in line:
            pass
        else:
            new_text.append(line)
    
    new_text.append(f"\nВыберите количество и добавьте в корзину:")
    
    await callback.message.edit_text(
        "\n".join(new_text),
        parse_mode="Markdown",
        reply_markup=get_product_detail_keyboard(product_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("add_"))
async def add_to_cart_callback(callback: CallbackQuery):
    product_id = int(callback.data.split("_")[1])
    user = get_user(callback.from_user.id)
    
    if not user:
        await callback.answer("Сначала запустите бота /start", show_alert=True)
        return
    
    # Извлекаем количество из сообщения
    message_text = callback.message.text
    quantity = 1
    
    for line in message_text.split("\n"):
        if "Количество:" in line:
            try:
                quantity = int(line.split(":")[-1].strip())
            except:
                pass
            break
    
    product = get_product_by_id(product_id)
    
    if product['stock'] < quantity:
        await callback.answer(f"Извините, в наличии только {product['stock']} шт.", show_alert=True)
        return
    
    add_to_cart(user['user_id'], product_id, quantity)
    
    await callback.answer(f"✓ Товар добавлен в корзину! ({quantity} шт.)", show_alert=True)
    
    # Возвращаемся к списку товаров в категории
    # Сохраняем категорию в данных (в реальном приложении нужно хранить)
    await callback.message.delete()
    await callback.message.answer("Товар добавлен в корзину! Можете продолжить покупки.")


@router.callback_query(F.data == "back_to_categories")
async def back_to_categories(callback: CallbackQuery):
    categories = get_all_categories()
    await callback.message.edit_text(
        "Выберите категорию товаров:",
        reply_markup=get_categories_keyboard(categories)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("back_to_products_"))
async def back_to_products(callback: CallbackQuery):
    # В реальном приложении нужно сохранять category_id
    # Для простоты покажем все товары
    products = get_all_products()
    if products:
        await callback.message.edit_text(
            "📦 Товары:",
            reply_markup=get_products_keyboard(products[:10])
        )
    await callback.answer()


@router.message(F.text == "🛒 Корзина")
async def show_cart(message: Message):
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Сначала запустите бота /start")
        return
    
    cart_items = get_cart(user['user_id'])
    
    if not cart_items:
        await message.answer("🛒 Ваша корзина пуста\n\nДобавьте товары через «Категории товаров»")
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    text = "🛒 *Ваша корзина:*\n\n"
    for item in cart_items:
        text += f"• {item['name']} x{item['quantity']} = {format_price(item['price'] * item['quantity'])}₽\n"
    
    text += f"\n*Итого: {format_price(total)}₽*"
    
    await message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_cart_keyboard(cart_items)
    )


@router.callback_query(F.data.startswith("remove_"))
async def remove_cart_item(callback: CallbackQuery):
    cart_id = int(callback.data.split("_")[1])
    remove_from_cart(cart_id)
    
    await callback.answer("Товар удалён из корзины")
    
    # Обновляем отображение корзины
    user = get_user(callback.from_user.id)
    cart_items = get_cart(user['user_id'])
    
    if not cart_items:
        await callback.message.edit_text("🛒 Корзина пуста")
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    text = "🛒 *Ваша корзина:*\n\n"
    for item in cart_items:
        text += f"• {item['name']} x{item['quantity']} = {format_price(item['price'] * item['quantity'])}₽\n"
    
    text += f"\n*Итого: {format_price(total)}₽*"
    
    await callback.message.edit_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_cart_keyboard(cart_items)
    )


@router.callback_query(F.data == "clear_cart")
async def clear_cart_callback(callback: CallbackQuery):
    user = get_user(callback.from_user.id)
    clear_cart(user['user_id'])
    
    await callback.message.edit_text("🛒 Корзина очищена")
    await callback.answer("Корзина очищена")


@router.callback_query(F.data == "checkout")
async def start_checkout(callback: CallbackQuery, state: FSMContext):
    user = get_user(callback.from_user.id)
    cart_items = get_cart(user['user_id'])
    
    if not cart_items:
        await callback.answer("Корзина пуста", show_alert=True)
        return
    
    if user['phone']:
        # Если номер уже есть, спрашиваем адрес
        await state.update_data(phone=user['phone'])
        await callback.message.answer(
            "📝 Укажите адрес доставки:",
            reply_markup=get_address_keyboard()
        )
        await state.set_state(CheckoutStates.waiting_for_address)
    else:
        await callback.message.answer(
            "📱 Пожалуйста, поделитесь своим номером телефона для связи:",
            reply_markup=get_contact_keyboard()
        )
        await state.set_state(CheckoutStates.waiting_for_phone)
    
    await callback.answer()


@router.message(CheckoutStates.waiting_for_phone, F.contact)
async def get_phone(message: Message, state: FSMContext):
    phone = message.contact.phone_number
    await state.update_data(phone=phone)
    
    # Сохраняем номер в БД
    update_user_info(message.from_user.id, phone=phone)
    
    await message.answer(
        "📝 Укажите адрес доставки:",
        reply_markup=get_address_keyboard()
    )
    await state.set_state(CheckoutStates.waiting_for_address)


@router.message(CheckoutStates.waiting_for_phone, F.text)
async def get_phone_text(message: Message, state: FSMContext):
    # Если пользователь отправил текст вместо контакта
    phone = message.text
    await state.update_data(phone=phone)
    update_user_info(message.from_user.id, phone=phone)
    
    await message.answer(
        "📝 Укажите адрес доставки:",
        reply_markup=get_address_keyboard()
    )
    await state.set_state(CheckoutStates.waiting_for_address)


@router.message(CheckoutStates.waiting_for_address, F.text)
async def get_address(message: Message, state: FSMContext):
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer(
            "Оформление заказа отменено",
            reply_markup=get_main_keyboard(is_admin(message.from_user.id))
        )
        return
    
    address = message.text
    data = await state.get_data()
    phone = data.get('phone')
    
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Ошибка: пользователь не найден. Напишите /start")
        await state.clear()
        return
    
    # Получаем корзину для подсчёта суммы
    cart_items = get_cart(user['user_id'])
    
    if not cart_items:
        await message.answer("Корзина пуста")
        await state.clear()
        return
    
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    
    try:
        # Создаём заказ (вся операция в одной транзакции)
        order_id = create_order(user['user_id'], total, phone, address)
        
        # Сохраняем адрес в БД
        update_user_info(message.from_user.id, address=address)
        
        await state.clear()
        
        await message.answer(
            f"✅ Заказ #{order_id} успешно оформлен!\n\n"
            f"💰 Сумма: {format_price(total)}₽\n"
            f"📞 Телефон: {phone}\n"
            f"🏠 Адрес: {address}\n\n"
            f"Статус заказа можно отслеживать в разделе «Мои заказы»",
            reply_markup=get_main_keyboard(is_admin(message.from_user.id))
        )
    except Exception as e:
        logger.error(f"Ошибка при создании заказа: {e}")
        await message.answer(
            "❌ Произошла ошибка при оформлении заказа. Пожалуйста, попробуйте позже.",
            reply_markup=get_main_keyboard(is_admin(message.from_user.id))
        )
        await state.clear()

@router.message(F.text == "📦 Мои заказы")
async def show_orders(message: Message):
    user = get_user(message.from_user.id)
    
    if not user:
        await message.answer("Сначала запустите бота /start")
        return
    
    orders = get_user_orders(user['user_id'])
    
    if not orders:
        await message.answer("У вас пока нет заказов")
        return
    
    for order in orders:
        status_text = {
            'pending': '⏳ Ожидает подтверждения',
            'processing': '🔄 В обработке',
            'shipped': '🚚 Отправлен',
            'delivered': '✅ Доставлен',
            'cancelled': '❌ Отменён'
        }.get(order['status'], order['status'])
        
        await message.answer(
            f"📦 Заказ #{order['order_id']}\n"
            f"📅 {order['order_date']}\n"
            f"💰 Сумма: {format_price(order['total_amount'])}₽\n"
            f"📊 Статус: {status_text}"
        )


@router.callback_query(F.data.startswith("order_"))
async def show_order_details(callback: CallbackQuery):
    order_id = int(callback.data.split("_")[1])
    items = get_order_items(order_id)
    
    if not items:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    text = f"📦 *Детали заказа #{order_id}:*\n\n"
    for item in items:
        text += f"• {item['product_name']} x{item['quantity']} = {format_price(item['price'] * item['quantity'])}₽\n"
    
    await callback.message.answer(text, parse_mode="Markdown")
    await callback.answer()


@router.message(F.text == "📞 Контакты")
async def show_contacts(message: Message):
    await message.answer(
        "📞 *Наши контакты:*\n\n"
        "Телефон: +7 (912) 123-45-67\n"
        "Email: shop@hvostik.ru\n"
        "Адрес: г. Ижевск, ул. Удмуртская, 123\n\n"
        "🕐 Режим работы:\n"
        "Пн-Пт: 10:00 - 20:00\n"
        "Сб-Вс: 11:00 - 18:00",
        parse_mode="Markdown"
    )


@router.message(F.text == "ℹ️ Помощь")
async def show_help(message: Message):
    await message.answer(
        "ℹ️ *Помощь*\n\n"
        "Доступные команды:\n"
        "/start - Начать работу\n"
        "/categories - Категории товаров\n"
        "/cart - Корзина\n"
        "/orders - Мои заказы\n\n"
        "Если у вас возникли вопросы, свяжитесь с нами по телефону или в чате поддержки.",
        parse_mode="Markdown"
    )


@router.message(Command("categories"))
async def cmd_categories(message: Message):
    categories = get_all_categories()
    await message.answer(
        "Выберите категорию:",
        reply_markup=get_categories_keyboard(categories)
    )


@router.message(Command("cart"))
async def cmd_cart(message: Message):
    await show_cart(message)


@router.message(Command("orders"))
async def cmd_orders(message: Message):
    await show_orders(message)


# ==================== АДМИНИСТРИРОВАНИЕ ====================

@router.message(Command("becomeadmin"))
async def cmd_become_admin(message: Message):
    parts = message.text.split()
    if len(parts) < 2:
        await message.answer(f"❌ Введи код: /becomeadmin КОД\n\nКод: {ADMIN_SECRET_CODE}")
        return
    
    code = parts[1]
    
    if code == ADMIN_SECRET_CODE:
        add_admin(message.from_user.id)
        await message.answer(
            "✅ Вы стали администратором!\n\n"
            "В главном меню появилась админ-панель."
        )
        await back_to_main(message)
    else:
        await message.answer("❌ Неверный код")


@router.message(F.text == "🔧 Админ-панель")
async def show_admin_panel(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    await message.answer(
        "🔧 *Админ-панель*\n\n"
        "Выберите действие:",
        parse_mode="Markdown",
        reply_markup=get_admin_keyboard()
    )


@router.message(F.text == "➕ Добавить товар")
async def start_add_product(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    categories = get_all_categories()
    
    if not categories:
        await message.answer("Сначала добавьте категории в БД")
        return
    
    keyboard = []
    row = []
    for cat in categories:
        row.append(KeyboardButton(text=cat['category_name']))
        if len(row) == 2:
            keyboard.append(row)
            row = []
    if row:
        keyboard.append(row)
    keyboard.append([KeyboardButton(text="◀️ Отмена")])
    
    await message.answer(
        "Выберите категорию товара:",
        reply_markup=ReplyKeyboardMarkup(keyboard=keyboard, resize_keyboard=True)
    )
    await state.set_state(AddProductStates.waiting_for_category)


@router.message(AddProductStates.waiting_for_category)
async def add_product_category(message: Message, state: FSMContext):
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer(
            "Добавление отменено",
            reply_markup=get_main_keyboard(True)
        )
        return
    
    categories = get_all_categories()
    selected = None
    
    for cat in categories:
        if cat['category_name'] == message.text:
            selected = cat
            break
    
    if not selected:
        await message.answer("Выберите категорию из списка")
        return
    
    await state.update_data(category_id=selected['category_id'])
    await message.answer(
        "Введите название товара:",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="◀️ Отмена")]],
            resize_keyboard=True
        )
    )
    await state.set_state(AddProductStates.waiting_for_name)


@router.message(AddProductStates.waiting_for_name)
async def add_product_name(message: Message, state: FSMContext):
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer(
            "Добавление отменено",
            reply_markup=get_main_keyboard(True)
        )
        return
    
    await state.update_data(name=message.text)
    await message.answer("Введите описание товара:")
    await state.set_state(AddProductStates.waiting_for_description)


@router.message(AddProductStates.waiting_for_description)
async def add_product_description(message: Message, state: FSMContext):
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer(
            "Добавление отменено",
            reply_markup=get_main_keyboard(True)
        )
        return
    
    await state.update_data(description=message.text)
    await message.answer("Введите цену товара (в рублях):")
    await state.set_state(AddProductStates.waiting_for_price)


@router.message(AddProductStates.waiting_for_price)
async def add_product_price(message: Message, state: FSMContext):
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer(
            "Добавление отменено",
            reply_markup=get_main_keyboard(True)
        )
        return
    
    try:
        price = float(message.text.replace(",", "."))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректную цену (положительное число)")
        return
    
    await state.update_data(price=price)
    await message.answer("Введите количество товара на складе:")
    await state.set_state(AddProductStates.waiting_for_stock)


@router.message(AddProductStates.waiting_for_stock)
async def add_product_stock(message: Message, state: FSMContext):
    if message.text == "◀️ Отмена":
        await state.clear()
        await message.answer(
            "Добавление отменено",
            reply_markup=get_main_keyboard(True)
        )
        return
    
    try:
        stock = int(message.text)
        if stock < 0:
            raise ValueError
    except ValueError:
        await message.answer("Введите корректное количество (целое неотрицательное число)")
        return
    
    data = await state.get_data()
    
    add_product(
        category_id=data['category_id'],
        name=data['name'],
        description=data['description'],
        price=data['price'],
        stock=stock
    )
    
    await state.clear()
    
    await message.answer(
        f"✅ Товар добавлен!\n\n"
        f"📦 {data['name']}\n"
        f"📝 {data['description']}\n"
        f"💰 Цена: {format_price(data['price'])}₽\n"
        f"📦 В наличии: {stock} шт.",
        reply_markup=get_main_keyboard(True)
    )


@router.message(F.text == "📋 Список товаров")
async def admin_list_products(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    products = get_all_products()
    
    if not products:
        await message.answer("Нет товаров в базе")
        return
    
    text = "*📋 Список товаров:*\n\n"
    for p in products:
        text += f"🆔 {p['product_id']}. {p['name']} - {format_price(p['price'])}₽ (в наличии: {p['stock']})\n"
        text += f"   ➡️ Для удаления: `/del_{p['product_id']}`\n\n"
    
    await message.answer(text, parse_mode="Markdown")


@router.message(lambda msg: msg.text and msg.text.startswith("/del_") and is_admin(msg.from_user.id))
async def admin_delete_product(message: Message):
    try:
        product_id = int(message.text.split("_")[1])
    except (IndexError, ValueError):
        await message.answer("❌ Неверный формат. Используйте /del_123")
        return
    
    product = get_product_by_id(product_id)
    
    if not product:
        await message.answer("Товар не найден")
        return
    
    deleted = delete_product(product_id)
    
    if deleted:
        await message.answer(f"✅ Товар «{product['name']}» удалён")
    else:
        await message.answer("Ошибка при удалении")


@router.message(F.text == "📦 Все заказы")
async def admin_all_orders(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    orders = get_all_orders()
    
    if not orders:
        await message.answer("Нет заказов")
        return
    
    text = "*📦 Все заказы:*\n\n"
    for order in orders[:20]:  # Показываем последние 20
        status_emoji = {
            'pending': '⏳',
            'processing': '🔄',
            'shipped': '🚚',
            'delivered': '✅',
            'cancelled': '❌'
        }.get(order['status'], '📦')
        
        text += f"{status_emoji} *Заказ #{order['order_id']}*\n"
        text += f"   👤 {order['first_name']}\n"
        text += f"   📞 {order['phone']}\n"
        text += f"   💰 {format_price(order['total_amount'])}₽\n"
        text += f"   📊 Статус: {order['status']}\n\n"
    
    await message.answer(text, parse_mode="Markdown")
    await message.answer(
        "Для управления статусом заказа нажмите на кнопку:",
        reply_markup=get_admin_orders_keyboard(orders[:10])
    )


@router.callback_query(F.data.startswith("admin_order_"))
async def admin_order_detail(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    
    order_id = int(callback.data.split("_")[2])
    items = get_order_items(order_id)
    
    if not items:
        await callback.answer("Заказ не найден", show_alert=True)
        return
    
    text = f"📦 *Заказ #{order_id}*\n\n"
    total = 0
    for item in items:
        subtotal = item['price'] * item['quantity']
        total += subtotal
        text += f"• {item['product_name']} x{item['quantity']} = {format_price(subtotal)}₽\n"
    
    text += f"\n*Итого: {format_price(total)}₽*"
    
    await callback.message.answer(
        text,
        parse_mode="Markdown",
        reply_markup=get_admin_order_actions_keyboard(order_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("status_"))
async def admin_update_order_status(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer("Доступ запрещён", show_alert=True)
        return
    
    parts = callback.data.split("_")
    order_id = int(parts[1])
    status = parts[2]
    
    update_order_status(order_id, status)
    
    status_text = {
        'processing': 'в обработку',
        'shipped': 'отправку',
        'delivered': 'доставку',
        'cancelled': 'отмену'
    }.get(status, status)
    
    await callback.answer(f"Статус заказа изменён на {status_text}")
    await callback.message.edit_text(
        callback.message.text + f"\n\n✅ Статус изменён на: {status}"
    )


@router.message(F.text == "👥 Пользователи")
async def admin_users(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("⛔ Доступ запрещён")
        return
    
    from database import get_db_connection
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users ORDER BY registered_at DESC')
        users = cursor.fetchall()
    
    if not users:
        await message.answer("Нет пользователей")
        return
    
    text = "*👥 Пользователи:*\n\n"
    for user in users:
        text += f"🆔 {user['telegram_id']}\n"
        text += f"   👤 {user['first_name']}\n"
        text += f"   📞 {user['phone'] or 'не указан'}\n"
        text += f"   📅 {user['registered_at']}\n\n"
    
    await message.answer(text, parse_mode="Markdown")