# Параллельное развертывание нового функционала

## Описание

Этот метод позволяет безопасно развернуть новую версию проекта параллельно со старой, протестировать её, а затем переключиться на неё или откатиться к старой версии.

## Преимущества

- ✅ Безопасность: старая версия остается рабочей
- ✅ Возможность тестирования новой версии перед переключением
- ✅ Легкий откат при проблемах
- ✅ Минимальное время простоя

## Структура

```
/root/
├── sparks/          # Старая версия (останавливается)
├── sparks_new/      # Новая версия (запускается)
└── sparks_old_*/    # Резервные копии старых версий
```

## Процесс развертывания

### Шаг 1: Подготовка

```bash
# Подключение к серверу
ssh root@149.154.66.216

# Переход в директорию проекта
cd /root/sparks
```

### Шаг 2: Запуск параллельного развертывания

```bash
# Запуск скрипта параллельного развертывания
bash scripts/deploy_parallel.sh
```

**Что делает скрипт:**
1. Создает бэкап текущего состояния
2. Останавливает старые контейнеры
3. Создает новую директорию `/root/sparks_new`
4. Копирует все файлы проекта (исключая node_modules, .git и т.д.)
5. Копирует базу данных
6. Копирует конфигурационные файлы (.env, docker-compose.yml)
7. Обновляет имена контейнеров (добавляет суффикс `_new`)
8. Опционально изменяет порты для параллельной работы
9. Собирает новые образы
10. Инициализирует новые таблицы Django
11. Применяет миграции Alembic
12. Запускает новые контейнеры
13. Проверяет работоспособность

### Шаг 3: Проверка новой версии

```bash
# Переход в новую директорию
cd /root/sparks_new

# Проверка статуса контейнеров
docker compose ps

# Просмотр логов
docker compose logs -f

# Проверка конкретного сервиса
docker compose logs backend
docker compose logs frontend
docker compose logs admin

# Проверка работоспособности (если порты изменены)
curl http://localhost:8002/health  # Backend (если порт изменен)
curl http://localhost:5174/         # Frontend (если порт изменен)
curl http://localhost:8003/admin/   # Admin (если порт изменен)
```

### Шаг 4: Переключение на новую версию

После успешной проверки новой версии:

```bash
# Запуск скрипта переключения
bash scripts/switch_to_new.sh
```

**Что делает скрипт:**
1. Останавливает старые контейнеры
2. Переименовывает старую версию в резервную копию
3. Переименовывает новую версию в основную
4. Обновляет имена контейнеров на оригинальные
5. Возвращает оригинальные порты
6. Перезапускает контейнеры
7. Проверяет статус

### Шаг 5: Проверка после переключения

```bash
# Проверка работы приложения
curl https://getsparks.ru
curl https://getsparks.ru/api/v1/health
curl https://getsparks.ru/admin/

# Проверка статуса контейнеров
cd /root/sparks
docker compose ps
```

## Откат к старой версии

Если новая версия работает некорректно:

```bash
# Запуск скрипта отката
bash scripts/rollback.sh
```

**Что делает скрипт:**
1. Останавливает новые контейнеры
2. Запускает старые контейнеры
3. Проверяет статус

## Ручное выполнение команд

Если нужно выполнить шаги вручную:

### 1. Создание новой директории и копирование файлов

```bash
# Остановка старых контейнеров
cd /root/sparks
docker compose down

# Создание новой директории
mkdir -p /root/sparks_new

# Копирование файлов
rsync -av --progress \
    --exclude='node_modules' \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.venv' \
    --exclude='venv' \
    --exclude='*.db' \
    --exclude='backups' \
    --exclude='logs' \
    /root/sparks/ /root/sparks_new/

# Копирование БД
mkdir -p /root/sparks_new/data
cp /root/sparks/data/sparks.db /root/sparks_new/data/sparks.db

# Копирование .env
cp /root/sparks/.env /root/sparks_new/.env
```

### 2. Обновление docker-compose.yml

```bash
cd /root/sparks_new

# Обновление имен контейнеров
sed -i 's/container_name: sparks-backend/container_name: sparks-backend-new/g' docker-compose.yml
sed -i 's/container_name: sparks-frontend/container_name: sparks-frontend-new/g' docker-compose.yml
sed -i 's/container_name: sparks-admin/container_name: sparks-admin-new/g' docker-compose.yml
sed -i 's/container_name: sparks-nginx/container_name: sparks-nginx-new/g' docker-compose.yml
```

### 3. Запуск новых контейнеров

```bash
cd /root/sparks_new

# Сборка образов
docker compose build --no-cache

# Инициализация таблиц Django
docker compose run --rm admin python scripts/init_django_tables.py

# Применение миграций
docker compose run --rm backend alembic upgrade head

# Запуск контейнеров
docker compose up -d

# Проверка статуса
docker compose ps
```

### 4. Переключение на новую версию

```bash
# Остановка старых контейнеров
cd /root/sparks
docker compose down

# Переименование директорий
mv /root/sparks /root/sparks_old_$(date +%Y%m%d_%H%M%S)
mv /root/sparks_new /root/sparks

# Обновление имен контейнеров обратно
cd /root/sparks
sed -i 's/container_name: sparks-backend-new/container_name: sparks-backend/g' docker-compose.yml
sed -i 's/container_name: sparks-frontend-new/container_name: sparks-frontend/g' docker-compose.yml
sed -i 's/container_name: sparks-admin-new/container_name: sparks-admin/g' docker-compose.yml

# Перезапуск контейнеров
docker compose down
docker compose up -d
```

## Важные замечания

1. **Порты:** По умолчанию новые контейнеры будут использовать те же порты, что и старые. Если нужно тестировать параллельно, измените порты в docker-compose.yml.

2. **Nginx:** Если используете Nginx, обновите конфигурацию для проксирования на новые контейнеры после переключения.

3. **База данных:** БД копируется один раз при создании новой версии. Изменения в новой версии не будут синхронизироваться со старой.

4. **Время простоя:** При переключении будет небольшой простой (несколько секунд) пока контейнеры перезапускаются.

5. **Резервные копии:** Старые версии сохраняются в `/root/sparks_old_*`. Можно удалить их через несколько дней после успешного развертывания.

## Очистка старых версий

```bash
# Удаление старых резервных копий (через несколько дней после успешного развертывания)
rm -rf /root/sparks_old_*

# Удаление неиспользуемых Docker образов
docker system prune -a
```

## Проверка использования дискового пространства

```bash
# Размер директорий
du -sh /root/sparks*
du -sh /root/sparks/backups/*

# Использование Docker
docker system df
```

## Устранение проблем

### Проблема: Новые контейнеры не запускаются

```bash
cd /root/sparks_new
docker compose logs
docker compose ps
```

### Проблема: Конфликт портов

Если порты не были изменены и старые контейнеры все еще работают:

```bash
# Остановка старых контейнеров
cd /root/sparks
docker compose down
```

### Проблема: БД не копируется

```bash
# Проверка существования БД
ls -lh /root/sparks/data/sparks.db

# Ручное копирование
mkdir -p /root/sparks_new/data
cp /root/sparks/data/sparks.db /root/sparks_new/data/sparks.db
```

## Быстрый старт

```bash
# 1. Параллельное развертывание
cd /root/sparks
bash scripts/deploy_parallel.sh

# 2. Проверка (подождите несколько минут)
cd /root/sparks_new
docker compose ps
docker compose logs -f

# 3. Переключение (если все работает)
bash scripts/switch_to_new.sh

# 4. Откат (если что-то не так)
bash scripts/rollback.sh
```

