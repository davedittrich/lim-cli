#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_ctu
--------

Tests for `lim.ctu` module.
"""

import os
import tempfile
import unittest

from lim.ctu import (
    get_file_last_mtime,
    normalize_ctu_name,
    CTU_Dataset,
)

TEST_CACHE = os.path.abspath('tests/test-ctu-cache.json')
TEST_EMPTY_CACHE = os.path.join(tempfile.mkdtemp(), 'empty-ctu-cache.json')

class Test_CTU_Dataset(unittest.TestCase):
    def setUp(self):
        self.ctu_dataset = CTU_Dataset(cache_file=TEST_CACHE)
        self.ctu_dataset.load_ctu_metadata()

    def tearDown(self):
        pass

    def test_cache_exists(self):
        self.assertTrue(os.path.exists(TEST_CACHE))

    def test_get_file_last_mtime_exists(self):
        self.assertNotEqual(
            get_file_last_mtime(file_path=TEST_CACHE), 0)

    def test_get_file_last_mtime_notexists(self):
        self.assertEqual(
            get_file_last_mtime(file_path=TEST_EMPTY_CACHE), 0)

    def test_get_file_last_mtime_nopath(self):
        self.assertRaises(RuntimeError,
                          get_file_last_mtime)

    def test_get_file_last_mtime_relative_path(self):
        self.assertRaises(RuntimeError,
                          get_file_last_mtime,
                          file_path='../../../etc/passwd')

    def test_get_file_last_mtime_clean_empty(self):
        os.makedirs(os.path.dirname(TEST_EMPTY_CACHE), exist_ok=True)
        f = open(TEST_EMPTY_CACHE, 'w')
        f.close()
        self.assertEqual(
            get_file_last_mtime(file_path=TEST_EMPTY_CACHE, clean=True), 0)
        self.assertRaises(FileNotFoundError,
                          open,
                          TEST_EMPTY_CACHE,
                          'r')

    def test_get_data_columns(self):
        columns = CTU_Dataset.get_data_columns()
        self.assertIs(type(columns), type(list()))
        self.assertTrue(len(columns) > 0)

    def test_get_index_columns(self):
        columns = CTU_Dataset.get_index_columns()
        self.assertIs(type(columns), type(list()))
        self.assertTrue(len(columns) > 0)

    def test_get_all_columns(self):
        columns = CTU_Dataset.get_all_columns()
        self.assertIs(type(columns), type(list()))
        self.assertTrue(len(columns) > 0)

    def test_get_disclaimer(self):
        disclaimer = CTU_Dataset.get_disclaimer()
        self.assertTrue("http://dx.doi.org/10.1016/j.cose.2014.05.011" in disclaimer)

    def test_get_scenarios(self):
        scenarios = self.ctu_dataset.get_scenarios()
        self.assertIs(type(scenarios), type(dict()))
        self.assertIn('CTU-Malware-Capture-Botnet-48', scenarios)

    def test_get_scenario_names(self):
        scenario_names = self.ctu_dataset.get_scenario_names()
        self.assertIs(type(scenario_names), type(list()))
        self.assertTrue(len(scenario_names) > 0)
        self.assertEqual(scenario_names[0], 'CTU-Malware-Capture-Botnet-90',
            msg=f'scenario_names[0]={scenario_names[0]:40}...')

    def test_is_valid_scenario_short_MATCH(self):
        self.assertFalse(self.ctu_dataset.is_valid_scenario('Botnet-48'))

    def test_is_valid_scenario_long_MATCH(self):
        self.assertTrue(self.ctu_dataset.is_valid_scenario('CTU-Malware-Capture-Botnet-48'))

    def test_is_valid_scenario_FAIL(self):
        self.assertFalse(self.ctu_dataset.is_valid_scenario('CTU-Milware-Copture-Botnet-48'))

    def test_get_scenario_data_url_SUCCESS(self):
        self.assertEqual(
            self.ctu_dataset.get_scenario_data('CTU-Malware-Capture-Botnet-48',
                                              'Capture_URL'),
            'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-48')

    def test_get_data_columns(self):
        items = [a for a in CTU_Dataset.__DATA_COLUMNS__]
        self.assertListEqual(items, self.ctu_dataset.get_data_columns())

    def test_get_scenario_data_url_FAIL(self):
        try:
            _ = self.ctu_dataset.get_scenario_data('CTU-Malware-Capture-Botnet-48',
                                                   'Capture_ORL')
        except RuntimeError as err:
            self.assertIn('is not supported', str(err))

    def test_get_scenario_data_pcap(self):
        url = self.ctu_dataset.get_scenario_data('CTU-Malware-Capture-Botnet-113-1',
                                                 'PCAP')
        self.assertEqual(url,
            'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Malware-Capture-Botnet-113-1/2015-03-12_capture-win6.pcap',
            msg=f'url={url}')

    def test_get_scenario_page_short(self):
        self.assertIn('DOCTYPE HTML PUBLIC',
                      self.ctu_dataset.get_scenario_page('Malware-Botnet-42'))

    def test_get_scenario_page_full(self):
        self.assertIn('DOCTYPE HTML PUBLIC',
                      self.ctu_dataset.get_scenario_page('CTU-Malware-Capture-Botnet-42'))

    def test_filename_from_url(self):
        filename = self.ctu_dataset.filename_from_url(
                'https://mcfp.felk.cvut.cz/publicDatasets/CTU-Mixed-Capture-1/2015-07-28_mixed.pcap')
        self.assertEqual(filename, '2015-07-28_mixed.pcap',
                         msg='filename={}'.format(filename))

    def test_get_fullname_short_5parts(self):
        fullname = self.ctu_dataset.get_fullname(name='CTU-Malware-Capture-Botnet-116-1')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-116-1')

    def test_get_fullname_short_4parts(self):
        fullname = self.ctu_dataset.get_fullname('Malware-Capture-Botnet-116-1')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-116-1')

    def test_get_fullname_short_3parts1(self):
        fullname = self.ctu_dataset.get_fullname(name='Malware-Botnet-116-1')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-116-1')

    def test_get_fullname_short_3parts2(self):
        fullname = self.ctu_dataset.get_fullname(name='Malware-Capture-42')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-42')

    def test_get_fullname_short_2parts1(self):
        fullname = self.ctu_dataset.get_fullname(name='Malware-42')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-42')

    def test_get_fullname_short_2parts2(self):
        fullname = self.ctu_dataset.get_fullname(name='Capture-42')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-42')

    def test_get_fullname_short_1part_number(self):
        fullname = self.ctu_dataset.get_fullname(name='42')
        self.assertEqual(fullname, 'CTU-Malware-Capture-Botnet-42')

    def test_get_fullname_short_1part_name(self):
        self.assertRaises(SystemExit,
                          self.ctu_dataset.get_fullname,
                          name='IoT')

    def test_get_fullname_short_fail(self):
        fullname = self.ctu_dataset.get_fullname(name='Botnet-1')
        self.assertEqual(fullname, None)

    def test_get_fullname_typo(self):
        fullname = self.ctu_dataset.get_fullname(name='CTU_Malware_Capture-Botnet-42')
        self.assertEqual(fullname, None)

    def test_get_shortname_match(self):
        shortname = self.ctu_dataset.get_shortname(name='CTU-Malware-Capture-Botnet-42')
        self.assertEqual(shortname, 'Malware-Botnet-42')

    def test_normalize_ctu_name_lower(self):
        self.assertEqual(normalize_ctu_name('ctu-malware-botnet-42'),
                        'CTU-Malware-Botnet-42')
        self.assertEqual(normalize_ctu_name('iot-malware-33-1'),
                        'IoT-Malware-33-1')
    def test_normalize_ctu_name_upper(self):
        self.assertEqual(normalize_ctu_name('CTU-MALWARE-BOTNET-42'),
                        'CTU-Malware-Botnet-42')
        self.assertEqual(normalize_ctu_name('IOT-MALWARE-33-1'),
                        'IoT-Malware-33-1')
    def test_normalize_ctu_name_mixed(self):
        self.assertEqual(normalize_ctu_name('Ctu-Malware-Botnet-42'),
                        'CTU-Malware-Botnet-42')
        self.assertEqual(normalize_ctu_name('Iot-Malware-33-1'),
                        'IoT-Malware-33-1')
    def test_normalize_ctu_name_random(self):
        self.assertEqual(normalize_ctu_name('CTU-MALWARE-BOTNET-42'),
                        'CTU-Malware-Botnet-42')
        self.assertEqual(normalize_ctu_name('IoT-MaLwArE-33-1'),
                        'IoT-Malware-33-1')

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
