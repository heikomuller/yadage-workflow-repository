"""Load and print workflow template schema."""
import json
from yadagetemplates.wftemplate import SourceHandle, TYPE_YAML

RESOURCE_URI = 'https://raw.githubusercontent.com/lukasheinrich/yadage-workflows/master/atlasexamples/fullchainderiv/rootflow.yml'

schema = SourceHandle(TYPE_YAML, {'resourceUri': RESOURCE_URI}).read()

print json.dumps(schema, indent=4)
