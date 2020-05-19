#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_ctu
--------

Tests for `lim.ctu` module.
"""

import os
import unittest

from lim.ctu import CTU_Dataset

TEST_VALID_GROUP = 'malware'
TEST_INVALID_GROUP = 'erawlam'
TEST_CACHE = 'tests/test-ctu-cache.json'

class Test_CTU_Dataset(unittest.TestCase):
    def setUp(self):
        self.ctu_dataset = CTU_Dataset(cache_file=TEST_CACHE)
        self.ctu_dataset.load_ctu_metadata()

    def tearDown(self):
        pass

    def test_cache_exists(self):
        self.assertTrue(os.path.exists(TEST_CACHE))

    def test_get_default_group(self):
        self.assertNotEqual(CTU_Dataset.get_default_group(), '')

    def test_get_groups(self):
        self.assertIs(type(CTU_Dataset.get_groups()), type(list()))
        self.assertTrue(len(CTU_Dataset.get_groups()) > 0)

    def test_get_group_VALID(self):
        self.assertIn(TEST_VALID_GROUP, CTU_Dataset.get_groups())

    def test_get_group_INVALID(self):
        self.assertNotIn(TEST_INVALID_GROUP, CTU_Dataset.get_groups())

    def test_get_url_for_group_valid(self):
        self.assertTrue(CTU_Dataset.get_url_for_group(TEST_VALID_GROUP).find('://') != -1)

    def test_get_url_for_group_invalid(self):
        self.assertIs(CTU_Dataset.get_url_for_group(TEST_INVALID_GROUP), None)

    def test_get_columns(self):
        columns = CTU_Dataset.get_columns()
        self.assertIs(type(columns), type(list()))
        self.assertTrue(len(columns) > 0)

    def test_get_disclaimer(self):
        disclaimer = CTU_Dataset.get_disclaimer()
        self.assertTrue("http://dx.doi.org/10.1016/j.cose.2014.05.011" in disclaimer)

    def test_get_scenarios(self):
        scenarios = self.ctu_dataset.get_scenarios()
        self.assertIs(type(scenarios), type(dict()))
        self.assertIn('CTU-Mixed-Capture-1', scenarios)

    def test_get_scenario_names(self):
        scenario_names = self.ctu_dataset.get_scenario_names()
        self.assertIs(type(scenario_names), type(list()))
        self.assertTrue(len(scenario_names) > 0)
        self.assertEqual(scenario_names[0], 'CTU-Mixed-Capture-1',
            msg='scenario_names[0]={}'.format(scenario_names[0]))

    def test_is_valid_scenario_MATCH(self):
        self.assertTrue(self.ctu_dataset.is_valid_scenario('CTU-Mixed-Capture-1'))

    def test_is_valid_scenario_FAIL(self):
        self.assertFalse(self.ctu_dataset.is_valid_scenario('CTU-Moxed-Cipture-1'))

    def test_get_scenario_attribute_url_SUCCESS(self):
        self.assertEqual(
            self.ctu_dataset.get_scenario_attribute('CTU-Mixed-Capture-1', 'URL'),
            'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-1/')

    def test_get_attributes(self):
        items = [a for a in CTU_Dataset.__ATTRIBUTES__]
        self.assertListEqual(items, self.ctu_dataset.get_attributes())

    def test_get_attributes_lower(self):
        items = [a.lower() for a in CTU_Dataset.__ATTRIBUTES__]
        self.assertListEqual(items, self.ctu_dataset.get_attributes_lower())

    def test_get_scenario_attribute_url_FAIL(self):
        try:
            _ = self.ctu_dataset.get_scenario_attribute('CTU-Mixed-Capture-1', 'ORL')
        except RuntimeError as err:
            self.assertIn('is not supported', str(err))
        else:
            raise

    def test_get_scenario_attribute_pcap(self):
        url = self.ctu_dataset.get_scenario_attribute('CTU-Mixed-Capture-1', 'PCAP')
        self.assertEqual(url,
            'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-1/2015-07-28_mixed.pcap',
            msg='url={}'.format(url))

    def test_get_scenario_page(self):
        self.assertIn('DOCTYPE HTML PUBLIC',
                      self.ctu_dataset.get_scenario_page('CTU-Mixed-Capture-1'))

    def test_filename_from_url(self):
        filename = self.ctu_dataset.filename_from_url(
                'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-1/2015-07-28_mixed.pcap')
        self.assertEqual(filename, '2015-07-28_mixed.pcap',
                         msg='filename={}'.format(filename))

    def test_get_fullname_short(self):
        prefix = self.ctu_dataset.__CTU_PREFIX__
        shortname = 'Botnet-1'
        fullname = self.ctu_dataset.get_fullname(shortname)
        self.assertEqual(fullname, prefix + shortname)

    def test_get_fullname_typo(self):
        prefix = self.ctu_dataset.__CTU_PREFIX__
        typoname = 'CTU_Malware_Capture-Botnet-1'
        fullname = self.ctu_dataset.get_fullname(typoname)
        self.assertEqual(fullname, typoname)

    def test_get_shortname_match(self):
        actual_shortname = 'Botnet-1'
        prefix = self.ctu_dataset.__CTU_PREFIX__
        fullname = prefix + actual_shortname
        shortname = self.ctu_dataset.get_shortname(fullname)
        self.assertEqual(shortname, actual_shortname)

    def test_get_shortname_nomatch(self):
        actual_shortname = 'Botnet-1'
        shortname = self.ctu_dataset.get_shortname(actual_shortname)
        self.assertEqual(shortname, actual_shortname)

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
