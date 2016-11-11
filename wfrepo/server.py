#!venv/bin/python
from flask import Flask, abort, jsonify, make_response
from flask_cors import CORS
import capschemas
import getopt
import json
import os
import sys


# ------------------------------------------------------------------------------
#
# App Configuration and Initialization
#
# ------------------------------------------------------------------------------

# Server URL
SERVER_URL = 'http://localhost'
PORT = 5005
APP_PATH = '/workflow-repository/api/v1'
# Start app in debug mode
DEBUG = False
# Template listing file
DB_FILE = '../data/local-workflows.db'
# Directory for log files (if not in debug mode)
LOG_DIR = '.'


# ------------------------------------------------------------------------------
# Parse command line arguments
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    command_line = """
    Usage:
    [-a | --path] <app-path>
    [-d | --debug]
    [-l | --logs] <log-directory>
    [-p | --port] <port-number>
    [-s | --server] <server-url>
    [-w | --workflows] <db-file>
    """
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:dl:p:s:w:', 'debug,logs=,path=,port=0,server=,workflows=')
    except getopt.GetoptError:
        print command_line
        sys.exit()

    if len(args) != 0:
        print command_line
        sys.exit()

    for opt, param in opts:
        if opt in ('-a', '--path'):
            APP_PATH = param
            if not APP_PATH.startswith('/'):
                print 'Invalid application path: ' + APP_PATH
                sys.exit()
            if APP_PATH.endswith('/'):
                APP_PATH = APP_PATH[:-1]
        elif opt in ('-d', '--debug'):
            DEBUG = True
        elif opt in ('-l', '--logs'):
            LOG_DIR = param
        elif opt in ('-p', '--port'):
            try:
                PORT = int(param)
            except ValueError:
                print 'Invalid port number: ' + param
                sys.exit()
        elif opt in ('-s', '--server'):
            SERVER_URL = param
        elif opt in ('-w', '--workflows'):
            DB_FILE = param

    if not os.access(DB_FILE, os.F_OK):
        print 'File not found: ' + DB_FILE
        sys.exit()

# Make sure that the log directory exists (only if not in debug mode)
if not DEBUG:
    if not os.access(LOG_DIR, os.F_OK):
        print 'Directory not found: ' + LOG_DIR
        sys.exit()

# ------------------------------------------------------------------------------
# Initilize Flask App
# ------------------------------------------------------------------------------

# Base URL used as prefix for all HATEOAS URL's
if PORT != 80:
    BASE_URL = SERVER_URL + ':' + str(PORT) + APP_PATH + '/'
else:
    BASE_URL = SERVER_URL + APP_PATH + '/'

print 'Running at ' + BASE_URL

# Create the app and enable cross-origin resource sharing
app = Flask(__name__)
app.config['APPLICATION_ROOT'] = APP_PATH
app.config['DEBUG'] = DEBUG
CORS(app)


# Initialize repository of workflow templates. Expects a tab-delimited file
# with six columns (last column is optional):
#
# 1) workflow-identifier
# 2) workflow-name
# 3) workflow-description
# 4) toplevel
# 5) source-file-name
# 6) Optional parameter description (JSON object)
db = {}
with open(DB_FILE, 'r') as cap_templates:
    line_no = 0
    for line in cap_templates:
        line_no += 1
        if not line.startswith('#'):
            if line.strip() == '':
                continue
            columns = line.strip().split('\t')
            if len(columns) < 5 or len(columns) > 6:
                print 'Invalid input:'
                print str(line_no) + ': ' + line.strip()
                sys.exit()
            wf_id = columns[0]
            wf_name = columns[1]
            wf_description = columns[2]
            toplevel = columns[3]
            source = columns[4]
            wf = capschemas.load(source, toplevel, 'yadage/workflow-schema', None, True)
            wf['id'] = wf_id
            wf['name'] = wf_name
            wf['description'] = wf_description
            if len(columns) == 6:
                wf['parameters'] = json.loads(columns[5])
            # HATEOS: Add self link to the template
            wf['links'] = [{'rel' : 'self', 'href' : BASE_URL + 'templates/' + wf_id}]
            db[wf_id] = wf


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
            {'rel' : 'doc', 'href' : 'http://cds-swg1.cims.nyu.edu/workflow-repository/api/v1/doc/index.html'},
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
    for wf_id in db:
        wf = db[wf_id]
        wf_descriptor = {
            'id' : wf_id,
            'name' : wf['name'],
            'description' : wf['description'],
            'links' : wf['links']
        }
        # Add parameters (if present) so we can display entry form without
        # having to load whole workflow template.
        if 'parameters' in wf:
            wf_descriptor['parameters'] = wf['parameters']
        listing.append(wf_descriptor)
    return jsonify({'workflows' : listing})

@app.route('/templates/<string:template_id>')
def get_template(template_id):
    """GET - Templates

    Returns the workflow template with the given identifier.
    """
    if template_id in db:
        return jsonify(db[template_id])
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
        import logging
        from logging.handlers import RotatingFileHandler
        file_handler = RotatingFileHandler(os.path.join(LOG_DIR, 'workflow-repository.log'), maxBytes=1024 * 1024 * 100, backupCount=20)
        file_handler.setLevel(logging.ERROR)
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
    # Load a dummy app at the root URL to give 404 errors.
    # Serve app at APPLICATION_ROOT for localhost development.
    application = DispatcherMiddleware(Flask('dummy_app'), {
        app.config['APPLICATION_ROOT']: app,
    })
    run_simple('0.0.0.0', PORT, application, use_reloader=app.config['DEBUG'])
