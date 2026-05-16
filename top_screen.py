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
