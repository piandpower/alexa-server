from flask import Flask, request, render_template, g
from flask_ask import Ask, statement, question, session
# from flask.ext.cache import Cache
from werkzeug.contrib.cache import SimpleCache
from json import dumps
from unreal_socket import UnrealSocket
from random import randint, choice
from werkzeug.serving import WSGIRequestHandler

import requests
import sys
import logging

app = Flask(__name__)

ask = Ask(app, "/")

cache = SimpleCache()
# cache = Cache(app,config={'CACHE_TYPE': 'simple'})
# cache.init_app(app)

# query_list = []

ROOT_URL = 'https://alexa-unreal.herokuapp.com'

app.debug = True
app.threaded = True
logging.getLogger("flask_ask").setLevel(logging.ERROR)

app.sock = None

def p(*args):
  print args[0] % (len(args) > 1 and args[1:] or [])
  sys.stdout.flush()

# Step 1
@app.route('/register', methods=['POST'])
def register_client():
    host = request.json['host']
    port = request.json['port']
    UnrealSocket(host, port)
    app.sock = UnrealSocket.active_socket
    p(str(app.sock))
    return 'ok'
    
# Step 3
@app.route('/alexa', methods=['POST'])
def execute_command():
    command_name = request.json['command']
    p('test')
    p(str(app.sock))
    # Step 4
    if app.sock:
        app.sock.process_command(command_name)
        return 'OK'
    else:
        return 'Nope'

@ask.launch
def new_game():
    welcome_msg = render_template('welcome')
    return question(welcome_msg)

@ask.intent("PressButtonIntent", convert = {'color': str})
def press_button(color):
    if (color == 'red'): res = requests.post(ROOT_URL + '/alexa', data = dumps({'command' : 1}), headers = {'content-type' : 'application/json'})
    elif(color == 'blue'): res = requests.post(ROOT_URL + '/alexa', data = dumps({'command' : 2}), headers = {'content-type' : 'application/json'})
    elif(color == 'green'): res = requests.post(ROOT_URL + '/alexa', data = dumps({'command' : 3}), headers = {'content-type' : 'application/json'})
    elif(color == 'yellow'): res = requests.post(ROOT_URL + '/alexa', data = dumps({'command' : 4}), headers = {'content-type' : 'application/json'})
    button_msg = render_template('press', buttonMsg = color)
    return question(button_msg)

@ask.intent("QuitIntent")
def quit():
    return statement(render_template('quit'))

@ask.intent("QueryWorldIntent")
def query_world():
    p('foo')
    res = requests.post(ROOT_URL + '/alexa', data = dumps({'command' : 0}), headers = 
        {'content-type' : 'application/json', 'Connection': 'Keep-alive'})
    return question(buildQueryList(getQueryList()))

@app.route('/queryResponse', methods=['POST'])
def execute_query():
    cache.set('query_list', request.json['query_list'])
    return 'ok' 

def getQueryList():
    if cache.get('query_list') is not None:
        return cache.get('query_list')
    else:
        p('query list is none')
        return ['nothing yet']

def buildQueryList(query_list):
    query_str = ', '.join(['a ' + x for x in query_list][:-1]) + ', and a ' + query_list[-1]
    return render_template('locate', queryStr = query_str)

@ask.intent("LocationIntent")
def locate_surounding():
    res = requests.post(ROOT_URL + '/alexa', data = dumps({'command' : 0}), headers = {'content-type' : 'application/json'})
    return question(buildQueryList(getQueryList()))

@ask.intent("NameIntent")
def about_self():
    about_str = choice(
            ['You know who I am. I am Em. Stuck here in the world of despair, longing for you. Please come save me', 
            'What\'s wrong? Do you not think its me? IT IS I, Em' , 
            'What do you mean? I am your wife Em',
            'You tell me. What do you think?']
    )
    return question(render_template('about', aboutStr = about_str))

def shutdown_server():
    func = request.environ.get('werkzeug.server.shutdown')
    if func is None:
        raise RuntimeError('Not running with the Werkzeug Server')
    func()

@app.route('/shutdown', methods=['POST'])
def shutdown():
    shutdown_server()
    UnrealSocket.cleanup()
    return 'Server shutting down...'

if __name__ == '__main__':
    WSGIRequestHandler.protocol_version = "HTTP/1.1"
    app.run(debug=True, threaded=True)
