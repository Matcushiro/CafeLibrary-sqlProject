import pyodbc
from config import get_connection_string


def get_connection():
    """Открывает новое соединение с базой данных."""
    return pyodbc.connect(get_connection_string())


def _rows_to_dicts(cursor):
    """Преобразует результат курсора в список словарей."""
    columns = [column[0] for column in cursor.description]
    return [dict(zip(columns, row)) for row in cursor.fetchall()]


def _execute_select(query, params=()):
    """Выполняет SELECT-запрос и возвращает список словарей."""
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        return _rows_to_dicts(cursor)


def _execute_proc(proc_name, params=(), fetch=False):
    """
    Вызывает хранимую процедуру.
    Если fetch=True - возвращает результат (список словарей).
    Иначе просто выполняет (для INSERT/UPDATE/DELETE процедур).
    """
    placeholders = ",".join("?" for _ in params)
    query = f"EXEC {proc_name} {placeholders}" if params else f"EXEC {proc_name}"
    with get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        result = _rows_to_dicts(cursor) if fetch else None
        conn.commit()
        return result


def _execute_proc_scalar(proc_name, params=()):
    """Вызывает процедуру, которая возвращает SELECT с одним значением (например, новый ID)."""
    rows = _execute_proc(proc_name, params, fetch=True)
    if rows:
        return list(rows[0].values())[0]
    return None

# Получение данных (используются VIEW для списков через запятую в выводах)

def get_books():
    return _execute_select("SELECT * FROM vw_BooksFull ORDER BY BookID")


def get_authors():
    return _execute_select("SELECT * FROM vw_AuthorsWithBooks ORDER BY AuthorID")


def get_clients():
    return _execute_select("SELECT * FROM vw_ClientsFull ORDER BY ClientID")


def get_menu_items():
    return _execute_select("SELECT * FROM MenuItems ORDER BY ItemID")


def get_orders():
    return _execute_select("SELECT * FROM vw_OrdersFull ORDER BY OrderID")


def get_employees():
    return _execute_select("SELECT * FROM Employees ORDER BY EmployeeID")


# Метаданные таблиц для универсального интерфейса

TABLES = {
    "Books":      {"label": "Книги",      "id_field": "BookID",     "loader": get_books},
    "Authors":    {"label": "Авторы",     "id_field": "AuthorID",   "loader": get_authors},
    "Clients":    {"label": "Клиенты",    "id_field": "ClientID",   "loader": get_clients},
    "MenuItems":  {"label": "Меню",       "id_field": "ItemID",     "loader": get_menu_items},
    "Orders":     {"label": "Заказы",     "id_field": "OrderID",    "loader": get_orders},
    "Employees":  {"label": "Сотрудники", "id_field": "EmployeeID", "loader": get_employees},
}

# Поиск

def find_by_id(table_name, record_id):
    """Найти запись по ID в указанной таблице"""
    return _execute_proc("sp_FindById", (table_name, record_id), fetch=True)


def search_by_name(text):
    """Найти текст по названиям/именам во всех таблицах сразу"""
    return _execute_proc("sp_SearchByName", (text,), fetch=True)

# Выдача/возврат книг

def issue_book(book_id, client_id):
    _execute_proc("sp_IssueBook", (book_id, client_id))


def return_book(book_id):
    _execute_proc("sp_ReturnBook", (book_id,))

# Заказы

def create_order(client_id, employee_id, is_card, card_number=None):
    """Создаёт заказ (шапку), возвращает новый OrderID"""
    return _execute_proc_scalar(
        "sp_CreateOrder", (client_id, employee_id, int(is_card), card_number)
    )


def add_order_item(order_id, item_id, quantity):
    _execute_proc("sp_AddOrderItem", (order_id, item_id, quantity))

# CRUD Книг

def add_book(title, written_date, author_id):
    return _execute_proc_scalar("sp_AddBook", (title, written_date, author_id))


def update_book(book_id, title, written_date, author_id):
    _execute_proc("sp_UpdateBook", (book_id, title, written_date, author_id))


def delete_book(book_id):
    _execute_proc("sp_DeleteBook", (book_id,))

# CRUD Авторов

def add_author(first_name, last_name, birth_year, death_year=None):
    return _execute_proc_scalar("sp_AddAuthor", (first_name, last_name, birth_year, death_year))


def update_author(author_id, first_name, last_name, birth_year, death_year=None):
    _execute_proc("sp_UpdateAuthor", (author_id, first_name, last_name, birth_year, death_year))


def delete_author(author_id):
    _execute_proc("sp_DeleteAuthor", (author_id,))

# CRUD Клиентов

def add_client(last_name, first_name, payment_method, card_number=None, employee_id=None):
    return _execute_proc_scalar(
        "sp_AddClient", (last_name, first_name, payment_method, card_number, employee_id)
    )


def update_client(client_id, last_name, first_name, payment_method, card_number=None, employee_id=None):
    _execute_proc(
        "sp_UpdateClient",
        (client_id, last_name, first_name, payment_method, card_number, employee_id),
    )


def delete_client(client_id):
    _execute_proc("sp_DeleteClient", (client_id,))

# CRUD Меню

def add_menu_item(name, ingredients, cost, profit):
    return _execute_proc_scalar("sp_AddMenuItem", (name, ingredients, cost, profit))


def update_menu_item(item_id, name, ingredients, cost, profit):
    _execute_proc("sp_UpdateMenuItem", (item_id, name, ingredients, cost, profit))


def delete_menu_item(item_id):
    _execute_proc("sp_DeleteMenuItem", (item_id,))

# CRUD Сотрудников

def add_employee(full_name, salary_card_number, phone, salary, is_staff=True):
    return _execute_proc_scalar(
        "sp_AddEmployee", (full_name, salary_card_number, phone, salary, int(is_staff))
    )


def update_employee(employee_id, full_name, salary_card_number, phone, salary, is_staff=True):
    _execute_proc(
        "sp_UpdateEmployee",
        (employee_id, full_name, salary_card_number, phone, salary, int(is_staff)),
    )


def delete_employee(employee_id):
    _execute_proc("sp_DeleteEmployee", (employee_id,))