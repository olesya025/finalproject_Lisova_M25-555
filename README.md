# ValutaTrade Hub - Currency Wallet Application

## Описание проекта
ValutaTrade Hub - это консольное приложение для управления мультивалютным портфелем с поддержкой фиатных валют и криптовалют.

## Структура проекта

```
finalproject_Lisova_M25-555/
├── data/
│   ├── users.json
│   ├── portfolios.json
│   ├── rates.json
│   └── exchange_rates.json
├── valutatrade_hub/
│   ├── __init__.py
│   ├── logging_config.py
│   ├── decorators.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── currencies.py
│   │   ├── exceptions.py
│   │   ├── models.py
│   │   ├── usecases.py
│   │   └── utils.py
│   ├── infra/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── database.py
│   ├── parser_service/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── api_clients.py
│   │   ├── updater.py
│   │   ├── storage.py
│   │   └── scheduler.py
│   └── cli/
│       ├── __init__.py
│       └── interface.py
├── main.py
├── Makefile
├── poetry.lock
├── pyproject.toml
└── README.md
```

## Установка и запуск

```bash
make install
```

```bash
make project
```

## Основные команды

### Главное меню:
1. Create User - регистрация нового пользователя
2. Login - вход в систему
3. Currency Information - информация о валютах
4. Exit - выход

### Меню портфеля:
1. View Balance - просмотр баланса
2. Deposit Funds - пополнение счета
3. Add Currency - добавление валюты в портфель
4. Buy Currency - покупка валюты за USD
5. Sell Currency - продажа валюты за USD
6. Currency Information - информация о валютах
7. Update Exchange Rates - обновление курсов валют
8. Show Current Rates - текущие курсы
9. Logout - выход

## Пример использования

После запуска приложения:
1. Зарегистрируйте нового пользователя
2. Войдите в систему
3. Просмотрите стартовый баланс (1000 USD)
4. Обновите курсы валют
5. Купите другие валюты (EUR, BTC, ETH и т.д.)
6. Просмотрите обновленный баланс

## Технические особенности

- Глубокое ООП с наследованием и инкапсуляцией
- Приватные атрибуты с геттерами/сеттерами
- Пользовательские исключения
- Декораторы для логирования и подтверждения операций
- Замыкания для кэширования курсов валют
- Паттерн Singleton для настроек и базы данных
- Логирование в JSON формате
- Модульная архитектура

## Поддерживаемые валюты

### Фиатные валюты:
- USD (US Dollar)
- EUR (Euro)
- RUB (Russian Ruble)

### Криптовалюты:
- BTC (Bitcoin)
- ETH (Ethereum)

## Источники данных

- CoinGecko API - курсы криптовалют
- ExchangeRate-API - курсы фиатных валют