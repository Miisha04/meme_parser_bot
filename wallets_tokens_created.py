import requests
import json

def rugs_checker(creator):
    url = f'https://frontend-api.pump.fun/coins/user-created-coins/{creator}'
    
    params = {
        'limit': 1000,
        'offset': 0,
        'includeNsfw': 'true'
    }
    
    headers = {
        'accept': '*/*'
    }

    proxies = {
        'http': 'http://user132834:gyckq8@45.159.180.71:3840',
        'https': 'http://user132834:gyckq8@45.159.180.71:3840'
    }

    # Инициализация переменных
    rugs, lowcaps, middle_caps, high_caps = 0, 0, 0, 0

    try:
        # Запрос к API
        response = requests.get(url, headers=headers, params=params, proxies=proxies)

        if response.status_code == 200:
            data = response.json()

            # Проходим по данным и проверяем необходимые условия
            for metrics in data:
                usd_market_cap = metrics.get('usd_market_cap', 0)
                complete = metrics.get('complete', False)
                
                if not complete:
                    rugs += 1
                elif 100000 <= usd_market_cap <= 500000:
                    lowcaps += 1
                elif 500001 <= usd_market_cap <= 3000000:
                    middle_caps += 1
                elif usd_market_cap > 3000000:
                    high_caps += 1

            # Возвращаем значения в формате "rugs/lowcaps/middle_caps/high_caps"
            return f"{rugs}/{lowcaps}/{middle_caps}/{high_caps}"
        else:
            print(f"Ошибка запроса: {response.status_code}")
            return None
    except requests.exceptions.ProxyError as e:
        print(f"Ошибка прокси: {e}")
        return None