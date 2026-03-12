import requests

api_key = 'sk_ababbf8165c8f7cc4d7f04ed2cccb1acb283ef7b3cbb8fad'
headers = {
    'xi-api-key': api_key,
    'Content-Type': 'application/json'
}

# Try Voice ID: CwhRBWXzGAHq8TQ4Fs17 (Roger)
url = 'https://api.elevenlabs.io/v1/text-to-speech/CwhRBWXzGAHq8TQ4Fs17'
payload = {
    'text': 'مرحبا',
    'model_id': 'eleven_multilingual_v2'
}

print("Testing Roger...")
response = requests.post(url, headers=headers, json=payload)
print(f'Status: {response.status_code}')
if response.status_code != 200:
    print(f'Error: {response.text}')

# Try Voice ID: pNInz6obpgDQGcFmaJgB (Adam)
url = 'https://api.elevenlabs.io/v1/text-to-speech/pNInz6obpgDQGcFmaJgB'
print("\nTesting Adam...")
response = requests.post(url, headers=headers, json=payload)
print(f'Status: {response.status_code}')
if response.status_code != 200:
    print(f'Error: {response.text}')

