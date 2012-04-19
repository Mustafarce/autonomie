# -*- coding: utf-8 -*-
# * File Name : conftest.py
#
# * Copyright (C) 2010 Gaston TJEBBES <g.t@majerti.fr>
# * Company : Majerti ( http://www.majerti.fr )
#
#   This software is distributed under GPLV3
#   License: http://www.gnu.org/licenses/gpl-3.0.txt
#
# * Creation Date : 12-03-2012
# * Last Modified :
#
# * Project :
#
import os

here = os.path.dirname(__file__)

def coerce_datas(settings, prefix, here=None):
    """
        get the test db settings as a dict and format them
    """
    options = dict((key[len(prefix):], settings[key])
                for key in settings if key.startswith(prefix))
    if here:
        options['sampledb'] = os.path.join(here, options['sampledb'])
        options['sampledatas'] = os.path.join(here, options['sampledatas'])
        options['updatedir'] = os.path.join(here, options['updatedir'])
    return options

def launch_cmd(cmd):
    """
        Main entry to launch os commands
    """
    print "Launching : %s" % cmd
    os.system(cmd)

def create_sql_user(options):
    """
        Create the sql test user
    """
    launch_cmd("echo 'CREATE USER {user}@localhost;' | {mysql_cmd}".format(
                                                                **options))

def create_test_db(options):
    """
        Create the test database and grant rights
    """
    launch_cmd("echo 'CREATE DATABASE IF NOT EXISTS `{db}` character \
set utf8;' | {mysql_cmd}".format(**options))

def grant_user(options):
    """
        grant privileges on the test db to the test user
    """
    launch_cmd("echo 'GRANT ALL PRIVILEGES on {db}.* to {user}@localhost \
identified by \"{password}\"; \
FLUSH PRIVILEGES;' | {mysql_cmd}".format(**options))

def dump_sample(options):
    """
        dump sample datas in our test database
    """
    launch_cmd("{mysql_cmd} {db} < {sampledb}".format(**options))
    launch_cmd("{mysql_cmd} {db} < {sampledatas}".format(**options))


def drop_db(options):
    """
        drop the test database
    """
    cmd = "echo 'drop database if exists {db};' | {mysql_cmd}".format(**options)
    launch_cmd(cmd)

def drop_sql_datas(settings, prefix):
    """
        Drop all the test db created stuff
    """
    print "Dropping test datas : keeping it clean"
    options = coerce_datas(settings, prefix)
    drop_db(options)

def update_database(options, fpath):
    """
        update database with the given sql file
    """
    options['updatefile'] = fpath
    launch_cmd("{mysql_cmd} {db} < {updatefile}".format(**options))

def initialize_test_database(settings, prefix, here):
    """
        dump sample datas as a test database
    """
    print "Initializing test database"
    options = coerce_datas(settings, prefix, here)
    create_sql_user(options)
    create_test_db(options)
    grant_user(options)
    dump_sample(options)
    for fname in os.listdir(options['updatedir']):
        update_database(options, os.path.join(options['updatedir'], fname))

def pytest_sessionstart():
    """
        Py.test setup
    """
    from py.test import config

    # Only run database setup on master (in case of xdist/multiproc mode)
    if not hasattr(config, 'slaveinput'):
        from autonomie.models import initialize_sql
        from pyramid.config import Configurator
        from paste.deploy.loadwsgi import appconfig
        from sqlalchemy import engine_from_config

        settings = appconfig('config:' + os.path.join(here,
                                                      'test.ini'),
                             "autonomie")
        initialize_test_database(settings, "testdb.", here)
        engine = engine_from_config(settings, prefix='sqlalchemy.')

        print 'Creating the tables on the test database %s' % engine

        config = Configurator(settings=settings)
        initialize_sql(engine)
        from autonomie.models.model import *

def pytest_sessionfinish():
    """
        py.test teardown
    """
    from py.test import config
    if not hasattr(config, 'slaveinput'):
        from paste.deploy.loadwsgi import appconfig
        settings = appconfig('config:' + os.path.join(here,
                                                      'test.ini'),
                             "autonomie")
        drop_sql_datas(settings, 'testdb.')
        from autonomie.tests.base import TMPDIR
        launch_cmd('rm -rf "%s"' % TMPDIR)
