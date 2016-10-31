#!venv/bin/python
from flask import Flask, abort, jsonify, make_response
from flask_cors import CORS
import capschemas
import getopt
import json
import os
import sys


# -----------------------------------------------------------------------------
# App Configuration
# -----------------------------------------------------------------------------

# Server URL
SERVER_URL = 'http://localhost'
PORT = 5005
APP_PATH = '/workflow-repository/api/v1'

# Template listing file
DB_FILE = './workflows.db'


# ------------------------------------------------------------------------------
# Parse command line arguments
# ------------------------------------------------------------------------------
if __name__ == '__main__':
    command_line = 'Usage: [-a | --path <app-path>] [-d | --db <db-file>] [-p | --port <port-number>] [-s | --server <server-url>]'
    try:
        opts, args = getopt.getopt(sys.argv[1:], 'a:d:p:s:', 'db=,path=,port=0,server=')
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
        elif opt in ('-d', '--db'):
            DB_FILE = param
        elif opt in ('-p', '--port'):
            try:
                PORT = int(param)
            except ValueError:
                print 'Invalid port number: ' + param
                sys.exit()
        elif opt in ('-s', '--server'):
            SERVER_URL = param

    if not os.access(DB_FILE, os.F_OK):
        print 'File not found: ' + DB_FILE
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
CORS(app)


# ------------------------------------------------------------------------------
# Initialize repository of workflow templates. Expects a tab-delimited file
# with six columns (last column is optional):
#
# 1) workflow-identifier
# 2) workflow-name
# 3) workflow-description
# 4) toplevel
# 5) source-file-name
# 6) Optional parameter description (JSON object)
# ------------------------------------------------------------------------------
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
# API Call Handlers
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# GET: Welcome Message
#
# Main object for the web service. Contains the service name and a list of
# references (including a reference to the API documentation, which is currently
# a hard coded URL).
# ------------------------------------------------------------------------------
@app.route('/')
def get_welcome():

    return jsonify({
        'name': 'Workflow Template Server API',
        'links' : [
            {'rel' : 'self', 'href' : BASE_URL},
            {'rel' : 'doc', 'href' : 'http://cds-swg1.cims.nyu.edu/workflow-repository/api/v1/doc/index.html'},
            {'rel' : 'templates', 'href' : BASE_URL + 'templates'}
        ]
    })
# ------------------------------------------------------------------------------
# GET: Template Listing
#
# Returns a list of (identifier, name, links) for all templates i the repository
# ------------------------------------------------------------------------------
@app.route('/templates')
def get_templates():
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


# ------------------------------------------------------------------------------
# GET: Templates
#
# Returns the workflow template with the given identifier
# ------------------------------------------------------------------------------
@app.route('/templates/<string:template_id>')
def get_template(template_id):
    if template_id in db:
        return jsonify(db[template_id])
    else:
        abort(404)


# ------------------------------------------------------------------------------
# 404 JSON response generator
# ------------------------------------------------------------------------------
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)


if __name__ == '__main__':
    # Relevant documents:
    # http://werkzeug.pocoo.org/docs/middlewares/
    # http://flask.pocoo.org/docs/patterns/appdispatch/
    from werkzeug.serving import run_simple
    from werkzeug.wsgi import DispatcherMiddleware
    app.config['DEBUG'] = True
    # Load a dummy app at the root URL to give 404 errors.
    # Serve app at APPLICATION_ROOT for localhost development.
    application = DispatcherMiddleware(Flask('dummy_app'), {
        app.config['APPLICATION_ROOT']: app,
    })
    run_simple('0.0.0.0', PORT, application, use_reloader=True)
