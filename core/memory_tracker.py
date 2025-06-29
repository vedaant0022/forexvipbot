# core/memory_tracker.py

import json
import os
from datetime import datetime, timedelta

MEMORY_FILE = "live_trading/trade_memory.json"
EXPIRY_HOURS = 48  # forget signal after 2 days

class MemoryTracker:
    def __init__(self):
        self.memory = {}
        self.load()

    def load(self):
        if os.path.exists(MEMORY_FILE):
            with open(MEMORY_FILE, 'r') as f:
                try:
                    self.memory = json.load(f)
                except json.JSONDecodeError:
                    self.memory = {}
        else:
            self.memory = {}

    def save(self):
        with open(MEMORY_FILE, 'w') as f:
            json.dump(self.memory, f, indent=2, default=str)

    def already_traded(self, symbol, signal_time, direction):
        key = f"{symbol}_{direction}"
        signal_time_str = str(signal_time)
        if key in self.memory:
            existing = self.memory[key]
            # Check time + expiry window
            last_time = datetime.fromisoformat(existing['signal_time'])
            now = datetime.now()
            if last_time >= signal_time:
                return True
            if now - last_time > timedelta(hours=EXPIRY_HOURS):
                # Expire it
                self.memory.pop(key, None)
                self.save()
        return False

    def mark_traded(self, symbol, signal_time, direction):
        key = f"{symbol}_{direction}"
        self.memory[key] = {
            "signal_time": str(signal_time),
            "marked_at": str(datetime.now())
        }
        self.save()

    def clear(self):
        self.memory = {}
        self.save()
