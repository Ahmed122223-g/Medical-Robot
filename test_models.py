import requests

api_key = 'sk_ababbf8165c8f7cc4d7f04ed2cccb1acb283ef7b3cbb8fad'
headers = {
    'xi-api-key': api_key,
    'Content-Type': 'application/json'
}

for model in ['eleven_turbo_v2_5', 'eleven_multilingual_v2', 'eleven_turbo_v2']:
    url = 'https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB'
    payload = {'text': 'Hello', 'model_id': model}
    print(f"\nTesting {model}...")
    response = requests.post(url, headers=headers, json=payload)
    print(f'Status: {response.status_code}')
    if response.status_code != 200:
        print(f'Error: {response.text}')
