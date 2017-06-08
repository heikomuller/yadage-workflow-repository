# Yadage Workflow Repository

A basic Web API for [Adage](https://github.com/diana-hep/adage.git) workflow templates. Provides access to a repository of templates for the [Yadage UI](https://github.com/diana-hep/yadage-webui).


The **documentation** of the API is located in
```
doc/html
```


## Setup

Below is a simple example to setup the workflow repository server after cloning the GihHub repository. The example uses a Python virtual environment:

```
virtualenv venv
source venv/bin/activate
pip install -e .
```


## Run

The workflow repository API is implemented as a Flask application. To start the API use the following command:

```
python yadagewfrepo
```


## Configuration

The API is configured using a configuration file. Configuration files are in YAML format. The default configuration file is `config/config.yaml`. At startup, the workflow repository server first tries to load the configuration file that is specified in the environment variable **YADAGEWFREPO_CONFIG**. If the variable is not set or the file does not exists the server tries to access file `config.yaml` in the working directory. If no configuration file is found the default file from the GitHub repository is used.

Below is the content of the default configuration file:

```
properties:
    - key: 'server.apppath'
      value : '/workflow-repository/api/v1'
    - key: server.url
      value : 'http://localhost'
    - key: 'server.port'
      value: 5000
    - key: 'app.doc'
      value: 'http://cds-swg1.cims.nyu.edu/workflow-repository/api/v1/doc/index.html'
    - key: ''app.debug'
      value: false
    - key: 'db.uri'
      value:
          type: 'YAML'
          properties:
              resourceUri: 'https://raw.githubusercontent.com/heikomuller/yadage-workflow-repository/master/config/yadage-workflows.yaml'
    - key: 'db.schema'
      value: 'https://raw.githubusercontent.com/diana-hep/yadage-schemas/master/yadageschemas/yadage/workflow-schema.json'
```

Entries in the configuration file are (key,value)-pairs. The following are valid keys:

- **server.url**: Url of the web server where the API is running. Used as prefix to generate Url's for API resources.
- **server.port**: Port on the server where Flask runs on.
- **server.app**: Path of the Flask application that runs the API. The combination of *server.url*, *server.port*, and *server.app* is expected the root Url for the API.
- **app.doc**: Url to the Html file containing the API documentation.
- **app.debug**: Switch debugging ON/OFF.
- **db.uri**: Path or Uri to Json or YAML file containing template information
- **db.schema**: Path or Uri to Json or YAML file containing schema definition for YADAGE workflows.
- **log.dir**: Path to directory for log files (optional).


## Workflow Templates

The workflow templates that are accessible via the Web API are specified in the database file (**db.uri**). The default listing of workflow templates is in 'config/yadage-workflows.yaml'. An example from the file is shown below

```
templates:
    - identifier: 'lhcoanalysis'
      name: 'LHC Analysis'
      description: 'Large Hadron Collider Analysis'
      parameters:
          - name: 'nevents'
            type: 'int'
            label: 'Number of Events'
            default: 100
      schema:
        source: 'from-github/phenochain'
        identifier: 'lhcoanalysis.yml'
    - identifier: 'madgraph_delphes'
      name: 'Madgraph Delphes'
      description: 'Generate collision events with MadGraph5_aMC@NLO and shower, hadronize, and simulate the response of a detector like CMS with Delphes and Pythia'
      parameters:
          - name: 'nevents'
            type: 'int'
            label: 'Number of Events'
            default: 100
      schema:
        source: 'from-github/phenochain'
        identifier: 'madgraph_delphes.yml'
```
Each entry has to have a unique **identifier**. The **name** and **description** are primarily intended for the Web GUI that displays a list of the availabe workflow templates for the user. The **schema** is expected to be a source-identifier pair that is interpretable by the [Yadage workflow loader](https://github.com/diana-hep/yadage/blob/master/yadage/workflow_loader.py).


## Docker

The workflow template API is available as a docker image on Docker Hub:

```
docker pull heikomueller/yadage-workflow-repository
```

The command to run the docker image with the default configuration is:

```
docker run -d -p 25012:25012 yadage-workflow-repository
```

If you want to use a custom configuration you can use the follwoing command:

```
docker run -d -p 5000:5000 -e YADAGEWFREPO_CONFIG="/config/config.yaml" -v /home/user/workflow-repository/config:/config heikomueller/yadage-workflow-repository
```
The command assumes a local config file `/home/user/workflow-repository/config/config.yaml` is used and that the **server.port** is set to 5000.
