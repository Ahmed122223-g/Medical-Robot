import requests

api_key = 'sk_ababbf8165c8f7cc4d7f04ed2cccb1acb283ef7b3cbb8fad'
url = 'https://api.elevenlabs.io/v1/voices'
headers = {'xi-api-key': api_key}

try:
    response = requests.get(url, headers=headers)
    print(f'Status: {response.status_code}')
    if response.status_code == 200:
        data = response.json()
        voices = data.get('voices', [])
        print(f'Found {len(voices)} voices.')
        for v in voices[:5]:
            print(f"- {v['name']} ({v['voice_id']}) Category: {v.get('category')}")
    else:
        print(f'Error: {response.text}')
except Exception as e:
    print(f'Exception: {e}')
