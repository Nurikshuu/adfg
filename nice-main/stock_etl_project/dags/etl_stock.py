from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from datetime import datetime
import requests, pandas as pd
import psycopg2
from sqlalchemy import create_engine
from train_model import train_model

def fetch_data():
    response = requests.get(
        "https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey=demo&datatype=csv"
    )
    with open("/opt/airflow/dags/aapl.csv", "w") as f:
        f.write(response.text)

def load_to_postgres():
    df = pd.read_csv("/opt/airflow/dags/aapl.csv")
    df.columns = [c.lower().strip().replace(' ', '_') for c in df.columns]
    engine = create_engine("postgresql+psycopg2://postgres:Mika2u7w@postgres:5432/stockdata")
    df.to_sql("daily_stock", engine, if_exists="replace", index=False)

def transfer_to_clickhouse():
    import pandas as pd
    from sqlalchemy import create_engine
    from clickhouse_driver import Client

    # Подключение к PostgreSQL
    pg_engine = create_engine('postgresql+psycopg2://postgres:Mika2u7w@postgres:5432/stockdata')
    df = pd.read_sql("SELECT * FROM daily_stock", con=pg_engine)

    # Преобразование timestamp в datetime
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    # Подключение к ClickHouse
    client = Client(
        host='clickhouse',
        user='etl_user',
        password='Mika2u7w',
        port=9000
    )

    # Создание базы и таблицы
    client.execute('CREATE DATABASE IF NOT EXISTS stock')
    client.execute('''
        CREATE TABLE IF NOT EXISTS stock.daily_stock (
            timestamp DateTime,
            open Float64,
            high Float64,
            low Float64,
            close Float64,
            volume Int64
        ) ENGINE = MergeTree()
        ORDER BY timestamp
    ''')

    # Вставка данных
    data = [tuple(row) for _, row in df.iterrows()]
    client.execute(
        'INSERT INTO stock.daily_stock (timestamp, open, high, low, close, volume) VALUES',
        data
    )

    print("✅ Data transferred from PostgreSQL to ClickHouse.")

default_args = {
    'start_date': datetime(2025, 5, 19),
    'catchup': False
}

with DAG("etl_stock_pipeline", schedule_interval="@daily", default_args=default_args) as dag:
    fetch = PythonOperator(task_id="fetch_data", python_callable=fetch_data)
    load_pg = PythonOperator(task_id="load_postgres", python_callable=load_to_postgres)
    load_ch = PythonOperator(task_id="load_clickhouse", python_callable=transfer_to_clickhouse)

    run_dbt = BashOperator(
        task_id='run_dbt',
        bash_command="""
        if command -v dbt >/dev/null 2>&1; then
          cd /path/to/dbt && dbt run --profiles-dir .
        else
          echo "⏭ DBT temporarily skipped"
        fi
        """,
    )

    train_task = PythonOperator(task_id='train_model', python_callable=train_model)

    fetch >> load_pg >> load_ch >> run_dbt >> train_task
