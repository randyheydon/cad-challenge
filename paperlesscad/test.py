import unittest
from paperlesscad.solution import dfm_check


class TestSolution(unittest.TestCase):

    def test_good_part(self):
        result = dfm_check('step_files/good_part.STEP')
        self.assertEqual(
            {'issues': []},
            result)

    def test_chamfer(self):
        result = dfm_check('step_files/chamfer.STEP')
        issue = {'issue': 'chamfer', 'faces': None}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            {'issues': [issue]},
            result)

    def test_radius(self):
        result = dfm_check('step_files/radius.STEP')
        issue = {'issue': 'radius', 'faces': None}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            {'issues': [issue]},
            result)
        result = dfm_check('step_files/radius_both_edges.STEP')
        self.assertGreater(len(result['issues']), 0)
        for i in result['issues']:
            self.assertEqual(issue, i)

    def test_nonuniform(self):
        result = dfm_check('step_files/nonuniform.STEP')
        issue = {'issue': 'non-uniform', 'faces': None}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            {'issues': [issue]},
            result)
        result = dfm_check('step_files/milled_pocket.STEP')
        self.assertEqual(
            {'issues': [issue]},
            result)

    def test_small_hole(self):
        result = dfm_check('step_files/small_hole_2.STEP')
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            'small-hole',
            result['issues'][0]['issue'])
        self.assertTrue(len(result['issues'][0]['faces']) >= 1)

    def test_small_cut(self):
        result = dfm_check('step_files/small_hole.STEP')
        # example: issue = {'issue': 'small-hole', 'faces': [1]}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            'small-cut',
            result['issues'][0]['issue'])
        self.assertTrue(len(result['issues'][0]['faces']) >= 1)

    def test_draft(self):
        result = dfm_check('step_files/draft.STEP')
        issue = {'issue': 'draft', 'faces': None}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            {'issues': [issue]},
            result)

    def test_countersink(self):
        result = dfm_check('step_files/counter_sinks.STEP')
        # example: issue = {'issue': 'counter-sink', 'faces': [1, 2]}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            'counter-sink',
            result['issues'][0]['issue'])
        self.assertTrue(len(result['issues'][0]['faces']) >= 2)

    def test_counterbore(self):
        result = dfm_check('step_files/counter_bore.STEP')
        # example: issue = {'issue': 'counter-bore', 'faces': [1]}
        self.assertGreater(len(result['issues']), 0)
        self.assertEqual(
            'counter-bore',
            result['issues'][0]['issue'])
        self.assertTrue(len(result['issues'][0]['faces']) >= 1)

if __name__ == '__main__':
    unittest.main()
