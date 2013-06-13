import logging
import datetime

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db
import oauth2 as oauth
import simplejson as json

import secrets
import pocketaccountant


class DirectMessage(db.Model):
    text = db.StringProperty()
    id = db.StringProperty()
    date = db.DateTimeProperty()

    @classmethod
    def last_DM_ID(self):
        last_DM = DirectMessage.all().order('-date').get()
        return last_DM.id

    @staticmethod
    def make_datetime(idatetime):
        return datetime.datetime.strptime(string.join(idatetime.split(
            ' +0000 ')), '%a %b %d %H:%M:%S %Y')

    @staticmethod
    def parse(DMtext):
        if len(DMtext.split(',')) == 1:
            return DMtext.split(' ', 1)
        else:
            return DMtext.split(',')


class TwitterPull(webapp.RequestHandler):
    def get(self):
        consumer = oauth.Consumer(key='A0YdjSUGSwKPfEEF1ThQ',
            secret=secrets.consumer)
        token = oauth.Token(
            key='371653560-dLklDiFqg8hMKOsskiF0MDmdCLOrwKhwH08vyq0E',
            secret=secrets.access)
        client = oauth.Client(consumer, token)
        url = ('http://api.twitter.com/1.1/direct_messages'
            '.json?since_id='+DirectMessage.last_DM_ID())
        resp, content = client.request(
            url,
            method="GET",
            body=None,
            headers=None,
            force_auth_header=True
        )
        jsoncontent = json.loads(content)
        if not jsoncontent:
            logging.info("No new DMs")
        else:
            i = len(jsoncontent) - 1
            while i >= 0:
                newDM = DirectMessage()
                newDM.id = jsoncontent[i]['id_str']
                newDM.text = jsoncontent[i]['text']
                newDM.date = pocketaccountant.correct_for_dst(
                    DirectMessage.make_datetime(
                    jsoncontent[i]['created_at']))
                i -= 1
                db.put(newDM)

                DMtext = DirectMessage.parse(jsoncontent[i]['text'])
                spending = pocketaccountant.Logged_spending()
                spending.amount = pocketaccountant.InputForm.money_int(
                    DMtext[0])
                spending.descrip = DMtext[1]
                spending.date = pocketaccountant.correct_for_dst(
                    DirectMessage.make_datetime(
                    jsoncontent[i]['created_at']))
                db.put(spending)

application = webapp.WSGIApplication([('/twitterpull', TwitterPull)],
                                     debug=True)


def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
