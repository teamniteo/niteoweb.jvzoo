.. _tips_and_tricks:

=============
Tips & Tricks
=============

JVZoo IPN API documentation
===========================

Available at http://support.jvzoo.com/Knowledgebase/Article/View/17/0/jvzipn.


Mocked request
==============

If you want to mock a request from JVZoo in your local development environment,
run something along these lines:

.. sourcecode:: bash

    TODO: replace this with jvzoo's request
    $ curl -d "buyer_email=test@niteoweb.com&buyer_name=John&buyer_surname=Smith&product_id=1&product_name=TestProduct&affiliate_username=affiliate@niteoweb.com&c2s_transaction_id=1&purchase_date=2012/01/01&purchase_time=00:00:00&secretkey=secret&acquirer_transaction_id=123&checksum=B457E9433F98EF22AA9DD9BA4A5E2B16" http://localhost:8080/Plone/@@jvzoo
