from flask import Flask
import logging
from logging.handlers import RotatingFileHandler
import os
from werkzeug.serving import run_simple
from werkzeug.wsgi import DispatcherMiddleware

#sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from yadagetemplates.server import template_app, SERVER_PORT  # noqa

# Switch logging on if not in debug mode
if template_app.debug is False:
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    if 'LOG_DIR' in template_app.config:
        file_handler = RotatingFileHandler(
            os.path.join(template_app.config['LOG_DIR'], 'workflow-repository.log'),
            maxBytes=1024 * 1024 * 100,
            backupCount=20
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        template_app.logger.addHandler(file_handler)
# Load a dummy app at the root URL to give 404 errors.
# Serve app at APPLICATION_ROOT for localhost development.
application = DispatcherMiddleware(Flask('dummy_app'), {
    template_app.config['APPLICATION_ROOT']: template_app,
})
run_simple('0.0.0.0', SERVER_PORT, application, use_reloader=template_app.debug)
