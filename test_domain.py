import urllib.request
import sys

url = 'https://homehni.com'
try:
    response = urllib.request.urlopen(url, timeout=5)
    print(f'[SUCCESS] Domain is accessible! Status: {response.getcode()}')
    print('You can proceed with using the domain for PDF URLs.')
except Exception as e:
    print(f'[ERROR] Domain not accessible: {e}')
    print('You need to connect the domain first for PDF URLs to work.')

