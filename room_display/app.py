import json
import logging
import os
import sys
from datetime import datetime

import flask
from flask import Flask, jsonify, abort, request
from flask_heroku import Heroku
from flask_script import Manager
from flask_script import Server


##################################################
#                    Setup
##################################################

# Logging
logging.basicConfig(format='%(levelname)s :: %(asctime)s :: %(name)s :: %(message)s', level=logging.DEBUG)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('pyexchange').setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.debug = True
heroku = Heroku(app)

_instabook_times = os.environ.get('INSTABOOK_TIMES', None)
_allowed_ips = os.environ.get('ALLOWED_IPS', None)

config = {
    # Misc settings
    'host': os.environ.get('HOST', '0.0.0.0'),
    'port': int(os.environ.get('PORT', 5000)),
    'demo_mode': os.environ.get('DEMO_MODE', None),

    # Exchange settings
    'domain': os.environ.get('OUTLOOK_DOMAIN', None),
    'ews_url': os.environ.get('OUTLOOK_EWS_URL', None),  # EWS = Exchange Web Services
    'username': os.environ.get('OUTLOOK_USERNAME', None),
    'password': os.environ.get('OUTLOOK_PASSWORD', None),
    'room_dict': os.environ.get('OUTLOOK_ROOM_DICT', None),
    'room_search_term': os.environ.get('OUTLOOK_ROOM_SEARCH_TERM', None),
    'refresh_time_seconds': os.environ.get('OUTLOOK_REFRESH_TIME', 60),
    'timezone_name': os.environ.get('OUTLOOK_TIMEZONE_NAME', 'Europe/London'),

    # Security settings
    'allowed_ips': [
        ip.strip()
        for ip in _allowed_ips.split(',')
        if ip
    ] if _allowed_ips is not None else [],

    # Frontend settings
    'poll_interval': os.environ.get('POLL_INTERVAL', 1),
    'poll_start_minute': os.environ.get('POLL_START_MINUTE', 420),
    'poll_end_minute': os.environ.get('POLL_END_MINUTE', 1140),

    # InstaBook settings
    'instabook_times': [
        int(ib_time.strip())
        for ib_time in _instabook_times.split(',')
        if ib_time
    ] if _instabook_times is not None else [15, 30],
}

DEMO_MODE = False
if config['demo_mode'] and config['demo_mode'].lower() == 'true':
    DEMO_MODE = True
if not config['domain']:
    DEMO_MODE = True

ROOM_DISPLAY_SERVICE = None
if DEMO_MODE:
    logger.debug('Using demo backend...')
    from service.room_display_demo import RoomDisplayDemo
    ROOM_DISPLAY_SERVICE = RoomDisplayDemo()
else:
    logger.debug('Using Exchange backend...')
    from service.room_display_exchange import RoomDisplayExchange
    ROOM_DISPLAY_SERVICE = RoomDisplayExchange(
        config['domain'],
        config['ews_url'],
        config['username'],
        config['password'],
        config['room_dict'],
        config['room_search_term'],
        config['refresh_time_seconds'],
        config['timezone_name'],
    )


##################################################
#                    Serving
##################################################

@app.before_request
def restrict_access():
    client_address = request.headers.get('X-Forwarded-For', request.remote_addr)
    if config['allowed_ips'] and client_address not in config['allowed_ips']:
        sys.stderr.write('Insecure access blocked from {ip}!\n'.format(ip=client_address))
        abort(403)


@app.route('/')
def index():
    return flask.send_file('./templates/index.html')


@app.route('/data')
def data():
    # Get booking info from the room display service
    data = {
        'now': datetime.now().isoformat(),
        'polling': {
            'interval': config['poll_interval'],
            'start_minute': config['poll_start_minute'],
            'end_minute': config['poll_end_minute'],
        },
        'instabook_times': config['instabook_times'],
        'rooms': ROOM_DISPLAY_SERVICE.get_room_data()
    }
    return jsonify(data)


@app.route('/instabook', methods=['POST'])
def instabook():
    # Extract POST data
    post_data = request.get_json()
    room_id = post_data['room_id']
    length = post_data['length']

    # Check the length is a valid one
    # TODO

    # Add a new booking
    result = ROOM_DISPLAY_SERVICE.add_booking(room_id, length)

    return jsonify(result)


##################################################
#                    Main
##################################################

manager = Manager(app)

# Bind the dev server to 0.0.0.0 so it works through Docker
#manager.add_command('runserver', Server(host='0.0.0.0'))

@manager.command
def runserver():
    """
    Run the server
    """
    # Go go go
    print(
        'Running on port {HOST}:{PORT}'.format(
            HOST=config['host'],
            PORT=config['port']
        )
    )
    app.run(host=config['host'], port=config['port'])

@manager.command
def production():
    """
    Run the server in production mode
    """
    # Turn off debug on live...
    app.debug = False

    runserver()


if __name__ == '__main__':
    manager.run()
