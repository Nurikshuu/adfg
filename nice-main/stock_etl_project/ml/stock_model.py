import pandas as pd
import joblib
import lightgbm as lgb
import numpy as np
import matplotlib.pyplot as plt

from clickhouse_driver import Client
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

def create_features(df):
    df['return'] = df['close'].pct_change()
    df['volatility'] = df['return'].rolling(window=5).std()
    df['ma5'] = df['close'].rolling(window=5).mean()
    df['ma10'] = df['close'].rolling(window=10).mean()
    df['day_of_week'] = pd.to_datetime(df['timestamp']).dt.dayofweek
    df = df.dropna()
    return df

def train_model():
    print("📡 Connecting to ClickHouse...")
    client = Client(host='clickhouse', user='etl_user', password='Mika2u7w')

    print("📥 Fetching data from ClickHouse...")
    query = "SELECT timestamp, open, high, low, close, volume FROM stock.daily_stock"
    data = client.execute(query)
    df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
    df['timestamp'] = pd.to_datetime(df['timestamp'])

    print("🧪 Creating features...")
    df = create_features(df)
    df['target'] = df['close'].shift(-1)
    df = df.dropna()

    features = ['open', 'high', 'low', 'close', 'volume', 'return', 'volatility', 'ma5', 'ma10', 'day_of_week']
    X = df[features]
    y = df['target']

    print("📊 Splitting train/test sets...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)

    print("🧠 Training LightGBM model...")
    model = lgb.LGBMRegressor(n_estimators=100, learning_rate=0.05, max_depth=5, random_state=42)
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)

    print("📈 Evaluating model...")
    mae = mean_absolute_error(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    r2 = r2_score(y_test, y_pred)

    print(f"✅ MAE: {mae:.4f}")
    print(f"✅ RMSE: {rmse:.4f}")
    print(f"✅ R²: {r2:.4f}")

    print("💾 Saving model and plot...")
    joblib.dump(model, "/opt/airflow/ml/model.joblib")

    plt.figure(figsize=(10, 5))
    plt.plot(y_test.values, label='True Price')
    plt.plot(y_pred, label='Predicted Price')
    plt.title("True vs Predicted Close Prices")
    plt.legend()
    plt.tight_layout()
    plt.savefig("/opt/airflow/ml/plot.png")

    print("🎉 Training complete. Model and plot saved.")
