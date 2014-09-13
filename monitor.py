import time, base64
from remote import *
from user import User
from helpers import send_to_queue

while True:
  for u in users.find({}):
    user = User(u['email'])
    messages, history_token = user.get_new_messages()
    user.set('history_token', history_token)
    for message in messages:
      if message['payload']['mimeType'] in ['text/plain', 'text/html']:
        body = message['payload']['body']['data']
      else:
        parts = message['payload']['parts']
        body = None
        for part in parts:
          if part['mimeType'] == 'text/plain':
            body = part['body']['data']
            break
        if body is None:
          for part in parts:
            if part['mimeType'] == 'text/html':
              body = part['body']['data']
              break
        if body is None:
          continue
        del message['payload']['parts']
      message['payload']['body'] = base64.b64decode(body)
      message['userid'] = u['_id']
      try:
        object_id = raw_data.insert(message)
        send_to_queue({'object_id': str(object_id)})
        print "Processed {}".format(message['id'])
      except:
        print "Ignored duplicate {}".format(message['id'])
        continue
  time.sleep(30)
