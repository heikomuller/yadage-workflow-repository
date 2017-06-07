from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

#sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from yadagetemplates.server import app  # noqa

# Switch logging on if not in debug mode
if app.debug is False:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    if not app.config['LOG_DIR'] is None:
        file_handler = RotatingFileHandler(
            os.path.join(app.config['LOG_DIR'], 'workflow-repository.log'),
            maxBytes=1024 * 1024 * 100,
            backupCount=20
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)
# Load a dummy app at the root URL to give 404 errors.
# Serve app at APPLICATION_ROOT for localhost development.
application = DispatcherMiddleware(Flask('dummy_app'), {
    app.config['APPLICATION_ROOT']: app,
})
run_simple('0.0.0.0', app.config['PORT'], application, use_reloader=app.debug)
