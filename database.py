import sqlite3
import logging
from contextlib import contextmanager

DB_NAME = "pet_shop.db"
logger = logging.getLogger(__name__)


@contextmanager
def get_db_connection():
    """Возвращает соединение с базой данных"""
    conn = None
    try:
        conn = sqlite3.connect(DB_NAME, timeout=30, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()


def init_db():
    """Создаёт таблицы, если их нет"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE,
                first_name TEXT,
                phone TEXT,
                address TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица категорий товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS categories (
                category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_name TEXT UNIQUE,
                icon TEXT
            )
        ''')

        # Таблица товаров
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                product_id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER,
                name TEXT,
                description TEXT,
                price REAL,
                stock INTEGER,
                image_url TEXT,
                FOREIGN KEY (category_id) REFERENCES categories(category_id)
            )
        ''')

        # Таблица корзины
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS cart (
                cart_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                product_id INTEGER,
                quantity INTEGER DEFAULT 1,
                added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id),
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            )
        ''')

        # Таблица заказов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                order_id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_amount REAL,
                status TEXT DEFAULT 'pending',
                phone TEXT,
                address TEXT,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Таблица товаров в заказе
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS order_items (
                item_id INTEGER PRIMARY KEY AUTOINCREMENT,
                order_id INTEGER,
                product_id INTEGER,
                product_name TEXT,
                price REAL,
                quantity INTEGER,
                FOREIGN KEY (order_id) REFERENCES orders(order_id)
            )
        ''')

        # Таблица администраторов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admins (
                admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id INTEGER UNIQUE
            )
        ''')

        # Добавляем категории по умолчанию
        default_categories = [
            ('Корм', '🍖'),
            ('Игрушки', '🧸'),
            ('Аксессуары', '🪢'),
            ('Гигиена', '🧴'),
            ('Лекарства', '💊'),
            ('Одежда', '👕')
        ]

        for cat_name, icon in default_categories:
            cursor.execute('''
                INSERT OR IGNORE INTO categories (category_name, icon)
                VALUES (?, ?)
            ''', (cat_name, icon))

        # Получаем ID категорий
        cursor.execute("SELECT category_id, category_name FROM categories")
        categories = {row['category_name']: row['category_id'] for row in cursor.fetchall()}

        # Удаляем старые тестовые товары (если нужно обновить)
        cursor.execute("DELETE FROM products")

        # Добавляем расширенный список товаров
        test_products = [
            # Корм (category_id = categories.get('Корм', 1))
            (categories.get('Корм', 1), "Корм Royal Canin для собак", "Полнорационный сухой корм для взрослых собак, 2 кг", 2500, 50, ""),
            (categories.get('Корм', 1), "Корм Purina Pro Plan для кошек", "Премиум корм для кошек, с лососем, 1.5 кг", 1800, 40, ""),
            (categories.get('Корм', 1), "Корм Acana для щенков", "Беззерновой корм для щенков мелких пород, 2.5 кг", 3200, 30, ""),
            (categories.get('Корм', 1), "Влажный корм Hill's", "Паштет для кошек, 85 г, 12 шт в упаковке", 1200, 60, ""),
            
            # Игрушки (category_id = categories.get('Игрушки', 2))
            (categories.get('Игрушки', 2), "Мячик резиновый с пищалкой", "Прочная резина, издает звук, для собак средних пород", 350, 100, ""),
            (categories.get('Игрушки', 2), "Игрушка-канат для собак", "Для активных игр, чистит зубы, длина 40 см", 250, 80, ""),
            (categories.get('Игрушки', 2), "Мышь на батарейках", "Интерактивная игрушка для кошек, двигается", 450, 45, ""),
            (categories.get('Игрушки', 2), "Дразнилка с перьями", "Для кошек, на удочке, с колокольчиком", 180, 70, ""),
            
            # Аксессуары (category_id = categories.get('Аксессуары', 3))
            (categories.get('Аксессуары', 3), "Ошейник нейлоновый", "Регулируемый, с металлической пряжкой, длина 40-60 см", 400, 60, ""),
            (categories.get('Аксессуары', 3), "Поводок-рулетка 5м", "Автоматическая смотка, удобная ручка, для собак до 20 кг", 800, 45, ""),
            (categories.get('Аксессуары', 3), "Шлейка для собак", "Мягкая, дышащая, светоотражающая, размер M", 950, 35, ""),
            (categories.get('Аксессуары', 3), "Переноска для кошек", "Складная, с мягким дном, размер 50х30х30 см", 1500, 25, ""),
            
            # Гигиена (category_id = categories.get('Гигиена', 4))
            (categories.get('Гигиена', 4), "Шампунь для собак", "Гипоаллергенный, с ромашкой, 500 мл", 500, 35, ""),
            (categories.get('Гигиена', 4), "Когтерезка для кошек", "С ограничителем глубины среза, для мелких пород", 320, 55, ""),
            (categories.get('Гигиена', 4), "Расчёска-пуходёрка", "Для вычёсывания подшёрстка, с вращающимися зубьями", 280, 40, ""),
            (categories.get('Гигиена', 4), "Зоосалфетки", "Для чистки лап и шерсти, 100 шт", 150, 90, ""),
            
            # ЛЕКАРСТВА - НОВЫЕ ТОВАРЫ
            (categories.get('Лекарства', 5), "Капли от блох и клещей", "Адвантейдж для собак мелких пород, 4 дозы", 1200, 35, ""),
            (categories.get('Лекарства', 5), "Глистогонное средство", "Дронтал для кошек, 2 таблетки", 350, 50, ""),
            (categories.get('Лекарства', 5), "Витамины для шерсти", "Лакситив для кошек и собак, паста 100 мл", 650, 40, ""),
            (categories.get('Лекарства', 5), "Спрей от воспалений", "Микостоп для лечения кожных заболеваний, 50 мл", 450, 30, ""),
            (categories.get('Лекарства', 5), "Капли в глаза", "Барс для кошек и собак, 10 мл", 280, 45, ""),
            (categories.get('Лекарства', 5), "Энтеросгель для животных", "При отравлениях, 100 г", 380, 55, ""),
            
            # ОДЕЖДА - НОВЫЕ ТОВАРЫ
            (categories.get('Одежда', 6), "Комбинезон для собак", "Непромокаемый, на флисе, для мальчиков, размер S", 1200, 25, ""),
            (categories.get('Одежда', 6), "Попона послеоперационная", "Для кошек и собак, трикотажная, размер M", 850, 30, ""),
            (categories.get('Одежда', 6), "Свитер для кошек", "Вязаный, с вырезом для лап, цвет серый", 650, 20, ""),
            (categories.get('Одежда', 6), "Дождевик для собак", "На пуговицах, со светоотражателями, размер L", 950, 15, ""),
            (categories.get('Одежда', 6), "Ботинки для собак", "На липучках, с мембраной, 4 шт в комплекте", 750, 35, ""),
            (categories.get('Одежда', 6), "Шапка-ушанка для собак", "С завязками, для холодной зимы", 450, 28, ""),
            (categories.get('Одежда', 6), "Жилет утеплённый", "На молнии, со светоотражающими полосками, размер XS", 1100, 18, ""),
        ]

        for p in test_products:
            cursor.execute('''
                INSERT INTO products (category_id, name, description, price, stock, image_url)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', p)

        logger.info("База данных инициализирована с добавленными товарами")
        logger.info(f"Добавлено товаров: {len(test_products)}")

        # Выводим информацию для отладки
        cursor.execute("SELECT category_name, COUNT(*) as count FROM products p JOIN categories c ON p.category_id = c.category_id GROUP BY category_name")
        stats = cursor.fetchall()
        for stat in stats:
            logger.info(f"Категория '{stat['category_name']}': {stat['count']} товаров")


# ==================== ПОЛЬЗОВАТЕЛИ ====================

def add_user(telegram_id, first_name, phone=None, address=None):
    """Добавляет пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO users (telegram_id, first_name, phone, address)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, first_name, phone, address))
        return cursor.lastrowid


