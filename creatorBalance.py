import requests
import json

def creator_balance(creator):
    url = "https://solana-mainnet.g.alchemy.com/v2/U7AyrpMfSAzCbMVIAqpVMWJiWxqKxZdb"
    
    payload = {
        "id": 1,
        "jsonrpc": "2.0",
        "method": "getBalance",
        "params": [creator]
    }
    
    headers = {
        "accept": "application/json",
        "content-type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers)
    
    # Преобразуем текст ответа в словарь
    response_data = json.loads(response.text)

    # Извлекаем значение "value"
    value = response_data["result"]["value"]

    # Возвращаем значение, деленное на 1 000 000 000
    return round(value / 1000000000, 2)