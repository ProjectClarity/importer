from helpers import build as helpers_build
from helpers import flatmap
from remote import users
from oauth2client.client import OAuth2Credentials
import json, time, apiclient

class User():
  def __init__(self, email):
    self.user = users.find_one({'email': email})

  def get(self, key):
    return self.user.get(key, '')

  def set(self, key, value):
    self.update({key: value})

  def update(self, d):
    users.update({'_id': self.user['_id']}, {'$set': d})
    self.user = users.find_one({'_id': self.get('_id')})

  def get_credentials(self):
    return OAuth2Credentials.from_json(json.dumps(self.get('credentials')))

  def get_timezone(self):
    timezone = self.get('timezone')
    if not timezone:
      calendar_service = self.build('calendar', v='v3')
      default_calendar = calendar_service.calendars().get(calendarId='primary').execute()
      self.set('timezone', default_calendar['timeZone'])
    return timezone

  def get_history_token(self):
    history_token = self.get('history_token')
    if not history_token:
      gmail_service = self.build('gmail', v='v1')
      threads = gmail_service.users().threads().list(userId='me', maxResults=1).execute()['threads']
      history_token = threads[0]['historyId']
      self.set('history_token', history_token)
    return history_token

  def get_new_messages(self):
    gmail_service = self.build('gmail', v='v1')
    history_token = self.get_history_token()
    history = gmail_service.users().history().list(userId='me', startHistoryId=history_token).execute()
    changes = history['history'] if 'history' in history else []
    while 'nextPageToken' in history:
      page_token = history['nextPageToken']
      history = gmail_service.users().history().list(userId='me', startHistoryId=history_token, pageToken=page_token).execute()
      changes.extend(history['history'])
    messages = flatmap(lambda x: x['messages'], changes)
    thread_ids = set([x['threadId'] for x in messages])
    def get_thread(x):
      try:
        return gmail_service.users().threads().get(userId='me', id=x).execute()
      except:
        return None
    threads = filter(lambda x: bool(x), map(get_thread , thread_ids))
    full_messages = map(lambda x: x['messages'][0], threads)
    return full_messages, history['historyId']

  def tag_message(self, message_id, tags):
    gmail_service = self.build('gmail', v='v1')
    labels = {x['name']:x['id'] for x in gmail_service.users().labels().list(userId='me').execute()['labels']}
    for tag in tags:
      if tag not in labels.keys():
        label = {'messageListVisibility': 'show', 'name': tag, 'labelListVisibility': 'labelShow'}
        labels[tag] = gmail_service.users().labels().create(userId='me', body=label).execute()['id']
    gmail_service.users().messages().modify(userId='me', id=message_id, body={'addLabelIds': [labels[x] for x in tags]}).execute()

  def build(self, service, **kwargs):
    return helpers_build(service, self.get_credentials(), **kwargs)
