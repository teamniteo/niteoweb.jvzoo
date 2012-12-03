# -*- coding: utf-8 -*-
"""
Test all aspects of the @@jvzoo BrowserView
------------------------------------------------
"""

from DateTime import DateTime
from niteoweb.jvzoo.interfaces import IJVZooSettings
from niteoweb.jvzoo.tests.base import IntegrationTestCase
from niteoweb.jvzoo.tests.base import MockedLoggingHandler as logger
from plone import api
from plone.app.testing import TEST_USER_NAME
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from zope.component import getUtility

import mock
import unittest2 as unittest


class TestJVZoo(IntegrationTestCase):
    """Test all aspects of @@jvzoo."""

    def setUp(self):
        """Prepare testing environment."""
        self.portal = self.layer['portal']
        self.view = self.portal.restrictedTraverse('jvzoo')
        self.registration = getToolByName(self.portal, 'portal_registration')
        self.membership = getToolByName(self.portal, 'portal_membership')
        self.groups = getToolByName(self.portal, 'portal_groups')
        self.mailhost = getToolByName(self.portal, 'MailHost')
        self.mailhost.reset()

        # configure product_id to group mapping; the groups must also exist
        registry = getUtility(IRegistry)
        self.settings = registry.forInterface(IJVZooSettings)
        self.settings.mapping = ["1|basic-members", "2|premium-members"]
        self.settings.secretkey = u'secret'
        self.groups.addGroup('basic-members')
        self.groups.addGroup('premium-members')

    def tearDown(self):
        """Clean up after yourself."""
        # reset our mocked logger
        logger.reset()

    def test_call_with_no_POST(self):
        """Test @@jvzoo's response when POST is empty."""
        html = self.view()
        self.failUnless('No POST request.' in html)

    def test_call_with_missing_parameter(self):
        """Test @@jvzoo's response when POST is missing a parameter."""

        # put something into self.request.form so it's not empty
        self.portal.REQUEST.form = dict(foo='bar')

        # test
        html = self.view()
        self.assertEqual(html, "POST parameter missing: 'cverify'")
        self.assertEqual(
            logger.error[0][:72], "POST parameter missing: 'cverify'"
        )

    def test_call_with_missing_secret_key(self):
        """Test @@jvzoo's response when JVZoo secret-key is not set."""

        # put something into self.request.form so it's not empty
        self.portal.REQUEST.form = dict(foo='bar')

        self.settings.secretkey = None

        # test
        html = self.view()
        self.assertEqual(
            html, "POST handling failed: JVZoo secret-key is not set!"
        )
        self.assertEqual(
            logger.error[0],
            "POST handling failed: JVZoo secret-key is not set!"
        )

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._verify_POST')
    def test_call_with_invalid_checksum(self, verify_post):
        """Test @@jvzoo's response when checksum cannot be verified."""

        # put something into self.request.form so it's not empty
        self.portal.REQUEST.form = dict(foo='bar')

        # mock return from _verify_POST
        verify_post.side_effect = AssertionError

        # test
        html = self.view()
        self.assertEqual(html, 'Checksum verification failed.')
        self.assertEqual(logger.error[0][:51], "Checksum verification failed.")

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._verify_POST')
    def test_call_with_internal_exception(self, verify_post):
        """Test @@jvzoo's response when there is an internal problem with the
        code.
        """

        # put something into self.request.form so it's not empty
        self.portal.REQUEST.form = dict(foo='bar')

        # mock return from _verify_POST
        verify_post.side_effect = Exception('Internal foo.')

        # test
        html = self.view()
        self.assertEqual(html, 'POST handling failed: Internal foo.')
        self.assertEqual(
            logger.error[0], "POST handling failed: Internal foo."
        )

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._verify_POST')
    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._parse_POST')
    @mock.patch(
        'niteoweb.jvzoo.browser.jvzoo.JVZooView.create_or_update_member'
    )
    def test_call_with_valid_POST(
        self,
        create_or_update_member,
        parse_post,
        verify_post
    ):
        """Test @@jvzoo's response when POST is valid."""

        # put something into self.request.form so it's not empty
        self.portal.REQUEST.form = dict(value='non empty value')

        # mock post handling
        verify_post.return_value = True
        parse_post.return_value = dict(
            username='username',
            transaction_type='SALE'
        )
        create_or_update_member.return_value = True

        # test
        html = self.view()
        self.assertIn('POST successfully parsed.', html)

    def test_generate_password(self):
        """Test password generation."""
        password = self.view._generate_password(8)
        self.assertEqual(len(password), 8)

    def test_verify_POST(self):
        """Test POST verification process."""
        params = dict(
            secretkey='secret',
            ccustname='fullname',
            cverify='38CFCDED',
        )
        self.view._verify_POST(params)
        self.assertTrue(True)  # no exceptions were raised, test should pass

    def test_parse_POST(self):
        """Test that POST parameters are correctly mirrored into member
        fields.
        """
        params = dict(
            ccustname='fullname',
            ccustemail='email',
            ctransreceipt='last_purchase_id',
            cproditem='product_id',
            cprodtitle='product_name',
            ctransaffiliate='affiliate',
            ctranstime='1325372400',
            ctransaction='SALE',
        )

        expected = dict(
            fullname=u'fullname',
            username='email',
            email='email',
            product_id='product_id',
            product_name='product_name',
            affiliate='affiliate',
            last_purchase_id='last_purchase_id',
            last_purchase_timestamp=DateTime('2012-01-01 00:00:00 GMT+1'),
            transaction_type='SALE',
        )

        result = self.view._parse_POST(params)
        self.assertEqual(result, expected)

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._generate_password')
    def test_create_member(self, generate_password):
        """Test creating a new member out of POST parameters."""
        generate_password.return_value = 'secret123'

        test_data = dict(
            username='john@smith.name',
            password='secret123',
            email='john@smith.name',
            fullname='John Smith',
            product_id='1',
            product_name='product_name',
            affiliate='Jane Affiliate',
            last_purchase_id='invoice_1',
            last_purchase_timestamp=DateTime('2010/01/01'),
        )

        # run method
        self.view.create_or_update_member(test_data['username'], test_data)

        # test member
        member = self.portal.portal_membership.getMemberById(
            test_data['username']
        )
        self.assertEqual(member.getProperty('email'), test_data['email'])
        self.assertEqual(member.getProperty('fullname'), test_data['fullname'])
        self.assertEqual(
            member.getProperty('product_id'),
            test_data['product_id']
        )
        self.assertEqual(
            member.getProperty('product_name'),
            test_data['product_name']
        )
        self.assertEqual(
            member.getProperty('affiliate'),
            test_data['affiliate']
        )
        self.assertEqual(
            member.getProperty('last_purchase_id'),
            test_data['last_purchase_id']
        )
        self.assertEqual(
            member.getProperty('last_purchase_timestamp'),
            test_data['last_purchase_timestamp']
        )

        # test email
        self.assertEqual(len(self.mailhost.messages), 1)
        msg = self.mailhost.messages[0]
        self.assertIn('To: %(email)s' % test_data, msg)
        self.assertIn(
            'Subject: =?utf-8?q?Your_Plone_site_login_credentials',
            msg
        )
        self.assertIn('u: %(username)s' % test_data, msg)
        self.assertIn('p: %(password)s' % test_data, msg)

        # test that we created group
        self.assertIn('jvzoo', self.groups.getGroupIds())
        self.assertIn('jvzoo', member.getGroups())

        # test that member was added to product group
        self.assertIn('basic-members', member.getGroups())

        # now test that if a request for same member is posted this member gets
        # updated and added to new product group
        test_data['username'] = 'john@smith.name'
        test_data['product_id'] = '2'
        test_data['last_purchase_id'] = 'invoice_2'
        test_data['last_purchase_timestamp'] = DateTime('2010/02/02')

        # run method
        self.view.create_or_update_member(test_data['username'], test_data)

        # test that member was updated and added to new product group
        member = self.membership.getMemberById(test_data['username'])
        self.assertEqual(member.getProperty('product_id'), '2')
        self.assertEqual(member.getProperty('last_purchase_id'), 'invoice_2')
        self.assertEqual(
            member.getProperty('last_purchase_timestamp'),
            DateTime('2010/02/02')
        )
        self.assertIn('premium-members', member.getGroups())

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._generate_password')
    def test_auto_cancel_member(self, generate_password):
        """Test creating a new member out of POST parameters."""
        generate_password.return_value = 'secret123'

        test_data = dict(
            username='john@smith.name',
            password='secret123',
            email='john@smith.name',
            fullname='John Smith',
            product_id='1',
            product_name='product_name',
            affiliate='Jane Affiliate',
            last_purchase_id='invoice_1',
            last_purchase_timestamp=DateTime('2010/01/01'),
        )

        # run method
        self.view.create_or_update_member(test_data['username'], test_data)

        # get member
        member = self.membership.getMemberById(test_data['username'])

        # Check if user has Member role
        self.assertIn('Member', api.user.get_roles(user=member.getUser()))

        # Call cancel user method
        self.view.auto_cancel_user(test_data['username'], test_data)

        # Now check if user does not have Member role
        self.assertNotIn('Member', api.user.get_roles(user=member.getUser()))

        # Check for autocanceled group
        autocanceled_group = api.group.get('autocanceled')
        self.assertIsNotNone(autocanceled_group)

        # Check if user is in autocanceled group
        self.assertIn(
            autocanceled_group, api.group.get_groups(user=member.getUser())
        )

    def test_update_member(self):
        """Test updating an existing member with POST parameters."""

        old_data = dict(
            username='john@smith.name',
            email='john@smith.name',
            product_id='1',
            last_purchase_id='invoice_1',
            last_purchase_timestamp=DateTime('2010/01/01'),
        )

        new_data = old_data
        new_data['product_id'] = '2'
        new_data['last_purchase_id'] = 'invoice_2'
        new_data['last_purchase_timestamp'] = DateTime('2010/02/02')

        # create a member in advance so POST parameters will perform UPDATE
        # instead of CREATE
        self.registration.addMember(
            old_data['username'],
            'test_password',
            properties=old_data
        )

        # run method
        self.view.create_or_update_member(new_data['username'], new_data)

        # test member
        member = self.portal.acl_users.getUserById(new_data['username'])
        self.assertEqual(
            member.getProperty('last_purchase_id'),
            new_data['last_purchase_id']
        )
        self.assertEqual(
            member.getProperty('last_purchase_timestamp'),
            new_data['last_purchase_timestamp']
        )

        # test that member was added to a new product group
        self.assertIn('premium-members', member.getGroups())

        # test email
        self.assertEqual(len(self.mailhost.messages), 0)

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.JVZooView._generate_password')
    def test_create_member_without_group_mapping(self, generate_password):
        """Test creating a new member when group mapping does not match
        any group to member's product_id.
        """
        generate_password.return_value = 'secret123'

        test_data = dict(
            username='john@smith.name',
            password='secret123',
            email='john@smith.name',
            fullname='John Smith',
            product_id='1',
            product_name='product_name',
            affiliate='Jane Affiliate',
            last_purchase_id='invoice_1',
            last_purchase_timestamp=DateTime('2010/01/01'),
        )

        self.settings.mapping = ["3|other-members", "2|premium-members"]

        # run method
        self.view.create_or_update_member(test_data['username'], test_data)

        # test member
        member = self.portal.portal_membership.getMemberById(
            test_data['username']
        )
        self.assertEqual(member.getProperty('email'), test_data['email'])
        self.assertEqual(member.getProperty('fullname'), test_data['fullname'])
        self.assertEqual(
            member.getProperty('product_id'),
            test_data['product_id']
        )
        self.assertEqual(
            member.getProperty('product_name'),
            test_data['product_name']
        )
        self.assertEqual(
            member.getProperty('affiliate'),
            test_data['affiliate']
        )
        self.assertEqual(
            member.getProperty('last_purchase_id'),
            test_data['last_purchase_id']
        )
        self.assertEqual(
            member.getProperty('last_purchase_timestamp'),
            test_data['last_purchase_timestamp']
        )

        # test email
        self.assertEqual(len(self.mailhost.messages), 1)
        msg = self.mailhost.messages[0]
        self.assertIn('To: %(email)s' % test_data, msg)
        self.assertIn(
            'Subject: =?utf-8?q?Your_Plone_site_login_credentials',
            msg
        )
        self.assertIn('u: %(username)s' % test_data, msg)
        self.assertIn('p: %(password)s' % test_data, msg)

        # test that we created jvzoo group
        self.assertIn('jvzoo', self.groups.getGroupIds())
        self.assertIn('jvzoo', member.getGroups())

        # test that member is not added to any product groups
        self.assertEqual(['jvzoo', 'AuthenticatedUsers'], member.getGroups())

    @mock.patch('niteoweb.jvzoo.browser.jvzoo.logger')
    def test_add_to_product_group_edge_cases(self, logger):
        """Test that member is added to a product group."""
        # first, let's test what happens if product_id is not found
        self.view._add_to_product_group(TEST_USER_NAME, '666')
        logger.error.assert_called_with(
            "Product_id 666 does not have a group assigned.")

        # next, let's test what happens if group for product_id is not found
        self.settings.mapping = ["13|foo-members"]
        self.view._add_to_product_group(TEST_USER_NAME, '13')
        logger.error.assert_called_with(
            "Cannot add a member (test-user) to a group, because group "
            "does not exist: 'foo-members'")

        # now let's add a member to a group and test that nothing happens when
        # @@jvzoo want's to add a member to this group again
        self.groups.addPrincipalToGroup(TEST_USER_NAME, 'basic-members')
        self.view._add_to_product_group(TEST_USER_NAME, '1')

    def test_email_password(self):
        """Test headers and text of email that is sent to newly created
        member."""

        test_data = dict(
            username='john@smith.name',
            password='secret123',
            email='john@smith.name',
            fullname='John Smith',
        )

        # set portal properties
        self.portal.title = u'JVZoo Integration Site'
        self.portal.email_from_address = "mail@plone.test"

        # run method
        self.view._email_password(
            test_data['username'], test_data['password'], test_data
        )

        # test email
        self.assertEqual(len(self.mailhost.messages), 1)
        msg = self.mailhost.messages[0]

        # test email headers
        self.failUnless('To: %(email)s' % test_data in msg)
        self.failUnless('From: %s' % self.portal.email_from_address in msg)
        self.failUnless(
            'Subject: =?utf-8?q?Your_JVZoo_Integration'
            '_Site_login_credentials' in msg
        )

        # test email body text
        self.failUnless('Hello %(fullname)s,' % test_data in msg)
        self.failUnless('u: %(username)s' % test_data in msg)
        self.failUnless('p: %(password)s' % test_data in msg)
        self.failUnless(
            'You can now login at http://nohost/plone/login_form'in msg
        )
        self.failUnless(
            'let us know on %s' % self.portal.email_from_address in msg
        )
        self.failUnless('Best wishes,\n%s Team' % self.portal.title in msg)

    def test_cancel_email(self):
        """Test headers and text of email that is sent to 'from' address
        when user is auto-canceled."""

        test_data = dict(
            username='john@smith.name',
            password='secret123',
            email='john@smith.name',
            properties={
                'fullname': 'John Smith'
            }
        )

        test_user = api.user.create(
            username=test_data['username'],
            email=test_data['email'],
            password=test_data['password'],
            properties=test_data['properties']
        )

        # set portal properties
        self.portal.title = u'JVZoo Integration Site'
        self.portal.email_from_address = "mail@plone.test"

        # run method
        self.view._cancel_email(test_user)

        # test email
        self.assertEqual(len(self.mailhost.messages), 1)
        msg = self.mailhost.messages[0]

        with open('/tmp/madafaka.txt', 'w') as f:
            f.write(msg)

        # test subject
        self.assertIn(
            "Subject: =?utf-8?q?JVZoo_Integration_Site_Cancelation_-_"
            "=5Bjohn=40smith=2Ename=5D?=",
            msg
        )

        # test 'to' email address
        self.assertIn(
            "To: mail@plone.test",
            msg
        )

        # test 'from' email address
        self.assertIn(
            "From: mail@plone.test",
            msg
        )

        # test member
        self.assertIn(
            "Member: John Smith",
            msg
        )

        # test username
        self.assertIn(
            "Member email/username: john@smith.name",
            msg
        )


def test_suite():
    """This sets up a test suite that actually runs the tests in the class
    above."""
    return unittest.defaultTestLoader.loadTestsFromName(__name__)
