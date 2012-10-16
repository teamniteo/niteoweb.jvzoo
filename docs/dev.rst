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

    $ curl -d "ccustname=JohnSmith&ccuststate=&ccustcc=&ccustemail=test@niteoweb.com&cproditem=1&cprodtitle=TestProduct&cprodtype=STANDARD&ctransaction=SALE&ctransaffiliate=affiliate@niteoweb.com&ctransamount=1000&ctranspaymentmethod=&ctransvendor=&ctransreceipt=1&cupsellreceipt=&caffitid=&cvendthru=&cverify=1EC4B66A&ctranstime=1350388651" http://localhost:8080/Plone/@@jvzoo
