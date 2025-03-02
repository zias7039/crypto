import requests
import datetime

class PriceFetcherThread:
    def __init__(self, symbols):
        self.symbols = symbols

    def fetch(self):
        results = {}
        usd_to_krw = self.fetch_usd_krw_rate()
        with requests.Session() as sess:
            binance_map = {}
            upbit_map = {}
            upbit_symbols = {}
            morning_map = {}

            for symbol in self.symbols:
                binance_price = self.fetch_binance_price(sess, symbol)
                morning_price = self.fetch_morning_price(sess, symbol)
                up_sym = self.to_upbit_symbol(symbol)
                binance_map[symbol] = binance_price
                morning_map[symbol] = morning_price
                if up_sym:
                    upbit_symbols[symbol] = up_sym

            upbit_markets = list(upbit_symbols.values())
            upbit_price_map = {}
            if upbit_markets:
                try:
                    url = "https://api.upbit.com/v1/ticker"
                    r = sess.get(url, params={"markets": ",".join(upbit_markets)})
                    for item in r.json():
                        upbit_price_map[item["market"]] = float(item["trade_price"])
                except Exception as e:
                    logging.error(f"Upbit 조회 실패: {e}")

        for symbol in self.symbols:
            binance_price = binance_map.get(symbol)
            morning_price = morning_map.get(symbol)
            kimchi_premium = None
            morning_diff = None

            if binance_price is not None and morning_price and morning_price > 0:
                diff = binance_price - morning_price
                morning_diff = (diff / morning_price) * 100

            if binance_price is not None and usd_to_krw > 0:
                up_sym = upbit_symbols.get(symbol)
                if up_sym and up_sym in upbit_price_map:
                    up_price = upbit_price_map[up_sym]
                    kimchi_premium = ((up_price - (binance_price * usd_to_krw))
                                      / (binance_price * usd_to_krw)) * 100

            results[symbol] = (binance_price, morning_diff, kimchi_premium)

        self.result_ready.emit(results)

    def fetch_usd_krw_rate(self):
        try:
            r = requests.get("https://api.exchangerate-api.com/v4/latest/USD")
            return float(r.json()["rates"]["KRW"])
        except:
            return 0.0

    def fetch_binance_price(self, sess, symbol):
        try:
            r = sess.get("https://api.binance.com/api/v3/ticker/price", params={"symbol": symbol})
            return float(r.json()["price"])
        except:
            return None

    def fetch_morning_price(self, sess, symbol):
        try:
            today = datetime.date.today()
            nine_am = datetime.datetime(today.year, today.month, today.day, 9, 0, 0)
            ts = int(nine_am.timestamp() * 1000)
            url = "https://api.binance.com/api/v3/klines"
            r = sess.get(url, params={
                "symbol": symbol, "interval": "1h",
                "startTime": ts, "endTime": ts + 3600000, "limit": 1
            })
            data = r.json()
            if data and len(data) > 0:
                return float(data[0][1])
        except:
            pass
        return None

    def to_upbit_symbol(self, binance_symbol):
        if binance_symbol.endswith("USDT"):
            return "KRW-" + binance_symbol.replace("USDT", "")
        return results
