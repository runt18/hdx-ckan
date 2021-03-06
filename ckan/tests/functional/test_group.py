import re

from nose.tools import assert_equal
import mock

import ckan.model as model
import ckan.lib.search as search

from ckan.tests import setup_test_search_index
from ckan import plugins
from ckan.lib.create_test_data import CreateTestData
from ckan.logic import get_action
from ckan.tests import *
from base import FunctionalTestCase
from ckan.tests import is_search_supported


class TestGroup(FunctionalTestCase):

    @classmethod
    def setup_class(self):
        search.clear()
        model.Session.remove()
        CreateTestData.create()

        # reduce extraneous logging
        from ckan.lib import activity_streams_session_extension
        activity_streams_session_extension.logger.level = 100

    @classmethod
    def teardown_class(self):
        model.repo.rebuild_db()

    def test_sorting(self):
        model.repo.rebuild_db()

        testsysadmin = model.User(name=u'testsysadmin')
        testsysadmin.sysadmin = True
        model.Session.add(testsysadmin)

        pkg1 = model.Package(name="pkg1")
        pkg2 = model.Package(name="pkg2")
        model.Session.add(pkg1)
        model.Session.add(pkg2)

        CreateTestData.create_groups([{'name': "alpha",
                                       'title': "Alpha",
                                       'packages': []},
                                      {'name': "beta",
                                       'title': "Beta",
                                       'packages': ["pkg1", "pkg2"]},
                                      {'name': "delta",
                                       'title': 'Delta',
                                       'packages': ["pkg1"]},
                                      {'name': "gamma",
                                       'title': "Gamma",
                                       'packages': []}],
                                     admin_user_name='testsysadmin')

        context = {'model': model, 'session': model.Session,
                   'user': 'testsysadmin', 'for_view': True,
                   'with_private': False}
        data_dict = {'all_fields': True}
        results = get_action('group_list')(context, data_dict)
        assert results[0]['name'] == u'alpha', results[0]['name']
        assert results[-1]['name'] == u'gamma', results[-1]['name']

        # Test title forward
        data_dict = {'all_fields': True, 'sort': 'title asc'}
        results = get_action('group_list')(context, data_dict)
        assert results[0]['name'] == u'alpha', results[0]['name']
        assert results[-1]['name'] == u'gamma', results[-1]['name']

        # Test title reverse
        data_dict = {'all_fields': True, 'sort': 'title desc'}
        results = get_action('group_list')(context, data_dict)
        assert results[0]['name'] == u'gamma', results[0]['name']
        assert results[-1]['name'] == u'alpha', results[-1]['name']

        # Test name reverse
        data_dict = {'all_fields': True, 'sort': 'name desc'}
        results = get_action('group_list')(context, data_dict)
        assert results[0]['name'] == u'gamma', results[0]['name']
        assert results[-1]['name'] == u'alpha', results[-1]['name']

        # Test packages reversed
        data_dict = {'all_fields': True, 'sort': 'packages desc'}
        results = get_action('group_list')(context, data_dict)
        assert results[0]['name'] == u'beta', results[0]['name']
        assert results[1]['name'] == u'delta', results[1]['name']

        # Test packages forward
        data_dict = {'all_fields': True, 'sort': 'packages asc'}
        results = get_action('group_list')(context, data_dict)
        assert results[-2]['name'] == u'delta', results[-2]['name']
        assert results[-1]['name'] == u'beta', results[-1]['name']

        # Default ordering for packages
        data_dict = {'all_fields': True, 'sort': 'packages'}
        results = get_action('group_list')(context, data_dict)
        assert results[0]['name'] == u'beta', results[0]['name']
        assert results[1]['name'] == u'delta', results[1]['name']

    def test_read_non_existent(self):
        name = u'group_does_not_exist'
        offset = url_for(controller='group', action='read', id=name)
        res = self.app.get(offset, status=404)


