#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains a test for the default plist parser."""

import os
import unittest

# Always import plist to force plugin registration.
from plaso import plist  # pylint: disable=W0611
from plaso.events import plist_event
from plaso.lib import errors
from plaso.lib import plist_interface


class MockPlugin(plist_interface.PlistPlugin):
  """Mock plugin."""
  PLIST_PATH = 'plist_binary'
  PLIST_KEYS = frozenset(['DeviceCache', 'PairedDevices'])

  def GetEntries(self):
    yield plist_event.PlistEvent(
        '/DeviceCache/44-00-00-00-00-00', 'LastInquiryUpdate',
        1351827808261762)


class TestPlistInterface(unittest.TestCase): # pylint: disable=R0923
  """The unittests for plist interface and components."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.base_path = 'test_data'
    self.fd = os.path.join(self.base_path, 'plist_binary')
    self.plugins = plist_interface.GetPlistPlugins()
    self.top_level_dict = {
        'DeviceCache': {
            '44-00-00-00-00-04': {
                'Name': 'Apple Magic Trackpad 2', 'LMPSubversion': 796,
                'Services': '', 'BatteryPercent': 0.61},
            '44-00-00-00-00-02': {
                'Name': 'test-macpro', 'ClockOffset': 28180,
                'PageScanPeriod': 2, 'PageScanRepetitionMode': 1}}}

  def testGetPlistPlugins(self):
    self.assertTrue(self.plugins)

  def testDefaultInList(self):
    self.assertTrue('DefaultPlugin' in [x.plugin_name for x in self.plugins])

  def testMockPluginErrors(self):
    """Ensure plugin proceeds only if both correct filename and keys exist."""
    plugin = MockPlugin(None)

    # Test correct filename and keys.
    self.assertTrue(
        plugin.Process('plist_binary', {'DeviceCache': 1, 'PairedDevices': 1}))

    # Correct filename with odd filename cAsinG.  Adding an extra useless key.
    self.assertTrue(
        plugin.Process('pLiSt_BinAry', {'DeviceCache': 1, 'PairedDevices': 1,
                                        'R@ndomExtraKey': 1}))
    # Test wrong filename.
    with self.assertRaises(errors.WrongPlistPlugin):
      plugin.Process('wrong_file.plist', {'DeviceCache': 1, 'PairedDevices': 1})

    # Test not enough required keys.
    with self.assertRaises(errors.WrongPlistPlugin):
      plugin.Process('plist_binary', {'Useless_Key': 0, 'PairedDevices': 1})

  def testRecurseKey(self):
    # Ensure with a depth of 1 we only return the root key.
    result = list(plist_interface.RecurseKey(self.top_level_dict, depth=1))
    self.assertEquals(len(result), 1)

    # Trying again with depth limit of 2 this time.
    result = list(plist_interface.RecurseKey(self.top_level_dict, depth=2))
    self.assertEquals(len(result), 3)

    # A depth of two should gives us root plus the two devices. Let's check.
    my_keys = []
    for root, key, value in result:
      my_keys.append(key)
    expected = set(['DeviceCache', '44-00-00-00-00-04', '44-00-00-00-00-02'])
    self.assertTrue(expected == set(my_keys))

  def testGetKey(self):
    # Match DeviceCache from the root level.
    key = ['DeviceCache']
    result = plist_interface.GetKeys(self.top_level_dict, key)
    self.assertEquals(len(result), 1)

    # Look for a key nested a layer beneath DeviceCache from root level.
    # Note: overriding the default depth to look deeper.
    key = ['44-00-00-00-00-02']
    result = plist_interface.GetKeys(self.top_level_dict, key, depth=2)
    self.assertEquals(len(result), 1)

    # Check the value of the result was extracted as expected.
    self.assertTrue('test-macpro' == result[key[0]]['Name'])


if __name__ == '__main__':
  unittest.main()