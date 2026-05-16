import os
import requests
from flask import Flask, render_template, send_from_directory
from top_screen import calculate_m15_entry

app = Flask(__name__)

def get_all_moex_tickers():
    """Автоматически загружает ВСЕ активные акции с Московской Биржи"""
    tickers = []
    start = 0
    while True:
        url = f"https://moex.com{start}"
        try:
            res = requests.get(url).json()
            data = res['history']['data']
            if not data:
                break
            for row in data:
                # Берем только уникальные краткие тикеры (например, SBER)
                if row[3] not in tickers:
                    tickers.append(row[3])
            start += 100
        except:
            break
    # Если биржа не ответила, даем базовый защитный список
    return tickers if tickers else ['SBER', 'LKOH', 'GAZP', 'NVTK', 'ROSN', 'GMKN', 'MGNT']

@app.route('/')
def index():
    all_tickers = get_all_moex_tickers()
    total_count = len(all_tickers)
    signals = []
    
    # Сканируем абсолютно каждый тикер на бирже
    for ticker in all_tickers:
        try:
            result = calculate_m15_entry(ticker)
            if result:
                signals.append(result)
        except Exception as e:
            print(f"Ошибка {ticker}: {e}")
            
    return render_template('index.html', signals=signals, total_count=total_count)

@app.route('/bull.png')
def custom_static():
    return send_from_directory(os.getcwd(), 'bull.png')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 80)))
