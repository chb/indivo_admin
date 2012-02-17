Indivo Admin
============

The Indivo Admin is an Indivo X administrative application 
that enables administrators of an Indivo instance to create
and manage Indivo accounts and records. It is implemented 
in python as a Django application. For more information 
about the Indivo X Personally Controlled Health Record
Platform, see http://indivohealth.org, or the technical
documentation at http://docs.indivohealth.org.

Licensing
---------

Copyright (C) 2012 Children's Hospital Boston. All rights 
reserved.

This program is free software: you can redistribute it 
and/or modify it under the terms of the GNU Lesser General 
Public License as published by the Free Software Foundation, 
either version 3 of the License, or (at your option) any 
later version.

This program is distributed in the hope that it will be 
useful, but WITHOUT ANY WARRANTY; without even the implied 
warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. 
See the GNU Lesser General Public License for more details.

A copy of the GNU Lesser General Public License is located in 
the LICENSE.txt file in this repository, and at 
http://www.gnu.org/licenses/.

Prerequisites
-------------

The admin app requires valid installs of:

* Python (2.6+)
* Django (1.2+)
* Postgres (8.0+), or your preferred Django-compatible datastore
* python-lxml
* Apache, or your preferred production webserver.

Instructions for installing all of these components on Ubuntu
can be found in the 
`instructions for installing Indivo X <http://wiki.chip.org/indivo/index.php/HOWTO:_install_Indivo_X#Pre-Requisites>`_.

Setup
-----

* Copy ``settings.py.default`` to ``settings.py`` and edit:

  * ``DEFAULT_USERS``: The superusers to create when resetting the
    admin. Users are tuples of 
    ``('Full Name', 'email@address', 'username', 'password')``. 

    Alternatively, set ``CREATE_USERS`` to ``False`` to never create
    users automatically (you'll need to create them yourself,
    using something like ``python manage.py createsuperuser``).
    
  * ``INDIVO_OAUTH_CREDENTIALS``: The consumer key and secret for 
    the admin app that have been registered with an instance of
    Indivo X.
    
    .. note:: 
       You must register the admin app as a **machine_app** with your
       instance of Indivo X: this app is not a standard user app.

  * ``INDIVO_SERVER_LOCATION``: The location of the Indivo X instance
    to administer

  * ``DEFAULT_ADMIN_OWNER``: The details of the default owner who will
    be set up to own all new records until you assign a new owner.

  * ``DATABASES``: The settings for the database you want to run the admin
    against. We recommend:

    * ``ENGINE``: ``django.db.backends.postgresql_psycopg2``
    * ``NAME``: ``indivo_admin_db``, or your favorite name for the database
    * ``USER``: ``indivo`` (if on the same machine as Indivo Server, use the same DB user)
    * ``PASSWORD``: Whatever works with ``USER``.

* Create your database, if you haven't already. Something like::

  createdb -U indivo -O indivo indivo_admin_db

* Run the admin reset script::

  python manage.py reset_admin

And you should be all set! Run the admin with:

* The Django development webserver::

  python manage.py runserver 0.0.0.0:8002 (or your favorite port)

* Apache: See `our setup instructions for Indivo <http://wiki.chip.org/indivo/index.php/HOWTO:_install_Indivo_X#Running_on_Apache>`_, and do something similar.
