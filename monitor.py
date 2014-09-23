import time, base64
from remote import *
from user import User
from helpers import send_to_queue
import email.utils, oauth2client, datetime

def get_header(message, name):
  for header in message['payload']['headers']:
    if header['name'] == name:
      return header['value']
  return None

while True:
  for u in users.find({'disabled': True}):
    user = User(u['email'])
    expiry_date = datetime.datetime.utcnow() - datetime.timedelta(hours=1)
    if user.get('disabled_at', expiry_date) <= expiry_date:
      user.set('disabled', False)
  for u in users.find({'disabled': {'$ne': True}}):
    user = User(u['email'])
    try:
      messages, history_token = user.get_new_messages()
    except oauth2client.client.AccessTokenRefreshError:
      print "Disabled User {}".format(user.get('_id'))
      user.update({'disabled': True, 'disabled_at': datetime.datetime.utcnow()})
      continue
    user.set('history_token', history_token)
    for message in messages:
      if 'TRASH' in message.get('labelIds', []):
        continue
      if processed_data.find_one({'email_id': message['id']}):
        continue
      if message['payload']['mimeType'] in ['text/plain', 'text/html']:
        body = message['payload']['body'].get('data')
        mime_type = message['payload']['mimeType']
      else:
        parts = message['payload']['parts']
        body = None
        mime_type = None
        order = ['text/plain', 'text/html']
        from_email =  email.utils.parseaddr(get_header(message, 'From'))[1]
        if any([x in from_email for x in ['eventbrite.com']]):
          order.reverse()
        for part in parts:
          if part['mimeType'] == order[0]:
            body = part['body'].get('data')
            mime_type = part['mimeType']
            break
        if body is None:
          for part in parts:
            if part['mimeType'] == order[1]:
              body = part['body'].get('data')
              mime_type = part['mimeType']
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
      message['payload']['mimeType'] = mime_type
      try:
        object_id = raw_data.insert(message)
        send_to_queue({'object_id': str(object_id)})
        print "Processed {}".format(message['id'])
      except:
        print "Ignored duplicate {}".format(message['id'])
        continue
  time.sleep(10)
