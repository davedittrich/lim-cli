#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_ctu
--------

Tests for `lim.ctu` module.
"""

import unittest

from lim.ctu import CTU_Dataset

TEST_VALID_GROUP = 'malware'
TEST_INVALID_GROUP = 'erawlam'
TEST_CACHE = 'ctu-cache.json'

class Test_CTU_Dataset(unittest.TestCase):
    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_get_default_group(self):
        assert CTU_Dataset.get_default_group() != ''

    def test_get_groups(self):
        assert type(CTU_Dataset.get_groups()) is type(list())
        assert len(CTU_Dataset.get_groups()) > 0

    def test_get_group_VALID(self):
        assert TEST_VALID_GROUP in CTU_Dataset.get_groups()

    def test_get_group_INVALID(self):
        assert TEST_INVALID_GROUP not in CTU_Dataset.get_groups()

    def test_get_url_for_group_valid(self):
        assert CTU_Dataset.get_url_for_group(TEST_VALID_GROUP).find('://') != -1

    def test_get_url_for_group_invalid(self):
        assert CTU_Dataset.get_url_for_group(TEST_INVALID_GROUP) is None

    def test_get_columns(self):
        columns = CTU_Dataset.get_columns()
        assert type(columns) is type(list())
        assert len(columns) > 0

    def test_get_disclaimer(self):
        disclaimer = CTU_Dataset.get_disclaimer()
        assert "http://dx.doi.org/10.1016/j.cose.2014.05.011" in disclaimer

    def test_get_scenarios(self):
        ctu_dataset = CTU_Dataset(cache_file=TEST_CACHE)
        ctu_dataset.load_ctu_metadata()
        scenarios = ctu_dataset.get_scenarios()
        assert type(scenarios) is type(dict())
        assert 'CTU-Mixed-Capture-1' in scenarios

    def test_get_scenario_names(self):
        ctu_dataset = CTU_Dataset(cache_file=TEST_CACHE)
        ctu_dataset.load_ctu_metadata()
        scenario_names = ctu_dataset.get_scenario_names()
        assert type(scenario_names) is type(list())
        assert len(scenario_names) > 0
        assert scenario_names[0] == 'CTU-Mixed-Capture-1'

if __name__ == '__main__':
    import sys
    sys.exit(unittest.main())

# vim: set fileencoding=utf-8 ts=4 sw=4 tw=0 et :
