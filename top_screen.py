import pandas as pd
import requests

def get_weekly_signals(ticker):
    # 1. Загрузка недельных свечей с МосБиржи
    url = f"https://moex.com{ticker}/candles.json?interval=31"
    response = requests.get(url).json()
    
    data = response['candles']['data']
    columns = response['candles']['columns']
    df = pd.DataFrame(data, columns=columns)
    
    if len(df) < 200: 
        return False # Отсекаем малоликвидные акции
        
    # 2. Расчет тяжелых скользящих SMA 150 и SMA 200
    df['sma150'] = df['close'].rolling(window=150).mean()
    df['sma200'] = df['close'].rolling(window=200).mean()
    
    last_row = df.iloc[-1]
    current_price = last_row['close']
    
    # 3. Жесткое сито: тренд строго вверх
    if current_price > last_row['sma150'] and last_row['sma150'] > last_row['sma200']:
        return True
    return False

def check_daily_compression(ticker):
    # 1. Загрузка дневных свечей с МосБиржи (последние 50 дней)
    url = f"https://moex.com{ticker}/candles.json?interval=24"
    response = requests.get(url).json()
    
    data = response['candles']['data']
    columns = response['candles']['columns']
    df = pd.DataFrame(data, columns=columns)
    
    if len(df) < 20:
        return False
        
    # 2. Расчет волатильности (True Range)
    df['high_low'] = df['high'] - df['low']
    
    # Считаем короткий ATR(5) и длинный ATR(20)
    df['atr5'] = df['high_low'].rolling(window=5).mean()
    df['atr20'] = df['high_low'].rolling(window=20).mean()
    
    last_row = df.iloc[-1]
    
    # 3. Фильтр затишья: текущая волатильность сжата
    if last_row['atr5'] < last_row['atr20']:
        return True
    return False

def check_hourly_squeeze(ticker):
    # 1. Загрузка часовых свечей с МосБиржи
    url = f"https://moex.com{ticker}/candles.json?interval=60"
    response = requests.get(url).json()
    
    data = response['candles']['data']
    columns = response['candles']['columns']
    df = pd.DataFrame(data, columns=columns)
    
    if len(df) < 50:
        return False
        
    # 2. Расчет быстрых скользящих EMA 10, 21, 50
    df['ema10'] = df['close'].ewm(span=10, adjust=False).mean()
    df['ema21'] = df['close'].ewm(span=21, adjust=False).mean()
    df['ema50'] = df['close'].ewm(span=50, adjust=False).mean()
    
    last_row = df.iloc[-1]
    p_close = last_row['close']
    
    # 3. Находим максимальную и минимальную цену среди трех EMA
    max_ema = max(last_row['ema10'], last_row['ema21'], last_row['ema50'])
    min_ema = min(last_row['ema10'], last_row['ema21'], last_row['ema50'])
    
    # Считаем ширину жгута в процентах от цены
    spread_pct = ((max_ema - min_ema) / p_close) * 100
    
    # Фильтр: жгут должен быть уже 0.3% от цены акции
    if spread_pct < 0.3:
        return True
    return False

def calculate_m15_entry(ticker):
    # 1. Сквозная проверка всех старших экранов
    if not get_weekly_signals(ticker): return None
    if not check_daily_compression(ticker): return None
    if not check_hourly_squeeze(ticker): return None
    
    # 2. Если старшие ТФ согласны, загружаем М15 для расчета точек
    url = f"https://moex.com{ticker}/candles.json?interval=15"
    response = requests.get(url).json()
    
    data = response['candles']['data']
    columns = response['candles']['columns']
    df = pd.DataFrame(data, columns=columns)
    
    if len(df) < 5: return None
    
    last_row = df.iloc[-1]
    prev_row = df.iloc[-2]
    
    # Локальный Хай и Лоу для пробоя коробки
    local_high = prev_row['high']
    local_low = prev_row['low']
    current_price = last_row['close']
    
    # 3. Условие сигнала: текущая цена пробивает хай на импульсе
    if current_price > local_high:
        entry = current_price
        stop = local_low - (entry * 0.001)  # Стоп под Лоу + небольшой зазор
        risk = entry - stop
        take = entry + (risk * 3)           # Математика прибыли строго 1:3
        
        return {
            "ticker": ticker,
            "entry": round(entry, 2),
            "stop": round(stop, 2),
            "take": round(take, 2)
        }
    return None
