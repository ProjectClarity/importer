from remote import *

def send_to_queue(d):
  message = JSONMessage()
  message.update(d)
  importer_queue.write(message)

def get_messages(n):
  return importer_queue.get_messages(num_messages=n, wait_time_seconds=20)

def delete_message(m):
  importer_queue.delete_message(m)

def delete_messages(l):
  importer_queue.delete_message_batch(l)

def process_messages(l, f):
  for m in l:
    f(m)
    delete_message(m)
