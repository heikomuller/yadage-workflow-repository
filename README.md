# Yadage Workflow Repository

A basic Web API for [Adage](https://github.com/diana-hep/adage.git) workflow
templates. Provides access to a repository of templates for the [Yadage UI](https://github.com/diana-hep/yadage-webui).


The **source code** for the Web API server is located at:
```
src/main/py
```

There is also a **documentation** of the API in the static folder
```
static\api\v1\doc
```

## Setup

The Web API uses Flask and is intended to run using a Python virtual environment.
Set up the environment using the following commands:

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

After the virtual environment is set up, the Web API can be run using the following
command:

```
cd src/main/py
./server.py [-a | --path <app-path>] [-d | --db <db-file>] [-p | --port <port-number>] [-s | --server <server-url>]

app-path: Path on the server under which the app is accessible (Default: /workflow-repository/api/v1)
db-file: TAB-delimited text file containing information about the workflow templates (Default: ./workflows.db)
port-number: Port at which the app is running (Default: 5005)
server-url: URL of the server running the app (Default: http://localhost)
```

When running the Web API with the default command line parameters the application will
be available on the local host at URL ```http://localhost:5005/workflow-repository/api/v1/```.


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
