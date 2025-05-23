# Торговый бот для БКС и Тинькофф Инвестиций

Торговый бот, способный подключаться к брокерским счетам БКС и Тинькофф Инвестиции, торговать по стратегии скользящих средних, управлять рисками, вести журнал действий и предоставлять веб-интерфейс для управления.

## Функциональность

- Подключение к API БКС и Тинькофф Инвестиций
- Торговая стратегия на основе скользящих средних
- Управление рисками (стоп-лосс, тейк-профит, контроль размера позиции)
- Ведение журнала всех действий
- Веб-интерфейс для управления и мониторинга

## Архитектура проекта

Проект разбит на следующие модули:

- **app/brokers** - Классы для работы с API брокеров (БКС и Тинькофф)
- **app/strategies** - Торговые стратегии (скользящие средние)
- **app/risk_management** - Управление рисками
- **app/logging** - Логирование операций
- **app/web** - Веб-интерфейс для управления

## Установка

### Обычная установка

1. Клонируйте репозиторий:
```
git clone https://github.com/username/mmvbtrade.git
cd mmvbtrade
```

2. Создайте виртуальное окружение и установите зависимости:
```
python -m venv venv
venv\Scripts\activate (Windows)
source venv/bin/activate (Linux/Mac)
pip install -r requirements.txt
```

3. Получите API ключи у брокеров:
   - Для Тинькофф: [Документация Tinkoff Invest API](https://tinkoff.github.io/invest-openapi/)
   - Для БКС: [Документация BCS API](https://bcs.ru/api) (может потребоваться обновить URL)

### Docker установка

Для запуска через Docker:

1. Клонируйте репозиторий:
```
git clone https://github.com/username/mmvbtrade.git
cd mmvbtrade
```

2. Создайте файл `.env` с вашими API ключами и настройками (используйте `.env.example` как шаблон)

3. Соберите и запустите через Docker Compose:
```
docker-compose build
docker-compose up -d
```

Подробную информацию о Docker-конфигурации смотрите в [DOCKER.md](DOCKER.md).

## Запуск

### Обычный запуск

1. Запустите приложение с указанием API ключей:
```
python -m app.main --tinkoff-token "ВАШ_ТОКЕН_ТИНЬКОФФ" --bcs-client-id "ВАШ_ID_БКС" --bcs-client-secret "ВАШ_СЕКРЕТ_БКС"
```

Или через переменные окружения:
```
set TINKOFF_TOKEN=ВАШ_ТОКЕН_ТИНЬКОФФ (Windows)
export TINKOFF_TOKEN=ВАШ_ТОКЕН_ТИНЬКОФФ (Linux/Mac)
set BCS_CLIENT_ID=ВАШ_ID_БКС
set BCS_CLIENT_SECRET=ВАШ_СЕКРЕТ_БКС
python -m app.main
```

2. Откройте веб-интерфейс: http://localhost:5000

### Запуск через Docker

```bash
# Запуск всех сервисов
docker-compose up -d

# Запуск только API-сервера
docker-compose up -d api

# Просмотр логов
docker-compose logs -f
```

## Конфигурация

Параметры командной строки:
- `--log-level` - Уровень логирования (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `--host` - Хост для веб-сервера (по умолчанию: 0.0.0.0)
- `--port` - Порт для веб-сервера (по умолчанию: 5000)
- `--debug` - Включить режим отладки для веб-сервера
- `--tinkoff-token` - Токен API Тинькофф Инвестиций
- `--bcs-client-id` - ID клиента API БКС
- `--bcs-client-secret` - Секрет клиента API БКС

## Безопасность

**Важно!** Никогда не храните API ключи в коде или публичных репозиториях. Используйте переменные окружения или защищенные хранилища секретов.

При использовании Docker, храните секреты в файле `.env`, который не включен в систему контроля версий.

## Дисклеймер

Данный торговый бот предназначен только для образовательных целей. Автоматическая торговля на финансовых рынках связана с риском потери капитала. Используйте на свой страх и риск.

## Лицензия

MIT License 