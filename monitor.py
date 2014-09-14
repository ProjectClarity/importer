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
      if 'TRASH' in message.get('labelIds', []):
        continue
      if message['payload']['mimeType'] in ['text/plain', 'text/html']:
        body = message['payload']['body'].get('data')
      else:
        parts = message['payload']['parts']
        body = None
        order = ['text/plain', 'text/html']
        if any([x in email.utils.parseaddr(get_header(message, 'From')) for x in ['eventbrite.com']]):
          order.reverse()
        for part in parts:
          if part['mimeType'] == order[0]:
            body = part['body'].get('data')
            break
        if body is None:
          for part in parts:
            if part['mimeType'] == order[1]:
              body = part['body'].get('data')
              break
        if body is None:
          continue
        del message['payload']['parts']
      body = str(body)
      try:
        message['payload']['body'] = base64.urlsafe_b64decode(body)
      except TypeError:
        continue
      message['userid'] = u['_id']
      message['payload']['headers'].append({"name": "X-Time-Zone", "value": user.get_timezone()})
      try:
        object_id = raw_data.insert(message)
        send_to_queue({'object_id': str(object_id)})
        print "Processed {}".format(message['id'])
      except:
        print "Ignored duplicate {}".format(message['id'])
        continue
  time.sleep(30)

def get_header(message, name):
  for header in message['payload']['headers']:
    if header['name'] == name:
      return header['value']
  return None
