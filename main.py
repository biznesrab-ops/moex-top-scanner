import os
from flask import Flask, render_template, send_from_directory
from top_screen import calculate_m15_entry

app = Flask(__name__)

# Список основных ликвидных акций МосБиржи для сканирования
TICKERS = ['SBER', 'LKOH', 'GAZP', 'NVTK', 'ROSN', 'GMKN', 'MGNT', 'CHMF', 'TATN', 'YNDX']

@app.route('/')
def index():
    signals = []
    
    # Запускаем конвейер фильтров для каждого тикера
    for ticker in TICKERS:
        try:
            result = calculate_m15_entry(ticker)
            if result:
                signals.append(result)
        except Exception as e:
            print(f"Ошибка при сканировании {ticker}: {e}")
            
    return render_template('index.html', signals=signals)

# Маршрут для отображения картинки быка из корня проекта
@app.route('/bull.png')
def custom_static():
    return send_from_directory(os.getcwd(), 'bull.png')

if __name__ == '__main__':
    # Настройки порта для успешного запуска на Amvera
    port = int(os.environ.get("PORT", 80))
    app.run(host='0.0.0.0', port=port)
