import sys
import json
import time
from datetime import date
from datetime import datetime
import random

import requests
from flask import Flask, request

app = Flask(__name__)

PAT = 'EAAKX1wT768cBAA85ZBYj7aBF8QQqSI3k4libNqQNHRye9eimTfZC3bZAkvhKYmP9P59tgkbFRgIwYEvehFCFJOrpMcsbYJ0vhAzxkUjDAko1O67jvsJ2vbs1x4o0icPaPbpxKMeiHNYfyNUGC1ZB54NJaTUqSgBts9RGKOEma5HiXCYK96X5'
VERIFY_TOKEN = 'FactBot'

REGULARITY_THRESHOLD = 0.8
WARNING_MSG = "RED FLAG: the text is highly regular. It was most likely written by a bot. Stay vigilant."
NON_WARNING_MSG = "The text was likely written by a human. But stay vigilant tho."

BLACKLISTED_MSG = "RED FLAG: this website has been flagged as a fake news site. Be skeptical of its contents."

SITE_SUFFIXES = ['.com', '.org', '.net', '.html', '.press', '.info']

FAKE_NEWS_SITES = ['24sevendailynews', 'akoy-pilipino', 'aljazeeranews-tv',
                   'allthingspinoy', 'angatpilipino', 'asensopinoy',
                   'asianpolicy', 'astigtayopinoy', 'balitangpinoy',
                   'balitangtotoo', 'balitaonline', 'breaking-bbc',
                   'breezynetwork', 'casterph', 'citizenexpress',
                   'classifiedtrends', 'cnn-channel', 'dailyartikulo',
                   'dailyfilipinews', 'dailyfilipino', 'dailyinsights',
                   'dailyviralhub', 'dakila', 'dakilanglahi', 'dds-tambayan',
                   'ddsfiles', 'definitelyfilipino', 'balita', 'buzz', 'buzz',
                   'du30community', 'du30express', 'du30gov', 'du30newsblog',
                   'du30newsinfo', 'du30today', 'Todaydu30today',
                   'Maharlikadugongmaharlika', 'Dutertardsdutertards',
                   'Defenderdutertedefender', 'Dutertedutertedefender',
                   'dutertefederal', 'dutertenews', 'du30news', 'du30news',
                   'dutertenewswatch', 'du3onews', 'dutertepilipinas',
                   'dutertetrendingnews', 'dutrending', 'extremereaders',
                   'filipinews', 'filipinews', 'filipinewsph', 'fullnewsph',
                   'globalnews', 'gma-tv', 'goforwin', 'goodnewsnetworkph',
                   'goodnewstoday', 'gossipdiary', 'grpshorts', 'hotnewsphil',
                   'ilikeyouquotes', 'internationallatestupdates', 'jazznews',
                   'kabalitaka', 'kalyepinoy', 'kantonewsph', 'kantonewsph',
                   'latestnewz', 'makibalita', 'mediacurious', 'mediaph',
                   'mindanation', 'my-prosper', 'mynewstv', 'nagbabagangbalita',
                   'napankamkumametbeewan', 'netcitizen', 'newsbite',
                   'newscenterph', 'newsglobal', 'newsinfolearn', 'newsmediaph',
                   'newstitans', 'newstv', 'newzflash', 'onelinebalita',
                   'philnewscourier', 'phppoliticsnews', 'pinasnewsportal',
                   'pinoyfreedomwall', 'pinoyhopes', 'pinoynews',
                   'pinoynewsblogger', 'pinoypolitics', 'pinoyspeak',
                   'pinoythinking', 'pinoytrending', 'pinoytrendingnews',
                   'pinoytrendingnewsph', 'pinoytrending', 'pinoyviralissues',
                   'pinoyworld', 'publictrending', 'publictrending',
                   'pinoytrending', 'qwazk', 'socialcastph', 'sowhatsnews',
                   'tahonews', 'tartey', 'tatakdu30', 'thedailysentry',
                   'thenewsfeeder', 'thevolatilian', 'thinkervlog',
                   'thinkingpinoy', 'thinkingpinoynews', 'tnp',
                   'trendingnewsportal', 'trendingnewsportal',
                   'trendingnewsportal', 'trendingnewsportal',
                   'trendingnewsportal-ph', 'tnp', 'todayinmanila',
                   'todaysbroadcast', 'todaystopnews', 'trendingbalita',
                   'trendingnewsvideo', 'trendingtopics', 'trendingviral',
                   'tv-cnn', 'unanghirit', 'update', 'updatetayo', 'verifiedph',
                   'viralportal', 'worldstrends', '360news', 'dyaryo',
                   'iampilipino', 'leaknewsph', 'maharlikanews',
                   'maharlikanews', 'newsfeedsociety', 'philnewsportal',
                   'pilipinasonlineupdates', 'socialnewsph', 'xolxol',
                   'adobochronicles']

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == VERIFY_TOKEN:
            print("FAILED VERIFICATION")
            return "Verification token mismatch", 403
        print("SUCCESSFUL VERIFICATION")
        return request.args["hub.challenge"], 200
    print("SUCCESSFUL VERIFICATION")
    return "Hello world", 200

def calc_regularity(text):
    data = {'project':'gpt-2-small',
            'text':text}
    res = requests.post('http://34.66.208.239:8081/analyze_text', json=data)
    print(res.json())
    return res.json()['regularity']

def extract_content(url):
    data = {'url':url}
    try:
        res = requests.post('http://34.66.208.239:8081/get_article_contents', json=data, timeout=20)
        print(res.json()['content'])
        return res.json()['content']
    except:
        print("timeout", url)
        return url
    # return res.json()['content']
    return url

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

                    send_message(sender_id, "analyzing, please wait...")

                    content_text = message_text
                    print(content_text)

                    # if is_url(message_text):
                    #    send_message(sender_id, "url content:")
                    #    message_text = extract_content(message_text)
                    #    send_message(sender_id, message_text)

                    is_site = False
                    is_blacklisted = False

                    # TODO: make more general
                    for marker in SITE_SUFFIXES:
                        if marker in message_text:
                            is_site = True
                            content_text = extract_content(message_text)
                            send_message(sender_id, content_text)

                            for fake_news_domain in FAKE_NEWS_SITES:
                                if fake_news_domain in message_text:
                                    is_blacklisted = True
                                    break
                            break

                    regularity = calc_regularity(content_text)

                    if regularity >= REGULARITY_THRESHOLD:
                        send_message(sender_id, WARNING_MSG)
                    else:
                        send_message(sender_id, NON_WARNING_MSG)

                    if is_blacklisted:
                        send_message(sender_id, BLACKLISTED_MSG)

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
