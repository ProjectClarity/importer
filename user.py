from helpers import build as helpers_build
from remote import users
from oauth2client.client import OAuth2Credentials
import json

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
    print self.get('credentials')
    return OAuth2Credentials.from_json(json.dumps(self.get('credentials')))

  def get_history_token(self):
    history_token = self.get('history_token')
    if not history_token:
      gmail_service = self.build('gmail', v='v1')
      threads = gmail_service.users().threads().list(userId='me', maxResults=1).execute()['threads']
      history_token = threads[0]['historyId']
      self.set('history_token', history_token)
    return history_token


  def build(self, service, **kwargs):
    return helpers_build(service, self.get_credentials(), **kwargs)
