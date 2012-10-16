===============================
JVZoo.com integration for Plone
===============================

A Plone add-on that integrates `JVZoo <http://jvzoo.com>`_ digital
products retailer system with `Plone <http://plone.org>`_ to enable paid
memberships on your site.

* `Source code @ GitHub <https://github.com/niteoweb/niteoweb.jvzoo>`_
* `Releases @ PyPI <http://pypi.python.org/pypi/niteoweb.jvzoo>`_
* `Documentation @ ReadTheDocs <http://readthedocs.org/docs/niteowebjvzoo>`_
* `Continuous Integration @ Travis-CI <http://travis-ci.org/niteoweb/niteoweb.jvzoo>`_


How it works
============

#. Visitor comes to ``yoursite.com/order`` (or similar) and clicks `Order` link.
#. Visitor is sent to JVZoo's order form (on ``http://jvzoo.com``),
   where he enters his personal information and performs payment.
#. JVZoo calls-back a special view on your plone site (``/@@jvzoo``),
   which reads POST data from JVZoo, verifies it against your
   ``Secret Key`` and creates a new member.
#. The following information is stored in member data for later use:

    ``product_id``
        JVZoo's `Product ID` of the purchased item.

    ``product_name``
        JVZoo's `Product Name` of the purchased item.

    ``affiliate``
        Affiliate who referred the buyer.

    ``last_purchase_id``
        JVZoo's `Receipt ID` of the last purchase. This field gets updated
        on every recurring payment.

    ``last_purchase_timestamp``
        Exact timestamp of the last purchase. This field gets updated on every
        recurring payment.

#. Upon creating a new member, Plone sends an email with login password.
#. An ``IMemberCreateEvent`` is emitted upon creating a new member.
#. The new member can now login and use the site.
#. It is possible to create a ``product_id`` to ``group_name`` mapping in
   Plone Control Panel. This means that if a member purchased a product which
   is listed in this mapping, the member will also be added to a group mapped
   to this product.

.. note::

    If a member already exists in Plone, then the ``@@jvzoo`` view simply
    updates ``last_purchase_id`` and ``last_purchase_timestamp`` member fields.
    The member will also be added to the new product group, but also kept in
    the old.


Demo
====

You can see this product in action at
`BigContentSearch <http://bigcontentsearch.com/>`_.


Installation
============

To install ``niteoweb.jvzoo`` you simply add
``niteoweb.jvzoo`` to the list of eggs in your buildout, run
buildout and restart Plone. Then, install `niteoweb.jvzoo` using the
Add-ons control panel.


Configuration
=============

JVZoo
-----

Go to `JVZoo.com <http://jvzoo.com>`_ and use ``Sellers`` ->
``Add a Product`` to add a new `Product`.

Then check the option ``External Program Integration``. For `URL`
set ``http://yoursite.com/@@jvzoo``. Under the ``My Account`` page
set the ``JVZIPN Secret Key``.


Plone
-----

Go to ``Site Setup`` -> ``jvzoo`` control panel form and configure
the ``Secret Key`` field by pasting in the `Secret Key` you defined above.

You can also configure the ``product_id`` to ``group_name`` mapping. This comes
in effect when member purchases a product which is listed in this mapping, the
member will also be added to a group mapped to this product.

For example, imagine you have the following in your mapping::

    1|basic-members
    2|premium-members

Members purchasing the product with id ``1`` will be added to the
``basic-members`` group, whose purchasing ``2`` will be added to the
``premium-members`` group. For others, nothing will be done.

When switching products, an updated member will be added to new product
group, but also kept in the old group. No information is removed/deleted.


Test it
=======

You are now ready to do a test buy! Go back to ``Sellers`` and click
``Test Purchases``. Select a product, click ``Create Test Purchase Code`` and
finish by clicking the link in ``Buy / Link`` column in the table below. In
order for the purchase link to work, the product needs to be activated in
``Sellers Dashboard`` (select a product and check ``Allow Sales``).

Before you finish the transaction, you of course need to set up your Plone
site to receive JVZoo server notifications.

Confirm by logging-in to http://jvzoo.com and checking to see if there were any
purchases (on ``Sellers`` tab). Also check if your received an email with
username and password for accessing your site and try to login with them.


Known issues
============

* If members stop paying for monthly or yearly subscriptions, you have to
  manually delete them from your Plone site.

* The same as above goes for any chargebacks or refunds. You have to manage
  them manually.

