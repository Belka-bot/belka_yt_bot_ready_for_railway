python
import os
import requests

def upload_to_yandex(filepath: str) -> str:
    token = os.getenv('YANDEX_TOKEN')
    filename = os.path.basename(filepath)
    url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
    params = {'path': f'/telegram_bot/{filename}', 'overwrite': 'true'}
    headers = {'Authorization': f'OAuth {token}'}
    res = requests.get(url, params=params, headers=headers)
    upload_url = res.json().get('href')

    with open(filepath, 'rb') as f:
        requests.put(upload_url, data=f)

    return f"https://cloud-api.yandex.net/v1/disk/resources/download?path=/telegram_bot/{filename}"