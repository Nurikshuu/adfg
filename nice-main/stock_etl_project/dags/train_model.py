import sys
import os
sys.path.append('/opt/airflow/ml')  # добавляем путь к каталогу с моделью

from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime
from stock_model import train_model  # ИМЕННО так! Без `ml.`, потому что путь уже указан вручную

default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 1, 1),
    'retries': 1,
}

with DAG(
    dag_id='train_stock_model',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False
) as dag:

    train_model_task = PythonOperator(
        task_id='train_model',
        python_callable=train_model
    )
