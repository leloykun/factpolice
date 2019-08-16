import sys
import json
import time
from datetime import date
from datetime import datetime
import random

import requests
from flask import Flask, request

import urllib2
import re

app = Flask(__name__)

PAT = 'EAAKX1wT768cBAGuUOywrR3Fh4kZBZBVw6Qa0jTIHXB8Bt8KbhbPNZCEMwwQo8QjmtAGSqy4DE2B4AZBmu1sk23RuTHZAHMgiMyDvWUcdRadxQcLYFnqNo7mQXcYLl4t6ZCwgiyCuLnPW40cZBbhPvcqdVtfr7xSeLbELUe44y9dpj1hcrhus889'
VERIFY_TOKEN = 'FactBot'

REGULARITY_THRESHOLD = 0.8
WARNING_MSG = "WARNING: the text is highly regular. It was most likely written by a bot. Stay vigilant."
NON_WARNING_MSG = "The text was likely written by a human. But stay vigilant still tho."

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200

def is_url(url):
    try:
        if not urllib2.urlparse.urlparse(url).netloc:
            return False

        website = urllib2.urlopen(url)
        if website.code != 200 :
            return False
    except Exception, e:
        print("Errored while attempting to validate link : ", url)
        print(e)
        return False
    return True

def extract_content(url):
    return url

def calc_regularity(text):
    data = {'project':'gpt-2-small',
            'text':text}
    res = requests.post('http://34.66.208.239:8081/analyze_text', json=data)
    print(res.json())
    return res.json()['regularity']

@app.route('/', methods=['POST'])
def webhook():
    # endpoint for processing incoming messaging events
    data = request.get_json()

    display_greeting()

    if data["object"] == "page":
        for entry in data["entry"]:
            print(entry)
            for messaging_event in entry["messaging"]:
                sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                display_action(sender_id, "mark_seen")
                display_action(sender_id, "typing_on")
                #time.sleep(0.5)

                if messaging_event.get("message"):  # someone sent us a message

                    message_text = messaging_event["message"]["text"]  # the message's text

                    if is_url(message_text):
                        message_text = extract_content(message_text)
                        send_message(sender_id, "url content:")
                        send_message(sender_id, message_text)

                    send_message(sender_id, "analyzing...")
                    regularity = calc_regularity(message_text)

                    if regularity >= REGULARITY_THRESHOLD:
                        send_message(sender_id, WARNING_MSG)
                    else:
                        send_message(sender_id, NON_WARNING_MSG)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                #if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                #    payload = messaging_event["postback"]["payload"]
                #    print(payload)
                #    send_message(sender_id, payload)

                display_action(sender_id, "typing_off")

    return "ok", 200

def send_message(recipient_id, message_text):
    params = {
        "access_token": PAT
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

def display_action(recipient_id, action):
    params = {
        "access_token": PAT
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "sender_action": action
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)

def display_greeting():
    params = {
        "access_token": PAT
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "get_started": {
            "payload": "get_started"
        },
        "greeting": [{
            "locale":"default",
            "text":"Hello, {{user_first_name}}!"
        }]
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messenger_profile", params=params, headers=headers, data=data)

if __name__ == '__main__':
    app.run()
