#!venv/bin/python
from flask import Flask, abort, jsonify, make_response
from flask_cors import CORS
import json
import logging
from logging.handlers import RotatingFileHandler
import os
from util import from_list
from wftemplate import SourceHandle, WorkflowTemplateRepository, TYPE_YAML
import yaml
import sys


# ------------------------------------------------------------------------------
#
# Gobal Constants
#
# ------------------------------------------------------------------------------

"""Environment Variable containing path to confiig file. If not set will try
file config.yaml in working directory.
"""
ENV_CONFIG = 'YADAGEWFREPO_CONFIG'


# ------------------------------------------------------------------------------
#
# App Configuration and Initialization
#
# ------------------------------------------------------------------------------

# Expects a server config file in the local directory. The config file is
# expected to contain values for all server configuration parameter. These
# parameters are:
#
# server.apppath : Application path part of the Url to access the app
# server.url : Base Url of the server where the app is running
# server.port: Port the server is running on
# app.doc : Url to web service documentation
# db.uri : Path or Uri to Json file containing template information
# db.schema : Source handle definition
# log.dir : Directory for log files
#
# The file is expected to contain a Json object with a single element
# 'properties' that references a list of 'key', 'value' pairs. We first try to
# read the config file on local dsk. If this doesn't work try to access a
# default config file that is maintained as part of the GitHub repository
LOCAL_CONFIG_FILE = os.getenv(ENV_CONFIG, './config.yaml')
if os.path.isfile(LOCAL_CONFIG_FILE):
    with open(LOCAL_CONFIG_FILE, 'r') as f:
        obj = yaml.load(f.read())
else:
    WEB_CONFIG_FILE_URI = 'https://raw.githubusercontent.com/heikomuller/yadage-workflow-repository/master/config/config.yaml'
    # Soure handle for default config file on the Web.
    obj = SourceHandle(TYPE_YAML, {'resourceUri': WEB_CONFIG_FILE_URI}).read()
config = from_list(obj['properties'])

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
SCHEMA_SOURCE = SourceHandle.from_json(config['db.schema'])
# Template listing file or source handle definition
DB_FILE = config['db.uri']
# Directory for log files (if not in debug mode). The entry is optional. If no
# directory is specified log messages will be written to standard output.
if 'log.dir' in config:
    LOG_DIR = config['log.dir']
else:
    LOG_DIR = None

# Flag to switch debugging on/off
DEBUG = True


# ------------------------------------------------------------------------------
# Initilize Flask App
# ------------------------------------------------------------------------------

# Create the app and enable cross-origin resource sharing
app = Flask(__name__)
app.config['APPLICATION_ROOT'] = APP_PATH
app.config['DEBUG'] = DEBUG
CORS(app)

# Initialize the workflow repository and load the content from DB_FILE source.
# THE DB_FILE may either point to a file on local disk (type = basestring) or
# is a source handle defintion (type: dict('type':...,'properties':...)).
db = WorkflowTemplateRepository(SCHEMA_SOURCE.read())
if type(DB_FILE) is str:
    with open(DB_FILE, 'r') as f:
        wf_templates = yaml.load(f.read())['templates']
else:
    wf_templates = SourceHandle.from_json(DB_FILE).read()['templates']
db.load(wf_templates)


# ------------------------------------------------------------------------------
#
# API
#
# ------------------------------------------------------------------------------

@app.route('/')
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


@app.route('/templates')
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


@app.route('/templates/<string:template_id>')
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

@app.errorhandler(404)
def not_found(error):
    """404 JSON response generator."""
    return make_response(jsonify({'error': 'Not found'}), 404)


@app.errorhandler(500)
def internal_error(exception):
    """Exception handler that logs exceptions."""
    app.logger.error(exception)
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
    if app.debug is not True:
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        if not LOG_DIR is None:
            file_handler = RotatingFileHandler(os.path.join(LOG_DIR, 'workflow-repository.log'), maxBytes=1024 * 1024 * 100, backupCount=20)
            file_handler.setLevel(logging.ERROR)
            file_handler.setFormatter(formatter)
            app.logger.addHandler(file_handler)
    # Load a dummy app at the root URL to give 404 errors.
    # Serve app at APPLICATION_ROOT for localhost development.
    application = DispatcherMiddleware(Flask('dummy_app'), {
        app.config['APPLICATION_ROOT']: app,
    })
    run_simple('0.0.0.0', SERVER_PORT, application, use_reloader=app.config['DEBUG'])
