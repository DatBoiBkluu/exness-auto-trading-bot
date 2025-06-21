import MetaTrader5 as mt5
import time
import json
import requests

# Load config
with open('config.json') as f:
    config = json.load(f)

MT5_LOGIN = config['mt5']['login']
MT5_PASSWORD = config['mt5']['password']
MT5_SERVER = config['mt5']['server']
RISK_ZAR = config['risk']['max_zar_loss']

def connect_mt5():
    if not mt5.initialize(login=MT5_LOGIN, server=MT5_SERVER, password=MT5_PASSWORD):
        print("MT5 initialize() failed")
        return False
    print("MT5 connected")
    return True

def calculate_lot_size(symbol, sl_pips):
    symbol_info = mt5.symbol_info(symbol)
    if symbol_info is None:
        print("Symbol info not found")
        return 0.01
    tick_value = symbol_info.trade_tick_value
    tick_size = symbol_info.trade_tick_size
    if tick_value == 0 or tick_size == 0:
        return 0.01
    lot = RISK_ZAR / (sl_pips * (tick_value / tick_size))
    lot = max(0.01, min(lot, symbol_info.volume_max))
    return round(lot, 2)

def get_signals():
    try:
        response = requests.get('https://your-signal-api.example.com/latest')
        return response.json()
    except:
        return []

def place_trade(signal):
    symbol = signal['symbol']
    action = signal['action']
    entry = signal['entry']
    sl = signal['sl']
    tp = signal['tp']
    sl_pips = abs(entry - sl) * 10000
    lot = calculate_lot_size(symbol, sl_pips)
    request_type = mt5.ORDER_TYPE_BUY if action == 'buy' else mt5.ORDER_TYPE_SELL
    price = mt5.symbol_info_tick(symbol).ask if action == 'buy' else mt5.symbol_info_tick(symbol).bid
    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": request_type,
        "price": price,
        "sl": sl,
        "tp": tp,
        "deviation": 10,
        "magic": 123456,
        "comment": "AutoTradeBot"
    }
    result = mt5.order_send(request)
    if result.retcode != mt5.TRADE_RETCODE_DONE:
        print(f"Failed to place trade on {symbol}: {result.retcode}")
    else:
        print(f"Trade placed on {symbol}: {action} {lot} lots")

def main():
    if not connect_mt5():
        return
    while True:
        signals = get_signals()
        for signal in signals:
            place_trade(signal)
        time.sleep(3600)

if __name__ == "__main__":
    main()
