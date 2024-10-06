import requests

from config import LOGIN, PASSWORD, PROXY_HOST, PROXY_PORT


# Заголовки с пользовательским агентом
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0'
}

# Прокси-сервер
proxy_url = f'socks5://{LOGIN}:{PASSWORD}@{PROXY_HOST}:{PROXY_PORT}'


def get_data_from_pumpfun(url):
    try:
        response = requests.get(url, headers=headers, proxies=proxy_url)
        response.raise_for_status()  # Проверка на ошибки HTTP
        return response.text  # Возвращаем текст ответа
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None