class TestEdit(FunctionalTestCase):

    @classmethod
    def setup_class(self):
        setup_test_search_index()
        model.Session.remove()
        CreateTestData.create()
        self.groupname = u'david'
        self.packagename = u'testpkg'
        model.repo.new_revision()
        model.Session.add(model.Package(name=self.packagename))
        model.repo.commit_and_remove()

    @classmethod
    def teardown_class(self):
        model.Session.remove()
        model.repo.rebuild_db()
        model.Session.remove()

    def test_0_not_authz(self):
        offset = url_for(controller='group', action='edit', id=self.groupname)
        # 401 gets caught by repoze.who and turned into redirect
        res = self.app.get(offset, status=[302, 401])
        res = res.follow()
        assert res.request.url.startswith('/user/login')

    def test_edit_non_existent(self):
        name = u'group_does_not_exist'
        offset = url_for(controller='group', action='edit', id=name)
        res = self.app.get(offset, status=404)


class TestNew(FunctionalTestCase):
    groupname = u'david'

    @classmethod
    def setup_class(self):
        model.Session.remove()
        CreateTestData.create()

        self.packagename = u'testpkg'
        model.repo.new_revision()
        model.Session.add(model.Package(name=self.packagename))
        model.repo.commit_and_remove()

    @classmethod
    def teardown_class(self):
        model.Session.remove()
        model.repo.rebuild_db()
        model.Session.remove()

    def test_1_not_authz(self):
        offset = url_for(controller='group', action='new')
        # 401 gets caught by repoze.who and turned into redirect
        res = self.app.get(offset, status=[302, 401])
        res = res.follow()
        assert res.request.url.startswith('/user/login')

    def test_new_bad_param(self):
        offset = url_for(controller='group', action='new',
                         __bad_parameter='value')
        res = self.app.post(offset, {'save': '1'},
                            extra_environ={'REMOTE_USER': 'testsysadmin'},
                            status=400)
        assert 'Integrity Error' in res.body


class TestRevisions(FunctionalTestCase):
    @classmethod
    def setup_class(self):
        model.Session.remove()
        CreateTestData.create()
        self.name = u'revisiontest1'

        # create pkg
        self.description = [u'Written by Puccini', u'Written by Rossini',
                            u'Not written at all', u'Written again',
                            u'Written off']
        rev = model.repo.new_revision()
        self.grp = model.Group(name=self.name)
        self.grp.description = self.description[0]
        model.Session.add(self.grp)
        model.setup_default_user_roles(self.grp)
        model.repo.commit_and_remove()

        # edit pkg
        for i in range(5)[1:]:
            rev = model.repo.new_revision()
            grp = model.Group.by_name(self.name)
            grp.description = self.description[i]
            model.repo.commit_and_remove()

        self.grp = model.Group.by_name(self.name)

    @classmethod
    def teardown_class(self):
        self.purge_packages([self.name])
        model.repo.rebuild_db()

    def test_2_atom_feed(self):
        offset = url_for(controller='group', action='history',
                         id=self.grp.name)
        offset = "{0!s}?format=atom".format(offset)
        res = self.app.get(offset)
        assert '<feed' in res, res
        assert 'xmlns="http://www.w3.org/2005/Atom"' in res, res
        assert '</feed>' in res, res


class TestMemberInvite(FunctionalTestCase):
    @classmethod
    def setup_class(self):
        model.Session.remove()
        model.repo.rebuild_db()

    def teardown(self):
        model.repo.rebuild_db()

    @mock.patch('ckan.lib.mailer.mail_user')
    def test_member_new_invites_user_if_received_email(self, mail_user):
        user = CreateTestData.create_user('a_user', sysadmin=True)
        group_name = 'a_group'
        CreateTestData.create_groups([{'name': group_name}], user.name)
        group = model.Group.get(group_name)
        url = url_for(controller='group', action='member_new', id=group.id)
        email = 'invited_user@mailinator.com'
        role = 'member'

        params = {'email': email, 'role': role}
        res = self.app.post(url, params,
                            extra_environ={'REMOTE_USER': str(user.name)})

        users = model.User.by_email(email)
        assert len(users) == 1, users
        user = users[0]
        assert user.email == email, user
        assert group.id in user.get_group_ids(capacity=role)
