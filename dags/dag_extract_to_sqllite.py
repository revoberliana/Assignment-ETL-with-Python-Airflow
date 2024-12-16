from airflow import DAG
from airflow.operators.python import PythonOperator, BranchPythonOperator
from airflow.operators.empty import EmptyOperator
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

# Default Arguments
default_args = {
    'owner': 'airflow',
    'start_date': datetime(2024, 6, 10),
    'retries': 1
}

# Fungsi Extract Data dari CSV
def extract_from_csv(**kwargs):
    file_path = 'data/7210_1.csv'
    df = pd.read_csv(file_path)
    df.to_csv('/tmp/extracted_data.csv', index=False)
    print("Extracted CSV to /tmp/extracted_data.csv")
    return '/tmp/extracted_data.csv'

# Fungsi Load ke SQLite
def load_to_sqlite(**kwargs):
    extracted_file = kwargs['ti'].xcom_pull(task_ids='extract_csv')
    db_path = 'sqlite:///data/extracted_data.db'
    engine = create_engine(db_path)
    df = pd.read_csv(extracted_file)
    df.to_sql('extracted_table', engine, if_exists='replace', index=False)
    print("Data successfully loaded to SQLite!")

# Branch Function (jika diperlukan)
def choose_branch(**kwargs):
    return 'extract_csv'  # Langsung mengeksekusi task extract_csv

# Definisi DAG
with DAG('extract_csv_to_sqlite',
         default_args=default_args,
         schedule_interval=None,
         catchup=False) as dag:

    start_task = EmptyOperator(task_id='start_task')

    branch_task = BranchPythonOperator(
        task_id='choose_branch',
        python_callable=choose_branch
    )

    extract_csv = PythonOperator(
        task_id='extract_csv',
        python_callable=extract_from_csv
    )

    load_sqlite = PythonOperator(
        task_id='load_to_sqlite',
        python_callable=load_to_sqlite
    )

    end_task = EmptyOperator(task_id='end_task')

    # Urutan Task
    start_task >> branch_task >> extract_csv >> load_sqlite >> end_task
