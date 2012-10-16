# -*- coding: utf-8 -*-
"""
Handling JVZoo purchase notifications
------------------------------------------
"""

from DateTime import DateTime
from niteoweb.jvzoo import parse_mapping
from niteoweb.jvzoo.interfaces import SecretKeyNotSet
from niteoweb.jvzoo.interfaces import IJVZooSettings
from niteoweb.jvzoo.interfaces import MemberCreatedEvent
from plone.registry.interfaces import IRegistry
from Products.CMFCore.utils import getToolByName
from Products.Five.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from zope.component import getUtility
from zope.event import notify
from zope.interface import Invalid

import hashlib
import random
import string
import logging

logger = logging.getLogger("niteoweb.jvzoo")


class JVZooView(BrowserView):
    """A BrowserView that JVZoo calls after a purchase."""

    def __call__(self):
        """Request handler for JVZoo purchase notifications."""
        # check for POST request
        if not self.request.form:
            return 'No POST request.'

        # prepare values
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IJVZooSettings)
        params = dict(self.request.form)
        params['secretkey'] = settings.secretkey

        try:
            # verify and parse post
            self._verify_POST(params)
            data = self._parse_POST(params)
            self.create_or_update_member(data['username'], data)

        # something went wrong?
        except KeyError as ex:
            msg = "POST parameter missing: %s" % ex
            logger.error(msg)
            return msg

        except AssertionError:
            msg = "Checksum verification failed."
            logger.error(msg)
            return msg

        except Exception as ex:
            msg = "POST handling failed: %s" % ex
            logger.error(msg)
            return msg

        return 'POST successfully parsed.'

    def _verify_POST(self, params):
        """Verifies if received POST is a valid JVZoo POST request.

        :param params: POST parameters sent by JVZoo Notification Service
        :type params: dict

        """
        if not params['secretkey']:
            raise SecretKeyNotSet('JVZoo secret-key is not set!')
        strparams = ""
        for key in iter(sorted(params.iterkeys())):
            if key in ['cverify', 'secretkey']:
                continue
            strparams += params[key] + "|"
        strparams += params['secretkey']
        sha = hashlib.sha1(strparams.encode('utf-8')).hexdigest().upper()
        assert params['cverify'] == sha[:8], 'Checksum verification failed.'

    def _parse_POST(self, params):
        """Parses POST from JVZoo and extracts information we need.

        :param params: POST parameters sent by JVZoo Notification Service
        :type params: dict

        """
        return {
            'username': params['ccustemail'],
            'email': params['ccustemail'],
            'fullname': u"%s" % params['ccustname'].decode("utf-8"),
            'product_id': params['cproditem'],
            'product_name': params['cprodtitle'],
            'affiliate': params['ctransaffiliate'],
            'last_purchase_id': params['ctransreceipt'],
            'last_purchase_timestamp': DateTime(
                int(params['ctranstime']),
                datefmt='epoch'
            ),
        }

    def create_or_update_member(self, username, data):
        """Creates or updates a Plone member.

        This method create a new Plone member if one with selected username does
        not exist yet.

        In case the member already exists, this method updates member's fields.
        Besides that, if `Product ID to group mapping` configuration in
        JVZoo control panel is set, it also adds the member to the
        respective group.

        :param username: username of member that is to be created/updated
        :type username: string
        :param data: member data of member that is to be created/updated
        :type data: dict
        """

        registration = getToolByName(self.context, 'portal_registration')
        membership = getToolByName(self.context, 'portal_membership')
        password = self._generate_password()

        # update or create member
        member = membership.getMemberById(username)
        if member:
            # update existing member
            member.setMemberProperties(mapping={
                'product_id': data['product_id'],
                'last_purchase_id': data['last_purchase_id'],
                'last_purchase_timestamp': data['last_purchase_timestamp'],
            })
        else:
            # create a new member
            member = registration.addMember(username, password, properties=data)
            notify(MemberCreatedEvent(self, username))
            self._email_password(username, password, data)

        # create default jvzoo group and add member to it
        groups = getToolByName(self.context, 'portal_groups')
        group_name = "jvzoo"
        if group_name not in groups.getGroupIds():
            groups.addGroup(group_name)
        groups.addPrincipalToGroup(username, group_name)

        # handle product_id to group_name mapping
        self._add_to_product_group(username, data['product_id'])

    def _add_to_product_group(self, username, product_id):
        """If ``product_id`` has a group mapping set in control panel,
        add member to this group.

        :param username: username of member that is to be added to a group
        :type username: string
        :param data: product_id to find in the mapping
        :type data: string
        """

        groups = getToolByName(self.context, 'portal_groups')
        registry = getUtility(IRegistry)
        settings = registry.forInterface(IJVZooSettings)

        try:
            mapping = parse_mapping(settings.mapping)
        except Invalid:
            logger.error("Due to problems with parsing product_id to group "
                         "mapping, the member '%s' was not added to group."
                         % username)
            return

        group_name = mapping.get(product_id)
        if not group_name:
            logger.error("Product_id %s does not have a group assigned."
                         % product_id)
            return

        if group_name not in groups.getGroupIds():
            logger.error("Cannot add a member (%s) to a group, because group "
                         "does not exist: '%s'" % (username, group_name))
            return

        groups.addPrincipalToGroup(username, group_name)

    def _email_password(self, mto, password, data):
        """Send an email with member's password.

        :param mto: email receipient
        :type mto: string

        :param password: member's login password that is written in the email
        :type string: string

        :param data: member data needed to construct the email (fullname, ...)
        :type data: dict

        """

        portal_title = self.context.title

        # email from address
        envelope_from = self.context.email_from_address

        # email subject
        subject = u"Your %s login credentials" % portal_title

        # email body text
        options = dict(
            fullname=data['fullname'],
            username=data['username'],
            password=password,
            login_url=self.context.absolute_url() + '/login_form',
            email_from=envelope_from,
            portal_title=portal_title,
        )
        body = ViewPageTemplateFile("email.pt")(self, **options)

        # send email
        mailhost = getToolByName(self.context, 'MailHost')
        mailhost.send(body, mto=mto, mfrom=envelope_from, subject=subject, charset='utf-8')

    def _generate_password(self, length=8, include=string.letters + string.digits):
        """Generate random password in base64.

        :param include: set of characters to choose from
        :type include: string

        :param length: number of characters to generate
        :type length: integer

        :returns: a random password
        :rtype: string

        """
        random.seed()
        return ''.join(random.sample(include, length))
