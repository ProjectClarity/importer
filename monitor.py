from remote import *
from user import User

while True:
  for u in users.find({}):
    user = User(u['email'])
    gmail_service = user.build('gmail', v='v1')
