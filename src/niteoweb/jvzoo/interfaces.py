# -*- coding: utf-8 -*-
"""
Interfaces, Events and Exceptions
---------------------------------
"""

from niteoweb.jvzoo import JVZooMessageFactory as _
from zope import schema
from zope.interface import Attribute
from zope.interface import implements
from zope.interface import Interface
from niteoweb.jvzoo import parse_mapping


# control panel schema
class IJVZooSettings(Interface):
    """Definition of fields for niteoweb.jvzoo configuration form."""

    secretkey = schema.Password(
        title=_(u"JVZoo Secret Key"),
        description=_(
            u"help_secretkey",
            default=u"Enter the Secret Key you got from JVZoo to access "
                    "their API."),
        required=True,
    )

    mapping = schema.List(
        title=_(u"Product ID to Group mapping"),
        description=_(
            u"help_secretkey",
            default=u"Optionally, you can set Product ID to Group mapping. "
                    "This is used to automatically add a new member to a "
                    "group based on which JVZoo product was purchased. Format: "
                    "'PRODUCT_ID|GROUP_ID'. Example: '1|premium_members'. "
                    "One mapping per line."),
        required=False,
        value_type=schema.ASCIILine(),
        constraint=parse_mapping,
    )


# exceptions
class JVZooError(Exception):
    """Base class for niteoweb.jvzoo exception."""


class SecretKeyNotSet(JVZooError):
    """Exception thrown when secret-key for jvzoo is not set."""


# events
class IJVZooEvent(Interface):
    """Base class for niteoweb.jvzoo events."""


class IMemberCreatedEvent(IJVZooEvent):
    """Interface for MemberCreatedEvent."""
    context = Attribute("A member was created by @@jvzoo.")


class MemberCreatedEvent(object):
    """Emmited when a new member is created by jvzoo post-back service
    calling @@jvzoo.
    """
    implements(IMemberCreatedEvent)

    def __init__(self, context, username):
        self.context = context
        self.username = username
