import tkinter as tk
from tkinter import ttk, messagebox, simpledialog

import db


class App(tk.Tk):
    """Главное окно приложения"""

    def __init__(self):
        super().__init__()
        self.title("Кафе-библиотека")
        self.geometry("1100x650")

        self.current_table = None  # название текущей открытой таблицы (чтобы правильно воркали Edit и Delete)

        self._build_top_buttons()
        self._build_search_panel()
        self._build_table()
        self._build_action_buttons()

        self.show_table("Books")

    # База интерфейса

    def _build_top_buttons(self):
        """Кнопки переключения между таблицами"""
        frame = ttk.LabelFrame(self, text="Таблицы")
        frame.pack(fill="x", padx=5, pady=5)

        for table_name, meta in db.TABLES.items():
            btn = ttk.Button(
                frame, text=meta["label"],
                command=lambda t=table_name: self.show_table(t)
            )
            btn.pack(side="left", padx=3, pady=3)

    def _build_search_panel(self):
        """Панель поиска по ID и по названию"""
        frame = ttk.LabelFrame(self, text="Поиск")
        frame.pack(fill="x", padx=5, pady=5)

        # Поиск по ID
        ttk.Label(frame, text="Таблица:").pack(side="left", padx=3)
        self.search_table_cb = ttk.Combobox(
            frame, values=list(db.TABLES.keys()), width=12, state="readonly"
        )
        self.search_table_cb.current(0)
        self.search_table_cb.pack(side="left", padx=3)

        ttk.Label(frame, text="ID:").pack(side="left", padx=3)
        self.search_id_entry = ttk.Entry(frame, width=10)
        self.search_id_entry.pack(side="left", padx=3)

        ttk.Button(frame, text="Найти по ID", command=self.on_find_by_id).pack(side="left", padx=5)

        # Разделитель
        ttk.Separator(frame, orient="vertical").pack(side="left", fill="y", padx=10)

        # Поиск по названию во всех таблицах
        ttk.Label(frame, text="Текст:").pack(side="left", padx=3)
        self.search_text_entry = ttk.Entry(frame, width=20)
        self.search_text_entry.pack(side="left", padx=3)

        ttk.Button(frame, text="Поиск по названию (везде)",
                   command=self.on_search_by_name).pack(side="left", padx=5)

        ttk.Button(frame, text="Сбросить (показать всё)",
                   command=lambda: self.show_table(self.current_table)).pack(side="left", padx=5)

    def _build_table(self):
        """Таблица для вывода результатов"""
        frame = ttk.Frame(self)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        self.tree = ttk.Treeview(frame, show="headings")
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)

        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")

        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)

    def _build_action_buttons(self):
        """Кнопки управления (выдача книг, заказы, CRUD)"""
        frame = ttk.LabelFrame(self, text="Действия")
        frame.pack(fill="x", padx=5, pady=5)

        ttk.Button(frame, text="Добавить", command=self.on_add).pack(side="left", padx=3, pady=3)
        ttk.Button(frame, text="Редактировать", command=self.on_edit).pack(side="left", padx=3, pady=3)
        ttk.Button(frame, text="Удалить", command=self.on_delete).pack(side="left", padx=3, pady=3)

        ttk.Separator(frame, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Button(frame, text="Выдать книгу", command=self.on_issue_book).pack(side="left", padx=3, pady=3)
        ttk.Button(frame, text="Вернуть книгу", command=self.on_return_book).pack(side="left", padx=3, pady=3)

        ttk.Separator(frame, orient="vertical").pack(side="left", fill="y", padx=10)

        ttk.Button(frame, text="Оформить заказ", command=self.on_create_order).pack(side="left", padx=3, pady=3)

    # Отображение данных

    def fill_tree(self, rows):
        """Заполняет Treeview переданными строками (список словарей)"""
        self.tree.delete(*self.tree.get_children())

        if not rows:
            self.tree["columns"] = []
            return

        columns = list(rows[0].keys())
        self.tree["columns"] = columns
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=120, anchor="w")

        for row in rows:
            values = [row[c] if row[c] is not None else "" for c in columns]
            self.tree.insert("", "end", values=values)

    def show_table(self, table_name):
        """Показывает все данные указанной таблицы"""
        if table_name is None:
            return
        self.current_table = table_name
        rows = db.TABLES[table_name]["loader"]()
        self.fill_tree(rows)

    def get_selected_id(self):
        """Возвращает значение ID выделенной строки (первый столбец)"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("Внимание", "Сначала выберите строку в таблице")
            return None
        values = self.tree.item(selected[0], "values")
        return values[0]

    # Поиск

    def on_find_by_id(self):
        table_name = self.search_table_cb.get()
        id_text = self.search_id_entry.get().strip()
        if not id_text.isdigit():
            messagebox.showerror("Ошибка", "ID должен быть числом")
            return
        try:
            rows = db.find_by_id(table_name, int(id_text))
            self.current_table = table_name
            self.fill_tree(rows)
            if not rows:
                messagebox.showinfo("Результат", "Ничего не найдено")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_search_by_name(self):
        text = self.search_text_entry.get().strip()
        if not text:
            messagebox.showerror("Ошибка", "Введите текст для поиска")
            return
        try:
            rows = db.search_by_name(text)
            self.current_table = None
            self.fill_tree(rows)
            if not rows:
                messagebox.showinfo("Результат", "Совпадений не найдено")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # Выдача и возврат книг

    def on_issue_book(self):
        book_id = simpledialog.askinteger("Выдача книги", "ID книги:")
        if book_id is None:
            return
        client_id = simpledialog.askinteger("Выдача книги", "ID клиента:")
        if client_id is None:
            return
        try:
            db.issue_book(book_id, client_id)
            messagebox.showinfo("Готово", "Книга выдана")
            self.show_table("Books")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_return_book(self):
        book_id = simpledialog.askinteger("Возврат книги", "ID книги:")
        if book_id is None:
            return
        try:
            db.return_book(book_id)
            messagebox.showinfo("Готово", "Книга возвращена")
            self.show_table("Books")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    # Оформление заказа

    def on_create_order(self):
        OrderDialog(self)
 
    # CRUD

    def on_add(self):
        if self.current_table is None:
            messagebox.showwarning("Внимание", "Сначала откройте конкретную таблицу")
            return
        dialog_cls = DIALOGS.get(self.current_table)
        if dialog_cls:
            dialog_cls(self, mode="add")
        else:
            messagebox.showinfo("Инфо", "Для этой таблицы добавление через интерфейс не предусмотрено")

    def on_edit(self):
        if self.current_table is None:
            messagebox.showwarning("Внимание", "Сначала откройте конкретную таблицу")
            return
        record_id = self.get_selected_id()
        if record_id is None:
            return
        dialog_cls = DIALOGS.get(self.current_table)
        if dialog_cls:
            dialog_cls(self, mode="edit", record_id=record_id)
        else:
            messagebox.showinfo("Инфо", "Для этой таблицы редактирование через интерфейс не предусмотрено")

    def on_delete(self):
        if self.current_table is None:
            messagebox.showwarning("Внимание", "Сначала откройте конкретную таблицу")
            return
        record_id = self.get_selected_id()
        if record_id is None:
            return
        if not messagebox.askyesno("Подтверждение", f"Удалить запись с ID={record_id}?"):
            return
        try:
            delete_func = DELETE_FUNCS.get(self.current_table)
            if delete_func is None:
                messagebox.showinfo("Инфо", "Для этой таблицы удаление через интерфейс не предусмотрено")
                return
            delete_func(int(record_id))
            messagebox.showinfo("Готово", "Запись удалена")
            self.show_table(self.current_table)
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

# Диалогие добавления и редактирования к каждой таблице

class BaseDialog(tk.Toplevel):
    """Базовый класс диалога добавления/редактирования записи"""

    def __init__(self, parent, title, mode, record_id=None):
        super().__init__(parent)
        self.parent = parent
        self.mode = mode
        self.record_id = record_id
        self.title(title)
        self.resizable(False, False)
        self.entries = {}
        self._row = 0

        self._build_form()

        if mode == "edit":
            self._load_existing_data()
        save_btn = ttk.Button(self, text="Сохранить", command=self.on_save)
        save_btn.grid(row=self._row, column=0, columnspan=2, pady=10)
        self.transient(parent)
        self.grab_set()

    def _add_field(self, label, key, width=30):
        """Добавляет подпись + поле ввода в следующую строку grid"""
        ttk.Label(self, text=label).grid(row=self._row, column=0, sticky="w", padx=5, pady=3)
        entry = ttk.Entry(self, width=width)
        entry.grid(row=self._row, column=1, padx=5, pady=3)
        self.entries[key] = entry
        self._row += 1
        return entry

    def _build_form(self):
        raise NotImplementedError

    def _load_existing_data(self):
        raise NotImplementedError

    def on_save(self):
        raise NotImplementedError


class BookDialog(BaseDialog):
    def __init__(self, parent, mode, record_id=None):
        super().__init__(parent, "Книга", mode, record_id)

    def _build_form(self):
        self._add_field("Название:", "title")
        self._add_field("Дата написания (YYYY-MM-DD):", "written_date")
        self._add_field("ID автора:", "author_id")

    def _load_existing_data(self):
        rows = db.find_by_id("Books", int(self.record_id))
        if not rows:
            return
        row = rows[0]
        self.entries["title"].insert(0, row["Title"])
        self.entries["written_date"].insert(0, str(row["WrittenDate"]))
        self.entries["author_id"].insert(0, str(row["AuthorID"]))

    def on_save(self):
        try:
            title = self.entries["title"].get()
            written_date = self.entries["written_date"].get()
            author_id = int(self.entries["author_id"].get())
            if self.mode == "add":
                db.add_book(title, written_date, author_id)
            else:
                db.update_book(int(self.record_id), title, written_date, author_id)
            self.parent.show_table("Books")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class AuthorDialog(BaseDialog):
    def __init__(self, parent, mode, record_id=None):
        super().__init__(parent, "Автор", mode, record_id)

    def _build_form(self):
        self._add_field("Имя:", "first_name")
        self._add_field("Фамилия:", "last_name")
        self._add_field("Год рождения:", "birth_year")
        self._add_field("Год смерти (пусто, если жив):", "death_year")

    def _load_existing_data(self):
        rows = db.find_by_id("Authors", int(self.record_id))
        if not rows:
            return
        row = rows[0]
        self.entries["first_name"].insert(0, row["FirstName"])
        self.entries["last_name"].insert(0, row["LastName"])
        self.entries["birth_year"].insert(0, str(row["BirthYear"]))
        if row["DeathYear"]:
            self.entries["death_year"].insert(0, str(row["DeathYear"]))

    def on_save(self):
        try:
            first_name = self.entries["first_name"].get()
            last_name = self.entries["last_name"].get()
            birth_year = int(self.entries["birth_year"].get())
            death_year_text = self.entries["death_year"].get().strip()
            death_year = int(death_year_text) if death_year_text else None
            if self.mode == "add":
                db.add_author(first_name, last_name, birth_year, death_year)
            else:
                db.update_author(int(self.record_id), first_name, last_name, birth_year, death_year)
            self.parent.show_table("Authors")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class ClientDialog(BaseDialog):
    def __init__(self, parent, mode, record_id=None):
        super().__init__(parent, "Клиент", mode, record_id)

    def _build_form(self):
        self._add_field("Фамилия:", "last_name")
        self._add_field("Имя:", "first_name")

        ttk.Label(self, text="Способ оплаты:").grid(row=self._row, column=0, sticky="w", padx=5, pady=3)
        self.payment_cb = ttk.Combobox(self, values=["Карта", "Наличные"], state="readonly", width=27)
        self.payment_cb.grid(row=self._row, column=1, padx=5, pady=3)
        self.payment_cb.current(1)
        self._row += 1

        self._add_field("Номер карты (если 'Карта'):", "card_number")
        self._add_field("ID обслуживающего сотрудника:", "employee_id")

    def _load_existing_data(self):
        rows = db.find_by_id("Clients", int(self.record_id))
        if not rows:
            return
        row = rows[0]
        self.entries["last_name"].insert(0, row["LastName"])
        self.entries["first_name"].insert(0, row["FirstName"])
        self.payment_cb.set(row["PaymentMethod"])
        if row["CardNumber"]:
            self.entries["card_number"].insert(0, row["CardNumber"])
        if row["EmployeeID"]:
            self.entries["employee_id"].insert(0, str(row["EmployeeID"]))

    def on_save(self):
        try:
            last_name = self.entries["last_name"].get()
            first_name = self.entries["first_name"].get()
            payment_method = self.payment_cb.get()
            card_number = self.entries["card_number"].get().strip() or None
            employee_id_text = self.entries["employee_id"].get().strip()
            employee_id = int(employee_id_text) if employee_id_text else None

            if payment_method == "Наличные":
                card_number = None  # согласованность с CHECK в базе

            if self.mode == "add":
                db.add_client(last_name, first_name, payment_method, card_number, employee_id)
            else:
                db.update_client(int(self.record_id), last_name, first_name,
                                  payment_method, card_number, employee_id)
            self.parent.show_table("Clients")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class MenuItemDialog(BaseDialog):
    def __init__(self, parent, mode, record_id=None):
        super().__init__(parent, "Блюдо", mode, record_id)

    def _build_form(self):
        self._add_field("Название:", "name")
        self._add_field("Ингредиенты:", "ingredients", width=40)
        self._add_field("Стоимость:", "cost")
        self._add_field("Прибыль:", "profit")

    def _load_existing_data(self):
        rows = db.find_by_id("MenuItems", int(self.record_id))
        if not rows:
            return
        row = rows[0]
        self.entries["name"].insert(0, row["Name"])
        self.entries["ingredients"].insert(0, row["Ingredients"])
        self.entries["cost"].insert(0, str(row["Cost"]))
        self.entries["profit"].insert(0, str(row["Profit"]))

    def on_save(self):
        try:
            name = self.entries["name"].get()
            ingredients = self.entries["ingredients"].get()
            cost = float(self.entries["cost"].get())
            profit = float(self.entries["profit"].get())
            if self.mode == "add":
                db.add_menu_item(name, ingredients, cost, profit)
            else:
                db.update_menu_item(int(self.record_id), name, ingredients, cost, profit)
            self.parent.show_table("MenuItems")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class EmployeeDialog(BaseDialog):
    def __init__(self, parent, mode, record_id=None):
        super().__init__(parent, "Сотрудник", mode, record_id)

    def _build_form(self):
        self._add_field("ФИО:", "full_name", width=35)
        self._add_field("Номер зарплатной карты:", "salary_card")
        self._add_field("Телефон:", "phone")
        self._add_field("Зарплата:", "salary")

        self.is_staff_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(self, text="В штате", variable=self.is_staff_var).grid(
            row=self._row, column=0, columnspan=2, pady=3
        )
        self._row += 1

    def _load_existing_data(self):
        rows = db.find_by_id("Employees", int(self.record_id))
        if not rows:
            return
        row = rows[0]
        self.entries["full_name"].insert(0, row["FullName"])
        self.entries["salary_card"].insert(0, row["SalaryCardNumber"])
        self.entries["phone"].insert(0, row["Phone"])
        self.entries["salary"].insert(0, str(row["Salary"]))
        self.is_staff_var.set(bool(row["IsStaff"]))

    def on_save(self):
        try:
            full_name = self.entries["full_name"].get()
            salary_card = self.entries["salary_card"].get()
            phone = self.entries["phone"].get()
            salary = float(self.entries["salary"].get())
            is_staff = self.is_staff_var.get()
            if self.mode == "add":
                db.add_employee(full_name, salary_card, phone, salary, is_staff)
            else:
                db.update_employee(int(self.record_id), full_name, salary_card, phone, salary, is_staff)
            self.parent.show_table("Employees")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))


class OrderDialog(tk.Toplevel):
    """Диалог оформления нового заказа: шапка + добавление блюд"""

    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.title("Новый заказ")
        self.resizable(False, False)
        self.order_id = None

        ttk.Label(self, text="ID клиента:").grid(row=0, column=0, sticky="w", padx=5, pady=3)
        self.client_entry = ttk.Entry(self)
        self.client_entry.grid(row=0, column=1, padx=5, pady=3)

        ttk.Label(self, text="ID сотрудника:").grid(row=1, column=0, sticky="w", padx=5, pady=3)
        self.employee_entry = ttk.Entry(self)
        self.employee_entry.grid(row=1, column=1, padx=5, pady=3)

        ttk.Label(self, text="Оплата:").grid(row=2, column=0, sticky="w", padx=5, pady=3)
        self.payment_cb = ttk.Combobox(self, values=["Карта", "Наличные"], state="readonly")
        self.payment_cb.current(1)
        self.payment_cb.grid(row=2, column=1, padx=5, pady=3)

        ttk.Label(self, text="Номер карты (если 'Карта'):").grid(row=3, column=0, sticky="w", padx=5, pady=3)
        self.card_entry = ttk.Entry(self)
        self.card_entry.grid(row=3, column=1, padx=5, pady=3)

        ttk.Button(self, text="Создать заказ", command=self.on_create_order).grid(
            row=4, column=0, columnspan=2, pady=5
        )

        ttk.Separator(self, orient="horizontal").grid(row=5, column=0, columnspan=2, sticky="ew", pady=5)

        ttk.Label(self, text="ID блюда:").grid(row=6, column=0, sticky="w", padx=5, pady=3)
        self.item_entry = ttk.Entry(self)
        self.item_entry.grid(row=6, column=1, padx=5, pady=3)

        ttk.Label(self, text="Количество:").grid(row=7, column=0, sticky="w", padx=5, pady=3)
        self.qty_entry = ttk.Entry(self)
        self.qty_entry.insert(0, "1")
        self.qty_entry.grid(row=7, column=1, padx=5, pady=3)

        ttk.Button(self, text="Добавить блюдо в заказ", command=self.on_add_item).grid(
            row=8, column=0, columnspan=2, pady=5
        )

        ttk.Button(self, text="Завершить", command=self.on_finish).grid(
            row=9, column=0, columnspan=2, pady=10
        )

        self.status_label = ttk.Label(self, text="Заказ ещё не создан")
        self.status_label.grid(row=10, column=0, columnspan=2)

        self.transient(parent)
        self.grab_set()

    def on_create_order(self):
        try:
            client_id = int(self.client_entry.get())
            employee_id = int(self.employee_entry.get())
            payment_method = self.payment_cb.get()
            is_card = payment_method == "Карта"
            card_number = self.card_entry.get().strip() or None
            if not is_card:
                card_number = None

            self.order_id = db.create_order(client_id, employee_id, is_card, card_number)
            self.status_label.config(text=f"Заказ создан, ID = {self.order_id}. Добавляйте блюда.")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_add_item(self):
        if self.order_id is None:
            messagebox.showwarning("Внимание", "Сначала создайте заказ")
            return
        try:
            item_id = int(self.item_entry.get())
            quantity = int(self.qty_entry.get())
            db.add_order_item(self.order_id, item_id, quantity)
            self.status_label.config(text=f"Блюдо добавлено в заказ №{self.order_id}")
        except Exception as e:
            messagebox.showerror("Ошибка", str(e))

    def on_finish(self):
        self.parent.show_table("Orders")
        self.destroy()


# Таблицы соответствий (диалогов и функций удаления)
DIALOGS = {
    "Books": BookDialog,
    "Authors": AuthorDialog,
    "Clients": ClientDialog,
    "MenuItems": MenuItemDialog,
    "Employees": EmployeeDialog,
}

DELETE_FUNCS = {
    "Books": db.delete_book,
    "Authors": db.delete_author,
    "Clients": db.delete_client,
    "MenuItems": db.delete_menu_item,
    "Employees": db.delete_employee,
}


if __name__ == "__main__":
    app = App()
    app.mainloop()