def get_user(telegram_id):
    """Получает информацию о пользователе"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone()


def update_user_info(telegram_id, phone=None, address=None):
    """Обновляет информацию о пользователе"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if phone:
            cursor.execute('UPDATE users SET phone = ? WHERE telegram_id = ?', (phone, telegram_id))
        if address:
            cursor.execute('UPDATE users SET address = ? WHERE telegram_id = ?', (address, telegram_id))


# ==================== ТОВАРЫ И КАТЕГОРИИ ====================

def get_all_categories():
    """Получает все категории"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM categories')
        return cursor.fetchall()


def get_products_by_category(category_id):
    """Получает товары по категории"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM products WHERE category_id = ? AND stock > 0
        ''', (category_id,))
        products = cursor.fetchall()
        logger.info(f"Найдено товаров в категории {category_id}: {len(products)}")
        return products


def get_product_by_id(product_id):
    """Получает товар по ID"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE product_id = ?', (product_id,))
        return cursor.fetchone()


def get_all_products():
    """Получает все товары"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products ORDER BY product_id')
        return cursor.fetchall()


def add_product(category_id, name, description, price, stock, image_url=""):
    """Добавляет товар"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO products (category_id, name, description, price, stock, image_url)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (category_id, name, description, price, stock, image_url))
        return cursor.lastrowid


def update_product_stock(product_id, stock):
    """Обновляет количество товара"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE products SET stock = ? WHERE product_id = ?', (stock, product_id))


def delete_product(product_id):
    """Удаляет товар"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM products WHERE product_id = ?', (product_id,))
        return cursor.rowcount


# ==================== КОРЗИНА ====================

def add_to_cart(user_id, product_id, quantity=1):
    """Добавляет товар в корзину"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM cart WHERE user_id = ? AND product_id = ?
        ''', (user_id, product_id))

        existing = cursor.fetchone()

        if existing:
            cursor.execute('''
                UPDATE cart SET quantity = quantity + ? 
                WHERE user_id = ? AND product_id = ?
            ''', (quantity, user_id, product_id))
        else:
            cursor.execute('''
                INSERT INTO cart (user_id, product_id, quantity)
                VALUES (?, ?, ?)
            ''', (user_id, product_id, quantity))


