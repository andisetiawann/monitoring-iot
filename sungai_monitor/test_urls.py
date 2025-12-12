#!/usr/bin/env python
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'sungai_monitor.settings')
sys.path.insert(0, os.path.dirname(__file__))
django.setup()

from django.test import Client
from django.urls import reverse

def test_urls():
    client = Client()

    print('Testing URL resolution...')
    try:
        login_url = reverse('login')
        print(f'Login URL: {login_url}')
    except Exception as e:
        print(f'Error reversing login: {e}')
        return

    try:
        dashboard_url = reverse('dashboard')
        print(f'Dashboard URL: {dashboard_url}')
    except Exception as e:
        print(f'Error reversing dashboard: {e}')
        return

    print('\nTesting HTTP responses...')
    # Test login page
    response = client.get('/login/')
    print(f'Login page status: {response.status_code}')

    # Test root page (should redirect to login)
    response = client.get('/')
    print(f'Root page status: {response.status_code}')
    if response.status_code == 302:
        print(f'Redirect location: {response["Location"]}')

if __name__ == '__main__':
    test_urls()