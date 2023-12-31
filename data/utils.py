import psycopg2
import os
from data.hh import HeadHunterAPI
from data.settings import DBdata


def create_connection():
    connection = psycopg2.connect(
        database=DBdata['db_name'],
        user=DBdata['db_user'],
        password=DBdata['db_password'],
        host=DBdata['db_host']
    )
    return connection


def create_database():
    """
    Создание базы данных
    """

    conn_data = psycopg2.connect(host="localhost", database=f"{DBdata['db_name'][0]}",
                                 user="postgres", password=f"{DBdata['db_password']}", client_encoding="utf-8")

    conn_data.autocommit = True
    cur = conn_data.cursor()

    # Проверка существования базы данных
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", ('course_work_5',))
    exists = cur.fetchone()

    if not exists:
        # Создание базы данных
        cur.execute("CREATE DATABASE course_work_5")

    cur.close()


def create_tables():
    """
    Функция для создания таблиц
    """
    conn_data = psycopg2.connect(host="localhost", database=f"{DBdata['db_name'][1]}",
                                 user="postgres", password=f"{DBdata['db_password']}", client_encoding="utf-8")
    with conn_data as conn_:
        with conn_.cursor() as cur:
            # Создание таблиц

            cur.execute("""
                        CREATE TABLE IF NOT EXISTS companies (
                        company_id INTEGER PRIMARY KEY,
                        company_name varchar(255),
                        url varchar(150),
                        open_vacancies INTEGER
                        )""")

            cur.execute("""
                        CREATE TABLE IF NOT EXISTS vacancies (
                        vacancy_id SERIAL PRIMARY KEY,
                        vacancies_name varchar(255),
                        salary_from INTEGER,
                        salary_to INTEGER,
                        currency varchar(10),
                        requirement TEXT,
                        vacancies_url TEXT,
                        company_id INTEGER REFERENCES companies(company_id)
                        )""")

            conn_.commit()


def add_to_table(companies):
    conn_data = psycopg2.connect(host="localhost", database="course_work_5",
                                 user="postgres", password=f"{DBdata['db_password']}", client_encoding="utf-8")
    data_hh = HeadHunterAPI()
    companies_data = data_hh.get_companies(companies)
    with conn_data as conn_:
        with conn_.cursor() as cur:
            for company in companies_data:
                # Получение данных о компании по API
                # Добавление компании в таблицу с игнорированием конфликта
                cur.execute('INSERT INTO companies (company_id, company_name, url, open_vacancies) '
                            'VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING RETURNING company_id',
                            (company['company_id'], company['company_name'],
                             company['url'], company['open_vacancies']))

                # Получение вакансий для компании по API
                vacancies_list = data_hh.get_vacancies(company['company_id'])

                i = 0
                for vacancy_data in vacancies_list:
                    if i <= 10:
                        i += 1
                        cur.execute('INSERT INTO vacancies (vacancy_id, vacancies_name, '
                                    'salary_from, salary_to, currency, '
                                    'requirement, vacancies_url, company_id) '
                                    'VALUES (%s, %s, %s, %s, %s, %s, %s, %s) ON CONFLICT DO NOTHING',
                                    (vacancy_data['vacancy_id'], vacancy_data['vacancies_name'],
                                     int(vacancy_data['salary_from']), int(vacancy_data['salary_to']),
                                     vacancy_data['currency'], vacancy_data['requirement'],
                                     vacancy_data['vacancy_url'], vacancy_data['company_id']))
                    else:
                        break

            conn_.commit()
