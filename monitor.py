import time
from remote import *
from user import User

while True:
  for u in users.find({}):
    user = User(u['email'])
    messages, history_token = user.get_new_messages()
    user.set('history_token', history_token)
    for message in messages:
      print message['payload']['mimeType']
  time.sleep(1)
  print 'here'

