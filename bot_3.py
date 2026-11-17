import pickle
from collections import UserDict
from datetime import datetime, timedelta
from pathlib import Path


class Field:
    """ Базовий клас для полів запису """
    
    def __init__(self, value):
        self.value = value
        

    def __str__(self):
        return str(self.value)


class Name(Field):
    """Імʼя контакту. Обовʼязкове поле"""
    
    
    def __init__(self, value):
        # ім'я без урахування регістру: john, JOHN → John
        super().__init__(value.title())
    

class Phone(Field):
    """ Номер телефону з перевіркою формату """
    
    def __init__(self, value):
        # перевірка, чи номер складається з 10 цифр
        if len(value) != 10 or not value.isdigit():
            raise ValueError("Phone number must contain 10 digits.")
        super().__init__(value)


class Birthday(Field):
    """День народження у форматі DD.MM.YYYY."""
    def __init__(self, value):
        try:
            # перетворюємо рядок на дату; якщо формат невірний — буде ValueError
            date = datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(date)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    """Запис контакту.Імʼя та список телефонів."""
    
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None
        

    def add_phone(self, phone):
        """ Додає телефон до запису """
        # не дуюблюємо номер, якщо вже є у контакту
        if self.find_phone(phone):
            raise ValueError("Phone already exists.")
        self.phones.append(Phone(phone))
        
    
    def add_birthday(self, birthday):
        """Додає день народження до запису."""
        self.birthday = Birthday(birthday)
        
        
     
    def find_phone(self, phone):
        """ Шукає телефон у записах.Повертає обʼєкт Phone або None """
        for p in self.phones:
            if p.value == phone:
                return p
        return None
    
    
    def remove_phone(self, phone):
        """ Видаляє номер з запису """
        found = self.find_phone(phone)  # шукає потрібний обʼєкт у списку
        if found:
            self.phones.remove(found)
            
            
    def edit_phone(self, old, new):
        """ Замінює старий номер на новий """
        found = self.find_phone(old)
        if not found:
            raise ValueError("Phone not found.")
        if self.find_phone(new):
            raise ValueError("Phone already exists.")
        index = self.phones.index(found)
        # новий обʼєкт Phone, щоб спрацювала перевірка на 10 цифр
        self.phones[index] = Phone(new)
    

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):
    """Адресна книга: імʼя - ключ, Record - значення."""
    
    
    def add_record(self, record):
        """Додає запис до адресної книги"""
        self.data[record.name.value] = record
        
        
    def find(self, name):
        """Шукає запис за імʼям. Повертає Record або None"""
        return self.data.get(name.title())
    
    
    def delete(self, name):
        """ Видаляє запис за імʼям"""
        name = name.title()
        if name in self.data:
            del self.data[name]
            
    
    @staticmethod
    def _birthday_in_year(birthday, year):
        """Повертає день народження у вказаному році.
        29 лютого в невисокосний рік переноситься на 1 березня.
        """
        try:
            return birthday.replace(year=year)
        except ValueError:
            return birthday.replace(year=year, month=3, day=1)
    
    def get_upcoming_birthdays(self):
        """Повертає список контактів, яких треба привітати протягом 7 днів."""
        upcoming_birthdays = []
        today = datetime.today().date()
        
        for record in self.data.values():
            if record.birthday is None:
                continue
            
            birthday = record.birthday.value
            birthday_this_year = self._birthday_in_year(birthday, today.year)
            if birthday_this_year < today:      # день народження вже минув
                birthday_this_year = self._birthday_in_year(birthday, today.year + 1)
                
            days_until = (birthday_this_year - today).days
            congrats_day = birthday_this_year
                
            if 0 <= days_until <= 6:
                if congrats_day.weekday() == 5:    # субота
                    congrats_day = congrats_day + timedelta(days=2)
                elif congrats_day.weekday() == 6:  # неділя
                    congrats_day = congrats_day + timedelta(days=1)
                        
                upcoming_birthdays.append({
                    "name": record.name.value,
                    "congratulation_date": congrats_day.strftime("%d.%m.%Y"),
                })
                
        return upcoming_birthdays   


def parse_input(user_input):
    """Розбирає введений рядок на команду та аргументи."""
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()  # команду в нижній регістр
    return cmd, *args


