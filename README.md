# Yadage Workflow Repository

A basic Web API for [Adage](https://github.com/diana-hep/adage.git) workflow templates. Provides access to a repository of templates for the [Yadage UI](https://github.com/diana-hep/yadage-webui).


The **documentation** of the API is located in the folder
```
doc/html
```


## Setup

The Web API uses Flask and is intended to run in a Python virtual environment. Set up the environment using the following commands:

```
cd src/main/py
virtualenv venv
source venv/bin/activate
pip install flask
pip install -U flask-cors
pip install cap-schemas
deactivate
```


## Run

After the virtual environment is set up, the Web API can be run using the following command:

```
cd src/main/py
./server.py
    [-a | --path] <app-path>
    [-d | --debug]
    [-l | --logs] <log-directory>
    [-p | --port] <port-number>
    [-s | --server] <server-url>
    [-w | --workflows] <db-file>

app-path:
	Path on the server under which the app is accessible (Default: /workflow-repository/api/v1)
-d/--debug:
	Switch debug mode on (Default: False)
log-directory:
	Path to directory where log files are stored, only if not running in debug mode (Default: .)
port-number:
	Port at which the app is running (Default: 5005)
server-url:
	URL of the server running the app (Default: http://localhost)
db-file:
	TAB-delimited text file containing information about the workflow templates (Default: ../data/local-workflows.db)
```

When running the Web API with the default command line parameters the application will be available on the local host at URL http://localhost:5005/workflow-repository/api/v1/.


## Workflow Templates

The workflow templates that are accessible via the Web API are specified in the database file (e.g., workflows.db). Each row in the TAB-delimited text file specifies a workflow template. The file has six columns:

```
1) workflow-identifier : Unique qorkflow identifier
2) workflow-name : Human-readable workflow name
3) workflow-description : Workflow description
4) toplevel : cap-schema top level
5) source-file-name : cap-schema source file
6) Optional parameter description (JSON object) : Definition of init parameters when running the workflow
```
