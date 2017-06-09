#!venv/bin/python
from flask import Flask, abort, jsonify, make_response
from flask_cors import CORS
import json
import logging
from logging.handlers import RotatingFileHandler
import os
import urllib2
from wftemplate import WorkflowTemplateRepository
import yadageschemas
import yaml
import sys


# ------------------------------------------------------------------------------
#
# Gobal Constants
#
# ------------------------------------------------------------------------------

"""Environment Variable containing path to config file. If not set will try
file config.yaml in working directory.
"""
ENV_CONFIG = 'YADAGEWFREPO_CONFIG'

"""Url of default config file on GitHub."""
WEB_CONFIG_FILE_URI = 'https://raw.githubusercontent.com/heikomuller/yadage-workflow-repository/master/config/config.yaml'


# ------------------------------------------------------------------------------
#
# App Configuration and Initialization
#
# ------------------------------------------------------------------------------

# Read server configuration from file. The file is expected to contain a Json
# object with a single element 'properties' that references a list of
# 'key'-'value' pairs. The expected parameters are:
#
# server.apppath : Application path part of the Url to access the app
# server.url : Base Url of the server where the app is running
# server.port: Port the server is running on
# app.doc : Url to web service documentation
# app.debug: Switch debugging ON/OFF
# db.uri : Path or Uri to Json file containing template information
# db.schema : Path or Uri to Json or YAML file containing schema definition for
#             YADAGE workflows.
# log.dir : Directory for log files
#
# The default configuration is read first from the GitHub repository. Default
# values are overwritten by configurations in local files. First attempts to
# read the file that is specified in the value of the environment variable
# YADAGEWFREPO_CONFIG. If the variable is not set an attempt to read file
# 'config.yaml' in the current working directory is made.
def_conf = yaml.load(urllib2.urlopen(WEB_CONFIG_FILE_URI).read())['properties']
config = {kvp['key'] : kvp['value'] for kvp in def_conf}
LOCAL_CONFIG_FILE = os.getenv(ENV_CONFIG)
obj = None
if not LOCAL_CONFIG_FILE is None and os.path.isfile(LOCAL_CONFIG_FILE):
    with open(LOCAL_CONFIG_FILE, 'r') as f:
        obj = yaml.load(f.read())
elif os.path.isfile('./config.yaml'):
    with open('./config.yaml', 'r') as f:
        obj = yaml.load(f.read())
if not obj is None:
    for kvp in obj['properties']:
        config[kvp['key']] = kvp['value']

# App Url
APP_PATH = config['server.apppath']
SERVER_URL = config['server.url']
if SERVER_URL.endswith('/'):
    SERVER_URL = SERVER_URL[:-1]
SERVER_PORT = config['server.port']
BASE_URL = SERVER_URL
if SERVER_PORT != 80:
    BASE_URL += ':' + str(SERVER_PORT)
BASE_URL += APP_PATH + '/'

# Url to Web Service documentation
DOC_URL = config['app.doc']
# Source handle definition for general YADAGE workflow schema definition
if 'db.schema' in config:
    SCHEMA_DIR = config['db.schema']
else:
    SCHEMA_DIR = yadageschemas.schemadir
# Template listing file or source handle definition
DB_FILE = config['db.uri']
# Directory for log files (if not in debug mode). The entry is optional. If no
# directory is specified log messages will be written to standard output.
if 'log.dir' in config:
    LOG_DIR = config['log.dir']
else:
    LOG_DIR = None

# Flag to switch debugging on/off
DEBUG = config['app.debug']


# ------------------------------------------------------------------------------
# Initilize Flask App
# ------------------------------------------------------------------------------

# Create the app and enable cross-origin resource sharing
template_app = Flask(__name__)
template_app.config['APPLICATION_ROOT'] = APP_PATH
#template_app.config['PORT'] = SERVER_PORT
template_app.config['DEBUG'] = DEBUG
if not LOG_DIR is None:
    template_app.config['LOG_DIR'] = LOG_DIR
CORS(template_app)