# підказки формату для кожної команди
USAGE = {
    "add_contact": "add [name] [phone]",
    "change_contact": "change [name] [old phone] [new phone]",
    "show_phone": "phone [name]",
    "add_birthday": "add-birthday [name] [DD.MM.YYYY]",
    "show_birthday": "show-birthday [name]",
}


def input_error(func):
    """Обробляє помилки введення в командах бота."""
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e:
            message = str(e)
            # не вистачає аргументів (помилка розпакування args)
            if "unpack" in message:
                return f"Not enough arguments. Usage: {USAGE[func.__name__]}"
            # повідомлення з класів Phone, Birthday, Record
            return message
        except IndexError:
            return f"Enter the name. Usage: {USAGE[func.__name__]}"
        except KeyError:
            return "Contact is not found."
        
    return inner


@input_error
def add_contact(args, book: AddressBook):
    """Додає новий контакт або телефон до існуючого."""
    name, phone, *_ = args
    record = book.find(name)
    if record is None:
        record = Record(name)
        record.add_phone(phone)  # спершу перевіряємо телефон
        book.add_record(record)  # додаємо в книгу, лише якщо телефон коректний
        return "Contact added."
    record.add_phone(phone)
    return "Phone added."


@input_error
def change_contact(args, book: AddressBook):
    """Змінює телефон існуючого контакту."""
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    record.edit_phone(old_phone, new_phone)
    return "Phone updated."


@input_error
def show_phone(args, book: AddressBook):
    """Повертає телефони контакту."""
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    return '; '.join(p.value for p in record.phones)


@input_error
def show_all(book: AddressBook):
    """Повертає всі контакти адресної книги."""
    if not book.data:
        return "No contacts saved."
    result = "All contacts:\n"
    for record in book.data.values():
        result += f"{record}\n"
    return result.strip()


@input_error
def add_birthday(args, book: AddressBook):
    """Додає дату народження контактів."""
    name, birthday, *_ = args
    record = book.find(name)
    if record is None:
        raise KeyError
    had_birthday = record.birthday is not None
    record.add_birthday(birthday)
    return "Birthday updated." if had_birthday else "Birthday added."

    
@input_error
def show_birthday(args, book: AddressBook):
    """ Повертає день народження контакту."""
    name = args[0]
    record = book.find(name)
    if record is None:
        raise KeyError
    if record.birthday is None:
        return "Birthday is not set."
    return record.birthday.value.strftime("%d.%m.%Y")
    
    
@input_error
def birthdays(args, book: AddressBook):
    """Повертає список привітань на наступний тиждень."""
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the next 7 days."
    result = "Upcoming birthdays:\n"
    for item in upcoming:
        result += f"{item['name']}: {item['congratulation_date']}\n"
    return result.strip()
    
    
DATA_FILE = Path(__file__).parent / "addressbook.pkl"
def save_data(book, filename=DATA_FILE):
    """Зберігає адресну книгу у файл."""
    with open(filename, "wb") as file:
        pickle.dump(book, file)
        
        
def load_data(filename=DATA_FILE):
    """Завантажує адресну книгу з файлу або створює нову."""
    try:
        with open(filename, "rb" ) as file:
            return pickle.load(file)
    except FileNotFoundError:
        # перший запуск: файлу ще немає
        return AddressBook()
    

def main():
    """Основний цикл бота: читає команди та викликає потрібні функції."""
    book = load_data()
    print("Welcome to the assistant bot!")
    try:
        while True:
            user_input = input("Enter a command: ")
            # пропускаємо порожнє введення, щоб парсер не впав
            if not user_input.strip():
                continue
            command, *args = parse_input(user_input)
            if command in ["close", "exit"]:
                print("Good bye!")
                break
            elif command == "hello":
                print("How can I help you?")
            elif command == "add":
                print(add_contact(args, book))
            elif command == "change":
                print(change_contact(args, book))
            elif command == "phone":
                print(show_phone(args, book))
            elif command == "all":
                print(show_all(book))
            elif command == "add-birthday":
                print(add_birthday(args, book))
            elif command == "show-birthday":
                print(show_birthday(args, book))
            elif command == "birthdays":
                print(birthdays(args, book))
            else:
                print("Invalid command. "
                    "Available: hello, add, change, phone, all, "
                    "add-birthday, show-birthday, birthdays, exit.")
    except (KeyboardInterrupt, EOFError):
        print("\nGood bye!")
    finally:
        # зберігаємо книгу за будь-якого виходу з програми
        save_data(book)


if __name__ == "__main__":
    main()