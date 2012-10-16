# -*- coding: utf-8 -*-
"""
Setup/installation tests for niteoweb.jvzoo
------------------------------------------------
"""

from AccessControl import Unauthorized
from plone.registry.interfaces import IRegistry
from zope.component import getUtility
from niteoweb.jvzoo.tests.base import IntegrationTestCase
from Products.CMFCore.utils import getToolByName
from zope.component import getMultiAdapter
from plone.app.testing import logout

import unittest2 as unittest


class TestInstall(IntegrationTestCase):
    """Test installation of niteoweb.jvzoo into Plone."""

    def setUp(self):
        """Custom shared utility setup for tests."""
        self.portal = self.layer['portal']
        self.installer = getToolByName(self.portal, 'portal_quickinstaller')

    def test_product_installed(self):
        """Test if niteoweb.jvzoo is installed with portal_quickinstaller."""
        self.assertTrue(self.installer.isProductInstalled('niteoweb.jvzoo'))

    def test_disable_registration_for_anonymous(self):
        """Test if anonymous visitors are prevented to register to the site."""
        # The API of the permissionsOfRole() function sucks - it is bound too
        # closely up in the permission management screen's user interface
        self.assertFalse(
            'Add portal member' in [r['name'] for r in
            self.portal.permissionsOfRole('Anonymous') if r['selected']])

    def test_jvzoo_fields_added(self):
        """Test if jvzoo-specific fields were added to memberdata."""
        properties = self.portal.portal_memberdata.propertyIds()
        self.failUnless('product_id' in properties)
        self.failUnless('product_name' in properties)
        self.failUnless('affiliate' in properties)
        self.failUnless('last_purchase_id' in properties)
        self.failUnless('last_purchase_timestamp' in properties)

    def test_use_email_as_login(self):
        """Test if email is indeed used as username."""
        site_properties = self.portal.portal_properties.site_properties
        self.assertTrue(site_properties.getProperty('use_email_as_login'))

    def test_jvzoo_controlpanel_available(self):
        """Test if jvzoo control panel configlet is available."""
        view = getMultiAdapter((self.portal, self.portal.REQUEST),
                               name="jvzoo-settings")
        view = view.__of__(self.portal)
        self.assertTrue(view())

    def test_jvzoo_controlpanel_view_protected(self):
        """Check that access to jvzoo settings is restricted."""
        logout()
        with self.assertRaises(Unauthorized):
            self.portal.restrictedTraverse('@@jvzoo-settings')

    def test_record_akismet_key(self):
        """Test that the secretkey record is in the registry."""
        registry = getUtility(IRegistry)
        record_secretkey = registry.records['niteoweb.jvzoo.interfaces.IJVZooSettings.secretkey']

        from niteoweb.jvzoo.interfaces import IJVZooSettings
        self.assertIn('secretkey', IJVZooSettings)
        self.assertEquals(record_secretkey.value, None)


def test_suite():
    """This sets up a test suite that actually runs the tests in the class
    above."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
