"""Simple tests for source handle schema reader."""
import unittest

from yadagetemplates.wftemplate import SourceHandle

class TestSourceReader(unittest.TestCase):

    def test_yaml_github_reader(self):
        s = SourceHandle('from-github/phenochain', 'madgraph_rivet.yml')
        wf = s.read()
        self.assertEquals(len(wf['stages']), 5)


if __name__ == '__main__':
    unittest.main()
