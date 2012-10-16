# -*- coding: utf-8 -*-
"""
JVZoo control panel configlet
----------------------------------
"""

from niteoweb.jvzoo import JVZooMessageFactory as _
from niteoweb.jvzoo.interfaces import IJVZooSettings
from plone.app.registry.browser import controlpanel


class JVZooSettingsEditForm(controlpanel.RegistryEditForm):
    """Form for configuring niteoweb.jvzoo."""

    schema = IJVZooSettings
    label = _(u"JVZoo settings")
    description = _(u"""Configure integration with JVZoo API.""")


class JVZooSettingsControlPanel(controlpanel.ControlPanelFormWrapper):
    form = JVZooSettingsEditForm
