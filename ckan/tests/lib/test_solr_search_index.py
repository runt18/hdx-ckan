from datetime import datetime
import hashlib
import socket
import solr
from pylons import config
from ckan import model
import ckan.lib.search as search
from ckan.tests import TestController, CreateTestData, setup_test_search_index, is_search_supported

class TestSolrConfig(TestController):
    """
    Make sure that solr is enabled for this ckan instance.
    """
    def test_solr_url_exists(self):
        if not is_search_supported():
            from nose import SkipTest
            raise SkipTest("Search not supported")

        conn = search.make_connection()
        try:
            # solr.SolrConnection.query will throw a socket.error if it
            # can't connect to the SOLR instance
            q = conn.query("*:*", rows=1)
            conn.close()
        except socket.error, e:
            if not config.get('solr_url'):
                raise AssertionError("Config option 'solr_url' needs to be defined in this CKAN's development.ini. Default of {0!s} didn't work: {1!s}".format(search.DEFAULT_SOLR_URL, e))
            else:
                raise AssertionError('SOLR connection problem. Connection defined in development.ini as: solr_url={0!s} Error: {1!s}'.format(config['solr_url'], e))


class TestSolrSearch:
    @classmethod
    def setup_class(cls):
        setup_test_search_index()
        CreateTestData.create_search_test_data()
        cls.solr = search.make_connection()
        cls.fq = " +site_id:\"{0!s}\" ".format(config['ckan.site_id'])
        search.rebuild()

    @classmethod
    def teardown_class(cls):
        model.repo.rebuild_db()
        cls.solr.close()
        search.index_for('Package').clear()

    def test_0_indexing(self):
        """
        Make sure that all packages created by CreateTestData.create_search_test_data
        have been added to the search index.
        """
        results = self.solr.query('*:*', fq=self.fq)
        assert len(results) == 6, len(results)

    def test_1_basic(self):
        results = self.solr.query('sweden', fq=self.fq)
        assert len(results) == 2
        result_names = [r['name'] for r in results]
        assert 'se-publications' in result_names
        assert 'se-opengov' in result_names

