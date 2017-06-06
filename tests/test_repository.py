import yaml
import unittest

from yadagetemplates.wftemplate import SourceHandle, WorkflowTemplateRepository
from yadagetemplates.wftemplate import TYPE_JSON, TYPE_YAML

CONFIG_FILE = '../config/yadage-workflows.yaml'
YAML_GITHUB_RESOURCE = 'https://raw.githubusercontent.com/lukasheinrich/yadage-workflows/master/phenochain/madgraph_delphes.yml'
SCHEMA_URI = 'https://raw.githubusercontent.com/diana-hep/yadage-schemas/master/yadageschemas/yadage/workflow-schema.json'


class TestWorkflowRepositoryReader(unittest.TestCase):

    def setUp(self):
        """Read the default YADAGE workflow schema defintiion and initialize an
        empty repository.
        """
        schema = SourceHandle(TYPE_JSON, {'resourceUri': SCHEMA_URI}).read()
        self.db = WorkflowTemplateRepository(schema)

    def test_duplicate_workflow_id(self):
        """Create workflow template repository from object that contains two
        workflows with identical id's. Ensure that a ValueError is thrown in
        this case.
        """
        with self.assertRaises(ValueError):
            self.db.load([
                {
                    'identifier' : 'ID1',
                    'name' : 'NAME1',
                    'description' :'',
                    'schema' : {
                        'type' : 'YAML',
                        'properties' : {
                            'resourceUri' : YAML_GITHUB_RESOURCE
                        }
                    },
                },
                {
                    'identifier' : 'ID1',
                    'name' : 'NAME1',
                    'description' :'',
                    'schema' : {
                        'type' : 'YAML',
                        'properties' : {
                            'resourceUri' : YAML_GITHUB_RESOURCE
                        }
                    },
                }
            ])

        def test_yadage_workflows_list(self):
            """Load workflow template repository from default listing file for
            YADAGE workflow templates. Ensures that all workflow templates are
            loaded without an exception.
            """
            # Read YADAGE workflow listing file
            with open(CONFIG_FILE, 'r') as f:
                data = yaml.load(f.read())
            # Load workflow templates in listing
            self.db.load(data['templates'])


if __name__ == '__main__':
    unittest.main()
