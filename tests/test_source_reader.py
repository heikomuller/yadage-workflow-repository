"""Simple tests for source handle schema reader."""
import unittest

from yadagewfrepo.wftemplate import SourceHandle, TYPE_JSON, TYPE_YAML

YAML_FILE_RESOURCE = 'file:///home/heiko/projects/adage/workflow-repository/tests/data/phenochain/madgraph_delphes.yml'
YAML_GITHUB_RESOURCE = 'https://raw.githubusercontent.com/lukasheinrich/yadage-workflows/master/phenochain/madgraph_delphes.yml'
JSON_FILE_RESOURCE = 'file:///home/heiko/projects/adage/workflow-repository/tests/data/madgraph_delphes.json'

class TestSourceReader(unittest.TestCase):

    def test_invalid_yaml_source(self):
        s = SourceHandle(TYPE_YAML, {'resourceUrl' : YAML_FILE_RESOURCE})
        with self.assertRaises(ValueError):
            wf = s.read()

    def test_invalid_json_source(self):
        s = SourceHandle(TYPE_JSON, {'resourceUrl' : YAML_FILE_RESOURCE})
        with self.assertRaises(ValueError):
            wf = s.read()

    def test_yaml_file_reader(self):
        s = SourceHandle(TYPE_YAML, {'resourceUri' : YAML_FILE_RESOURCE})
        wf = s.read()
        self.assertEquals(len(wf['stages']), 4)

    def test_yaml_github_reader(self):
        s = SourceHandle(TYPE_YAML, {'resourceUri' : YAML_GITHUB_RESOURCE})
        wf = s.read()
        self.assertEquals(len(wf['stages']), 4)

    def test_json_file_reader(self):
        s = SourceHandle(TYPE_JSON, {'resourceUri' : JSON_FILE_RESOURCE})
        wf = s.read()
        self.assertEquals(len(wf['stages']), 4)


if __name__ == '__main__':
    unittest.main()
