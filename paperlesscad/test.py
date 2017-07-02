import unittest
from collections import Counter
from paperlesscad.solution import dfm_check


def summarize(results):
    "Helper function to make it easy to check raised issues."
    return Counter(i['issue'] for i in results['issues'])


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
        self.assertTrue(any(i == issue for i in result['issues']))
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
        small_cut_issues = [i for i in result['issues']
                            if i['issue'] == 'small-cut']
        self.assertGreater(len(small_cut_issues), 0)
        self.assertTrue(len(small_cut_issues[0]['faces']) >= 1)

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

    def test_small_outside_edge(self):
        result = dfm_check('step_files/small_outside_edge.step')
        self.assertEqual(result, {'issues': []})

    def test_small_outside_radii(self):
        result = dfm_check('step_files/small_outside_radii.step')
        self.assertEqual(result, {'issues': []})

    def test_thin_cut_large_ends(self):
        result = dfm_check('step_files/thin_cut_large_ends.step')
        summary = summarize(result)
        self.assertIn('small-cut', summary)

    def test_thin_cut_from_outside(self):
        result = dfm_check('step_files/thin_cut_from_outside.step')
        summary = summarize(result)
        self.assertIn('small-cut', summary)

    def test_thin_cut_between_radii(self):
        result = dfm_check('step_files/thin_cut_between_radii.step')
        summary = summarize(result)
        self.assertIn('small-cut', summary)

    def test_sharp_internal_corner(self):
        result = dfm_check('step_files/sharp_internal_corner.step')
        summary = summarize(result)
        self.assertIn('tight-corner', summary)

    def test_small_radius_internal_corner(self):
        result = dfm_check('step_files/small_radius_internal_corner.step')
        summary = summarize(result)
        self.assertIn('tight-corner', summary)

    def test_large_radius_internal_corner(self):
        result = dfm_check('step_files/large_radius_internal_corner.step')
        self.assertEqual(result, {'issues': []})

    def test_shallow_internal_corner(self):
        result = dfm_check('step_files/shallow_internal_corner.step')
        summary = summarize(result)
        self.assertIn('tight-corner-mild', summary)

    def test_shallow_internal_radius(self):
        result = dfm_check('step_files/shallow_internal_radius.step')
        summary = summarize(result)
        self.assertIn('tight-corner-mild', summary)

    def test_counter_confusion(self):
        result = dfm_check('step_files/counter_confusion.step')
        summary = summarize(result)
        self.assertNotIn('counter-bore', summary)
        self.assertNotIn('counter-sink', summary)
        self.assertIn('non-uniform', summary)

    def test_manufacturable_extrusion(self):
        result = dfm_check('step_files/manufacturable_extrusion.step')
        self.assertEqual(result, {'issues': []})

    def test_manufacturable_splines(self):
        result = dfm_check('step_files/manufacturable_splines.step')
        self.assertEqual(result, {'issues': []})

    def test_unmanufacturable_extrusion(self):
        result = dfm_check('step_files/unmanufacturable_extrusion.step')
        summary = summarize(result)
        self.assertIn('non-uniform', summary)

if __name__ == '__main__':
    unittest.main()
