import threading
import logging
import urllib2
import base64
import simplejson
import os
from datetime import datetime
from urlparse import urlparse
from errbot.botplugin import BotPlugin
from config import BOT_DATA_DIR, CHATROOM_PRESENCE

POLL_INTERVAL = 150

class ReviewBoardBot(BotPlugin):
    t = None
    lock = threading.Lock()
    poll_started = False
    cache_file = os.path.join(BOT_DATA_DIR, 'rbbot.cache')

    min_err_version = '1.3.0' # it needs the configuration feature

    def get_configuration_template(self):
        return {'url' : 'http://machine.domain/api', 'username' : 'yourusername','password' : 'yourpassword' }

    def configure(self, configuration):
        if configuration:
            if type(configuration) != dict:
                raise Exception('Wrong configuration type')

            if not all(key in configuration for key in ('url','username','password')):
                raise Exception('Wrong configuration type, it should contain RB_API_URL, RB_USERNAME and RB_PASSWORD entries')

            if len(configuration) > 3:
                raise Exception('What else did you try to insert in my config ?')
        super(ReviewBoardBot, self).configure(configuration)

    def log(self, msg, _type='info'):
        l = getattr(logging, _type)
        l('%s: %s' % (self.__class__.__name__, msg))

    def start_poll(self):
        self.t = threading.Timer(
            POLL_INTERVAL,
            self.make_request,
            kwargs=self.config
        )
        self.t.setDaemon(True)  # so it is not locking on exit
        self.t.start()

    def cache_data(self, data):
        f = open(self.cache_file, 'w')
        f.write(data)
        f.close()

    def get_cached_data(self):
        if os.path.isfile(self.cache_file):
            f = open(self.cache_file, 'r')
            data = f.read()
            f.close()
            return data
        else:
            return '0\n0'

    def make_request(self, *args, **kwargs):
        self.log('Making API request')
        url = kwargs['url']

        req = urllib2.Request('%s/review-requests/' % url)

        # add the username and password to the header
        base64string = base64.encodestring('%s:%s' % (
            kwargs['username'], kwargs['password']
        ))[:-1]
        authheader = "Basic %s" % base64string
        req.add_header("Authorization", authheader)

        # make the request and convert to python object
        try:
            handle = urllib2.urlopen(req)
            self.handle_request(handle.read())
        except IOError:
            self.log('Error connecting to %s' % url)

    def handle_request(self, result):
        result_object = simplejson.loads(result)
        cached_id, cached_data = self.get_cached_data().split('\n')
        cached_id = int(cached_id)

        # get the latest request, cache and send message
        if 'review_requests' in result_object:
            requests = result_object['review_requests']
            if len(requests) > 0:
                review_request = self.get_latest_review_request(requests)
                current_id = int(review_request['id'])
                self.cache_data('%s\n%s' % (current_id, result))

                if cached_id == 0 or (cached_id != current_id):
                    self.log('Caching review request: %s' % current_id)
                    self.cache_data('%s\n%s' % (current_id, result))
                    self.send_message(review_request)

        self.start_poll()

    def get_latest_review_request(self, requests):
        ordered_reviews = {}
        latest_review = None

        for r in requests:
            # time in 2012-06-12 14:32:34 format
            time_added = datetime.strptime(r['time_added'], '%Y-%m-%d %H:%M:%S')
            ordered_reviews[time_added] = r

        for k in sorted(ordered_reviews, key=ordered_reviews.get):
            latest_review = ordered_reviews[k]
            break

        return latest_review

    def send_message(self, review_request):
        rooms = CHATROOM_PRESENCE

        if rooms:
            _id = review_request['id']
            summary = review_request['summary']
            parsed_url = urlparse(self.config['url'])

            msg = 'Review requested: %s, %s://%s/r/%s' % (
                summary, parsed_url.scheme, parsed_url.netloc, _id
            )
            for room in rooms:
                self.send(room, msg, message_type='groupchat')

    def callback_connect(self):
        self.log('callback_connect')
        if not self.config:
            raise Exception('This plugin needs to be configured')
        if not self.poll_started:
            self.poll_started = True
            self.log('starting polling')
            self.start_poll()
