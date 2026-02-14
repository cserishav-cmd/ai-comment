import requests

try:
    response = requests.get('http://localhost:5000/api/styles')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Styles count: {len(data.get('styles', []))}")
        print(f"First 5 styles: {data.get('styles', [])[:5]}")
    else:
        print(f"Error: {response.text}")
except Exception as e:
    print(f"Exception: {e}")
