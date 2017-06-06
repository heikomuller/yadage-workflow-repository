import yaml
import unittest

from yadagetemplates.wftemplate import WorkflowTemplateRepository

WORKFLOW_LISTING_FILE = './data/yadage-workflows.yaml'
DUPLICATE_WORKFLOW_LISTING_FILE = './data/yadage-duplicate-workflows.yaml'

class TestWorkflowRepositoryReader(unittest.TestCase):

    def setUp(self):
        """Read the default YADAGE workflow schema defintiion and initialize an
        empty repository.
        """
        self.db = WorkflowTemplateRepository()

    def test_duplicate_workflow_id(self):
        """Create workflow template repository from object that contains two
        workflows with identical id's.
        """
        # Read YADAGE workflow listing file
        with open(DUPLICATE_WORKFLOW_LISTING_FILE, 'r') as f:
            data = yaml.load(f.read())
        # Load workflow templates in listing
        with self.assertRaises(ValueError):
            self.db.load(data['templates'])

    def test_yadage_workflows_list(self):
        """Load workflow template repository from default listing file for
        YADAGE workflow templates. Ensures that all workflow templates are
        loaded without an exception.
        """
        # Read YADAGE workflow listing file
        with open(WORKFLOW_LISTING_FILE, 'r') as f:
            data = yaml.load(f.read())
        # Load workflow templates in listing
        self.db.load(data['templates'])
        self.assertEquals(len(self.db.db), 7)


if __name__ == '__main__':
    unittest.main()
