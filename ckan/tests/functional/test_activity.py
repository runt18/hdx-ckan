from pylons import config
from pylons.test import pylonsapp
from paste.deploy.converters import asbool
import paste.fixture
from routes import url_for
from nose import SkipTest

import ckan
from ckan.logic.action.create import package_create, user_create, group_create
from ckan.logic.action.create import follow_dataset, follow_user
from ckan.logic.action.update import package_update, resource_update
from ckan.logic.action.update import user_update, group_update
from ckan.logic.action.delete import package_delete
from ckan.tests.html_check import HtmlCheckMethods

class TestActivity(HtmlCheckMethods):
    """Test the rendering of activity streams into HTML pages.

    Activity streams are tested in detail elsewhere, this class just briefly
    tests the rendering of activity streams to HTML.

    """
    @classmethod
    def setup(cls):
        if not asbool(config.get('ckan.activity_streams_enabled', 'true')):
            raise SkipTest('Activity streams not enabled')
        ckan.tests.CreateTestData.create()
        cls.sysadmin_user = ckan.model.User.get('testsysadmin')
        cls.app = paste.fixture.TestApp(pylonsapp)

    @classmethod
    def teardown(cls):
        ckan.model.repo.rebuild_db()


    def test_user_activity(self):
        """Test user activity streams HTML rendering."""

        # Register a new user.
        user_dict = {'name': 'billybeane',
                'fullname': 'Billy Beane',
                'about': 'General Manager, Oakland Athletics',
                'email': 'billy@beane.org',
                'password': 'b1lly'}
        context = {
            'model': ckan.model,
            'session': ckan.model.Session,
            'user': self.sysadmin_user.name,
            'allow_partial_update': True,
            }
        user = user_create(context, user_dict)
        offset = url_for(controller='user', action='activity', id=user['id'])
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} signed up'.format(user['fullname']) in stripped, stripped

        # Create a new package.
        package = {
            'name' : 'baseball_stats',
            'title' : "Billy's Stats about Baseball Players",
        }
        context['user'] = user['name']
        # FIXME This test use an old way to get at the schema to
        # recreate this we need to pretend to be using the api. We
        # should not be calling package_create like this we should be
        # going via the api or package controllers
        context['api_version'] = 3
        context['ignore_auth'] = True
        package = package_create(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} created the dataset {1!s} '.format(
                user['fullname'], package['title']) in stripped, stripped

        # Add a resource to the package.
        resource = {
            'url': 'http://www.example.com',
            'description': "Chad Bradford's OBP Stats`",
            'format': 'cvs',
            'name': 'Chad Bradford Stats',
            }
        package['resources'].append(resource)
        request_data = {
                'id': package['id'],
                'resources': package['resources'],
                }
        package = package_update(context, request_data)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} added the resource {1!s} to the dataset {2!s}'.format(user['fullname'], resource['name'], package['title']) \
                in stripped, stripped

        # Update the package.
        package['title'] =  "Billy's Updated Stats about Baseball Players"
        package = package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} updated the dataset {1!s}'.format(user['fullname'], package['title']) \
                in stripped, stripped

        # Update the resource.
        resource = package['resources'][0]
        resource['name'] = 'Chad Bradford Updated Stats'
        resource = resource_update(context, resource)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} updated the resource {1!s} in the dataset {2!s}'.format(user['fullname'], resource['name'], package['title']) \
                in stripped, stripped

        # Delete the resource.
        context['allow_partial_update'] = False
        package['resources'] = []
        package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} deleted the resource {1!s} from the dataset {2!s}'.format(user['fullname'], resource['name'], package['title']) \
                in stripped, stripped

        # Follow the package.
        follow_dataset(context, {'id': package['id']})
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} started following {1!s}'.format(user['fullname'],
                package['title']) not in stripped, stripped

        # Follow another user.
        follow_user(context, {'id': 'joeadmin'})
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} started following {1!s}'.format(user['fullname'],
                'joeadmin') not in stripped, stripped

        # Create a new group.
        group = {
            'name': 'baseball-stats-group',
            'title': 'A Group for Datasets about Baseball'
            }
        context['allow_partial_update'] = True
        group = group_create(context, group)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} created the group {1!s}'.format(user['fullname'], group['title']) \
                in stripped, stripped

        # Update the group.
        group['title'] = 'updated'
        group = group_update(context, group)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} updated the group {1!s}'.format(user['fullname'], group['title']) \
                in stripped, stripped

        # Delete the group.
        group['state'] = 'deleted'
        group_update(context, group)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} deleted the group {1!s}'.format(user['fullname'], group['title']) \
                in stripped, stripped

        # Add a new tag to the package.
        tag = {'name': 'baseball'}
        package['tags'].append(tag)
        package = package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} added the tag {1!s} to the dataset {2!s}'.format(user['fullname'], tag['name'], package['title']) \
                in stripped, stripped

        # Remove the tag from the package.
        package['tags'] = []
        context['allow_partial_update'] = False
        package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} removed the tag {1!s} from the dataset {2!s}'.format(user['fullname'], tag['name'], package['title']) \
                in stripped, stripped

        # Add an extra to the package.
        package['extras'].append({'key': 'quality', 'value': '10000'})
        package = package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} added the extra "{1!s}" to the dataset {2!s}'.format(user['fullname'], 'quality', package['title']) \
                in stripped, stripped

        # Update the extra.
        package['extras'][0]['value'] = 'updated'
        package = package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} changed the extra "{1!s}" of the dataset {2!s}'.format(user['fullname'], 'quality', package['title']) \
                in stripped, stripped

        # Delete the extra.
        del package['extras'][0]
        package = package_update(context, package)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} deleted the extra "{1!s}" from the dataset {2!s}'.format(user['fullname'], 'quality', package['title']) \
                in stripped, stripped

        # Delete the package.
        # we need to get round the delete permission
        context['ignore_auth'] = True
        package_delete(context, package)
        del context['ignore_auth']
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} deleted the dataset {1!s}'.format(user['fullname'], package['title']) \
                in stripped, stripped

        # Update the user's profile.
        user['about'] = ''
        user_update(context, user)
        result = self.app.get(offset, status=200)
        stripped = self.strip_tags(result)
        assert '{0!s} updated their profile'.format(user['fullname']) \
                in stripped, stripped

        # By now we've created >15 activities, but only the latest 15 should
        # appear on the page.
        result = self.app.get(offset, status=200)
        assert result.body.count('<span class="actor">') \
                == 15, result.body.count('<span class="actor">')

        # The user's dashboard page should load successfully and have the
        # latest 15 activities on it.
        offset = url_for(controller='user', action='dashboard')
        extra_environ = {'Authorization':
                str(ckan.model.User.get('billybeane').apikey)}
        result = self.app.post(offset, extra_environ=extra_environ,
                status=200)
        assert result.body.count('<span class="actor">') == 15, \
            result.body.count('<span class="actor">')
