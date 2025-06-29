import csv
import os

def log_trade(trade_data, path='logs/live_trades.csv'):
    file_exists = os.path.isfile(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, mode='a', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=trade_data.keys())
        if not file_exists:
            writer.writeheader()
        writer.writerow(trade_data)
