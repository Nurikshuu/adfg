FROM apache/airflow:2.9.1-python3.10

# Upgrade system packages to reduce vulnerabilities
USER root
RUN apt-get update && apt-get upgrade -y && apt-get clean
USER airflow

# Install dbt Postgres
RUN pip install dbt-postgres

# Copy dbt project (если нужно)
COPY dbt /opt/dbt

RUN pip install "pendulum<3.0.0"

USER root

# Установка системной зависимости для LightGBM
RUN apt-get update && apt-get install -y libgomp1

# Копируем скрипт и requirements
COPY create_user.sh /create_user.sh
COPY requirements.txt /requirements.txt
RUN chmod +x /create_user.sh

USER airflow


# Установка зависимостей под пользователем airflow
RUN pip install --no-cache-dir clickhouse-driver dbt-core dbt-clickhouse && \
    pip install --no-cache-dir -r /requirements.txt

ENTRYPOINT ["/create_user.sh"]
CMD ["airflow", "webserver"]