# Initialize the workflow repository and load the content from DB_FILE source.
# THE DB_FILE may either point to a file on local disk (type = basestring) or
# is a source handle defintion (type: dict('type':...,'properties':...)).
db = WorkflowTemplateRepository()
try:
    with open(DB_FILE, 'r') as f:
        wf_templates = yaml.load(f.read())['templates']
except IOError as ex:
    obj = yaml.load(urllib2.urlopen(DB_FILE).read())
    wf_templates = obj['templates']
db.load(wf_templates, SCHEMA_DIR)


# ------------------------------------------------------------------------------
#
# API
#
# ------------------------------------------------------------------------------

@template_app.route('/')
def get_welcome():
    """GET - Welcome Message

    Main object for the web service. Contains the service name and a list of
    references (including a reference to the API documentation, which is
    currently a hard coded URL).
    """
    return jsonify({
        'name': 'Workflow Template Server API',
        'links' : [
            {'rel' : 'self', 'href' : BASE_URL},
            {'rel' : 'doc', 'href' : DOC_URL},
            {'rel' : 'templates', 'href' : BASE_URL + 'templates'}
        ]
    })


@template_app.route('/templates')
def get_templates():
    """GET - Template Listing

    Returns a list of (identifier, name, links) for all templates in the
    repository.
    """
    listing = []
    for wf in db.list():
        wf_descriptor = {
            'id' : wf.identifier,
            'name' : wf.name,
            'description' : wf.description,
            'links' : [{
                'rel' : 'self',
                'href' : BASE_URL + 'templates/' + wf.identifier
            }]
        }
        # Add parameters (if present) so we can display entry form without
        # having to load whole workflow template.
        if not wf.parameters is None:
            wf_descriptor['parameters'] = wf.parameters
        listing.append(wf_descriptor)
    return jsonify({'workflows' : listing})


@template_app.route('/templates/<string:template_id>')
def get_template(template_id):
    """GET - Templates

    Returns the workflow template with the given identifier.
    """
    wf = db.get(template_id)
    if not wf is None:
        wf_descriptor = {
            'id' : wf.identifier,
            'name' : wf.name,
            'description' : wf.description,
            'schema' : wf.schema,
            'links' : [
                {
                    'rel' : 'self',
                    'href' : BASE_URL + 'templates/' + wf.identifier
                },
                {
                    'rel' : 'listing',
                    'href' : BASE_URL + 'templates'
                }
            ]
        }
        # Add parameters (if present) so we can display entry form without
        # having to load whole workflow template.
        if not wf.parameters is None:
            wf_descriptor['parameters'] = wf.parameters
        return jsonify(wf_descriptor)
    else:
        abort(404)


# ------------------------------------------------------------------------------
#
# Helper methods
#
# ------------------------------------------------------------------------------

@template_app.errorhandler(404)
def not_found(error):
    """404 JSON response generator."""
    return make_response(jsonify({'error': 'Not found'}), 404)


@template_app.errorhandler(500)
def internal_error(exception):
    """Exception handler that logs exceptions."""
    template_app.logger.error(exception)
    return make_response(jsonify({'error': str(exception)}), 500)


# ------------------------------------------------------------------------------
# MAIN
# ------------------------------------------------------------------------------

if __name__ == '__main__':
    # Relevant documents:
    # http://werkzeug.pocoo.org/docs/middlewares/
    # http://flask.pocoo.org/docs/patterns/appdispatch/
    from werkzeug.serving import run_simple
    from werkzeug.wsgi import DispatcherMiddleware
    # Switch logging on if not in debug mode
    if template_app.debug is False:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        if not LOG_DIR is None:
            file_handler = RotatingFileHandler(os.path.join(LOG_DIR, 'workflow-repository.log'), maxBytes=1024 * 1024 * 100, backupCount=20)
            file_handler.setLevel(logging.ERROR)
            file_handler.setFormatter(formatter)
            template_app.logger.addHandler(file_handler)
    # Load a dummy app at the root URL to give 404 errors.
    # Serve app at APPLICATION_ROOT for localhost development.
    application = DispatcherMiddleware(Flask('dummy_app'), {
        template_app.config['APPLICATION_ROOT']: template_app,
    })
    run_simple('0.0.0.0', SERVER_PORT, application, use_reloader=template_app.debug)