def get_cart(user_id):
    """Получает корзину пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT c.cart_id, c.product_id, c.quantity, p.name, p.price, p.stock
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        ''', (user_id,))
        return cursor.fetchall()


def remove_from_cart(cart_id):
    """Удаляет товар из корзины"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE cart_id = ?', (cart_id,))


def update_cart_quantity(cart_id, quantity):
    """Обновляет количество товара в корзине"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        if quantity <= 0:
            cursor.execute('DELETE FROM cart WHERE cart_id = ?', (cart_id,))
        else:
            cursor.execute('UPDATE cart SET quantity = ? WHERE cart_id = ?', (quantity, cart_id))


def clear_cart(user_id):
    """Очищает корзину"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('DELETE FROM cart WHERE user_id = ?', (user_id,))


# ==================== ЗАКАЗЫ ====================

def create_order(user_id, total_amount, phone, address):
    """Создаёт заказ - ВСЯ ОПЕРАЦИЯ В ОДНОЙ ТРАНЗАКЦИИ"""
    with get_db_connection() as conn:
        cursor = conn.cursor()

        # 1. Получаем корзину пользователя
        cursor.execute('''
            SELECT c.cart_id, c.product_id, c.quantity, p.name, p.price, p.stock
            FROM cart c
            JOIN products p ON c.product_id = p.product_id
            WHERE c.user_id = ?
        ''', (user_id,))
        
        cart_items = cursor.fetchall()
        
        if not cart_items:
            raise ValueError("Корзина пуста")

        # 2. Создаём заказ
        cursor.execute('''
            INSERT INTO orders (user_id, total_amount, phone, address, status)
            VALUES (?, ?, ?, ?, 'pending')
        ''', (user_id, total_amount, phone, address))
        
        order_id = cursor.lastrowid

        # 3. Добавляем товары в order_items и обновляем склад
        for item in cart_items:
            cursor.execute('''
                INSERT INTO order_items (order_id, product_id, product_name, price, quantity)
                VALUES (?, ?, ?, ?, ?)
            ''', (order_id, item['product_id'], item['name'], item['price'], item['quantity']))

            new_stock = item['stock'] - item['quantity']
            cursor.execute('UPDATE products SET stock = ? WHERE product_id = ?', 
                          (new_stock, item['product_id']))

            cursor.execute('DELETE FROM cart WHERE cart_id = ?', (item['cart_id'],))

        return order_id


def get_user_orders(user_id):
    """Получает заказы пользователя"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM orders WHERE user_id = ? ORDER BY order_date DESC
        ''', (user_id,))
        return cursor.fetchall()


def get_order_items(order_id):
    """Получает товары в заказе"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM order_items WHERE order_id = ?
        ''', (order_id,))
        return cursor.fetchall()


def get_all_orders():
    """Получает все заказы (для админа)"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT o.*, u.first_name, u.phone 
            FROM orders o
            JOIN users u ON o.user_id = u.user_id
            ORDER BY o.order_date DESC
        ''')
        return cursor.fetchall()


def update_order_status(order_id, status):
    """Обновляет статус заказа"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('UPDATE orders SET status = ? WHERE order_id = ?', (status, order_id))


# ==================== АДМИНИСТРАТОРЫ ====================

def add_admin(telegram_id):
    """Добавляет администратора"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('INSERT OR IGNORE INTO admins (telegram_id) VALUES (?)', (telegram_id,))


def is_admin(telegram_id):
    """Проверяет, является ли пользователь администратором"""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM admins WHERE telegram_id = ?', (telegram_id,))
        return cursor.fetchone() is not None