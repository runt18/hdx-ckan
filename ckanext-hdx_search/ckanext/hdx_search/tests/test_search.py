'''
Created on September 18, 2014

@author: Marianne, Alex, Dan


'''
import logging as logging
import ckan.lib.helpers as h
import ckan.model as model

import ckanext.hdx_theme.tests.hdx_test_base as hdx_test_base

log = logging.getLogger(__name__)


class TestHDXSearch(hdx_test_base.HdxBaseTest):

    @classmethod
    def _load_plugins(cls):
        hdx_test_base.load_plugin('hdx_search hdx_theme')

    def test_search(self):
        user = model.User.by_name('tester')
        offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health'})
        assert '200' in response.status

    def test_indicators(self):
    	user = model.User.by_name('tester')
    	offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health', 'ext_indicator':1})
        assert '200' in response.status

    def test_datasets(self):
    	user = model.User.by_name('tester')
    	offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health', 'ext_indicator':0})
        assert '200' in response.status

	def test_features(self):
		user = model.User.by_name('tester')
    	offset = h.url_for(
            controller='ckanext.hdx_search.controllers.search_controller:HDXSearchController', action='search')
        response = self.app.get(offset, params={'q': 'health', 'ext_feature':1})
        assert '200' in response.status    