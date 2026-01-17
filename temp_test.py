#!/usr/bin/env python3
import os
from dotenv import load_dotenv
load_dotenv()
gemini_api_key = os.getenv('GEMINI_API_KEY')
print('API key loaded:', bool(gemini_api_key))
from src.identity.identity_manager import IdentityManager
print('Creating manager...')
manager = IdentityManager('test_user', gemini_api_key, './data/profiles')
print('Manager created')
print('Profile maturity:', manager.identity_profile.profile_maturity)
print('Simulating exchanges...')
test_exchanges = [
    {'user': 'Yeah so I am building this React app for the hackathon', 'ai': 'Nice! What kind of app are you building?'},
    {'user': 'It is an AI companion that learns your communication style', 'ai': 'That sounds interesting. How does it learn the style?'},
    {'user': 'It analyzes how you speak and adapts to match your patterns', 'ai': 'Cool approach. Are you using any specific models for that?'},
    {'user': 'Just Gemini for everything, keeping it simple', 'ai': 'Good call. Simpler is often better for hackathons.'},
    {'user': 'Exactly, no time for complicated setups', 'ai': 'Makes sense. How is it going so far?'},
]
for i, exchange in enumerate(test_exchanges, 1):
    print(f'Exchange {i}')
    manager.on_new_exchange(i, exchange['user'], exchange['ai'])
print('Exchanges done')
import time
print('Waiting 3 seconds...')
time.sleep(3)
print('Checking update...')
updated = manager.profile_was_updated()
print('Profile updated:', updated)
print('Cleanup...')
manager.cleanup()
print('Done')