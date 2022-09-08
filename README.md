# SPAAACE-calendar

### Для запуска в докере необходимо выполнить следующие действия
- docker build -t calendar .
- docker-compose up -d

Далее необходмо выполнить инициализацию базы. Для этого надо выполнить следующие шаги:
- docker cp .\dump.sql calendar_postgres:/
- docker exec -it calendar_postgres /bin/bash
- psql -U user -d test -W -f dump.sql (имя пользователя (user) и имя базы (test) задаются через переменные окружение в compose файле,
если вы их там изменили, тут они должны соответствовать новым)

### Стэк
Для бэка используется **Python (3.10.5)** с микрофреймворком **Flask (2.2.2)**.
На фронте обычный **HTML**/**CSS**/**JS**(**Jquery**), с использованием **bootstrap 5** для упрощения верстки.
В качестве базы данных используется **PostgreSQL (14.3)**.

### Окружение
Проект расчитан на запуск на Linux. Для полноценного рабочего окружения необходимо:
- Установить Python, желательно актуальной версии
- Установить pip, скачать нужные пакеты, указанные в файле requirements.txt
- Установить и настроить postgres
- Запустить проект

Далее, каждый пункт будет описан отдельно. К сожалению, не могу дать точных инструкций, так как не знаю, в каком виде будет разворачиваться проект.

Перед установкой новых пакетов не забываем обновляться:
```
sudo apt-get update
```
```
sudo apt-get upgrade
```

##### Установка Python
По дефолту Python3 стоит на всех современных дистрибутивах, как минимум debian подобных.
На всякий случай, для установки:
```
sudo apt-get install python3
```
Чтобы проверить версию:
```
python3 --version
```

##### Установка PIP
Как и Python3, pip стоит на большинстве современных дистрибутивов.
На всякий случай, для установки:
```
sudo apt-get install python3-pip
```

##### Установка python зависимостей
В репозитории находится файл `requirements.txt`, для установки необходимых зависимостей выполните команду:
```
pip install -r requirements.txt
```

##### Установка postgres
Для установки PostgreSQL используем следующую команду:
```
sudo apt install postgresql postgresql-contrib
```
Дальнейшее развертывание и настройку можно производить по своим нуждам и желаниям, на всякий случай, вот неплохой [гайд](https://www.digitalocean.com/community/tutorials/how-to-install-postgresql-on-ubuntu-20-04-quickstart "гайд").

Как минимум, ее надо поднять:
```
sudo systemctl start postgresql.service
```

Нам важен один момент! Это создание пользователя с паролем и базы данных, которая ему принадлежит. Происходит это в терминале psql. Чтобы зайти туда под стандартным пользователем вводим:
```
psql -U postgres -d postgres
```
Создаем пользователя:
```
CREATE ROLE username with PASSWORD 'password' LOGIN;
```
Создаем бд:
```
CREATE DATABASE calendar OWNER username;
```

Осталось лишь мигрировать нашу бд. В репозитории находится dump.sql, там лежит информация о структуре нашей бд и базовая информация. Грузим данные:
```
psql -U username -d calendar -W -f dump.sql
```
#### Запуск
Последнее, что осталось - запуск. Поднимать приложение можно как напрямую через интерпритатор питона, так и грамотно, например: gunicorn, вот хороший [гайд](https://www.digitalocean.com/community/tutorials/how-to-deploy-python-wsgi-apps-using-gunicorn-http-server-behind-nginx#downloading-and-installing-gunicorn "гайд") по нему.

В любом варианте запуска нам очень важны несколько env переменных, а именно:
```
DB_USER=username
DB_PASS=password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=calendar
FLASK_ENV=production
UNISENDER_TOKEN=614mpmfijiyn3ztz5kt916x4epnqgypmbtacy9oy
RECEIVER_EMAIL=address@mail.ru
```

С соответственно правильными данными, UNISENDER_TOKEN это токен для сервиса отправки email уведомлений, RECEIVER_EMAIL это почта, на которую эти уведомления должны приходить, лишь FLASK_ENV остается со значением production.

Логи, ошибки и тд, все подобные моменты сильно зависят от того, как будет собираться и запускаться проект. Лишь по дефолту лог flask'a идет в stdout.

### Архитектура
Все очень минималистично, никаких сложностей нету. Основной файл **app.py** отвечает за весь бэк приложения, в **db.py** лежат функции для соединения с бд. В папке **templates** - шаблоны html. Больше особо и нечего сказать.

### API

- **Получение данных о записях**
Запрос:
```
[GET] /api/get?from=2022.09.01&to=2022.09.30
```
Ответ:
```
[
	{
		"booking": [
			{
				"email": "test@test.com",
				"finish": "13:00",
				"id": "U44KUG",
				"name": "Николай",
				"note": "Заметки о заявке",
				"products": [
					{
						"id": "VF2XC5",
						"name": "TEST"
					},
					{
						"id": "C3SPKG",
						"name": "TEST1"
					}
				],
				"start": "08:00"
			}
		],
		"date": "2022.09.07",
		"finish": "14:00",
		"id": "C517FZ",
		"start": "07:00"
	}
]
```

- **Заявка**
Запрос:
```
[POST] /api/book
{
	"date": "2022.9.7",
	"start": "8:00",
	"finish": "13:00",
	"name": "Николай",
	"email": "test@test.com",
	"note": "Заметки о заявке",
	"products": [
		"id": "VF2XC5"
	]
}
```
Ответ:
```
{
	"email": "test@test.com",
	"finish": "13:00",
	"id": "4J2T1C",
	"name": "Николай",
	"note": "Заметки о заявке",
	"products": [
		"VF2XC5"
	],
	"start": "08:00"
}
```

- **Продукты**
Запрос:
```
[GET] /api/products
```
Ответ:
```
[
	{
		"id": "VF2XC5",
		"name": "TEST"
	},
	{
		"id": "C3SPKG",
		"name": "TEST1"
	}
]
```
