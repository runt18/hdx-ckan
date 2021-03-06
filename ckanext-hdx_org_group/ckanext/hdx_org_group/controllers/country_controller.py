'''
Created on Jan 13, 2015

@author: alexandru-m-g
'''
import json
import collections

import logging
import datetime as dt

import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
import ckan.common as common
import ckan.controllers.group as group
import ckan.lib.helpers as h

import ckanext.hdx_search.controllers.search_controller as search_controller
import ckanext.hdx_theme.helpers.top_line_items_formatter as formatters
import ckanext.hdx_org_group.dao.indicator_access as indicator_access

from ckan.controllers.api import CONTENT_TYPES

render = base.render
abort = base.abort
NotFound = logic.NotFound
NotAuthorized = logic.NotAuthorized
get_action = logic.get_action
c = common.c
request = common.request
_ = common._
response = common.response

log = logging.getLogger(__name__)
OrderedDict = collections.OrderedDict

group_type = 'group'

indicators_4_charts_list = [
    ('PVH140', 'mdgs'),
    ('PVN010', 'fao-foodsec'),
    ('PVW010', 'mdgs'),
    ('PVF020', 'faostat3'),
    ('PSE160', 'data.undp.org'),
    ('PCX051', 'mdgs'),
    ('PVE130', 'mdgs'),
    ('PCX060', 'mdgs'),
    ('RW002', 'RW'),
    ('PVE110', 'data.undp.org'),
    ('PVN050', 'mdgs'),
    ('PVN070', 'mdgs'),
    ('PVW040', 'mdgs')
]

indicators_4_charts = [el[0] for el in indicators_4_charts_list]

indicators_4_top_line_list = [
    ('PSP120', 'world-bank'),
    ('PSP090', 'world-bank'),
    ('PSE220', 'data.undp.org'),
    ('PSE030', 'world-bank'),
    ('CG300', 'world-bank')
]
indicators_4_top_line = [el[0] for el in indicators_4_top_line_list]


class CountryController(group.GroupController, search_controller.HDXSearchController):
    def country_read(self, id):
        self.get_country(id)

        country_code = c.group_dict.get('name', id)

        if self._is_facet_only_request():
            c.full_facet_info = self.get_dataset_search_results(country_code)
            c.full_facet_info.get('facets', {}).pop('vocab_Topics', {})
            response.headers['Content-Type'] = CONTENT_TYPES['json']
            return json.dumps(c.full_facet_info)
        else:

            self.get_dataset_results(country_code)
            # c.hdx_group_activities = self.get_activity_stream(country_uuid)

            c.full_facet_info = self.get_dataset_search_results(country_code)
            vocab_topics_list = c.full_facet_info.get(
                'facets', {}).pop('vocab_Topics', {}).get('items', [])
            c.cont_browsing = self.get_cont_browsing(
                c.group_dict, vocab_topics_list)

            c.show_overview = len(c.top_line_data_list) > 0 or len(c.chart_data_list) > 0

            result = render('country/country.html')

            return result

    def get_country(self, id):
        if group_type != self.group_type:
            abort(404, _('Incorrect group type'))

        context = {'model': model, 'session': model.Session,
                   'user': c.user or c.author,
                   'schema': self._db_to_form_schema(group_type=group_type),
                   'for_view': True}
        data_dict = {'id': id}

        try:
            context['include_datasets'] = False
            c.group_dict = self._action(
                'hdx_light_group_show')(context, data_dict)
            # c.group = context['group']

        except NotFound:
            abort(404, _('Group not found'))
        except NotAuthorized:
            abort(401, _('Unauthorized to read group %s') % id)

    def get_dataset_results(self, country_id):

        top_line_dao = indicator_access.IndicatorAccess(
            country_id, indicators_4_top_line_list, {'periodType': 'LATEST_YEAR_BY_COUNTRY'})

        top_line_results = top_line_dao.fetch_indicator_data_from_cps()
        top_line_data = top_line_results.get('results', [])

        if not top_line_data:
            log.warn(
                'No top line numbers found for country: {0}'.format(country_id))
            top_line_data = []
        sorted_top_line_data = sorted(top_line_data,
                                      key=lambda x: indicators_4_top_line.index(x['indicatorTypeCode']))
        for el in sorted_top_line_data:
            el['formatted_value'] = formatters.format_decimal_number(
                el['value'], 2)

        c.top_line_data_list = sorted_top_line_data

        top_line_ind_codes = [el['indicatorTypeCode']
                              for el in sorted_top_line_data]

        chart_dao = indicator_access.IndicatorAccess(
            country_id, indicators_4_charts_list, {'sorting': 'INDICATOR_TYPE_ASC'})

        chart_dao.fetch_indicator_data_from_cps()
        chart_dataseries_dict = chart_dao.get_structured_data_from_cps()
        if not chart_dataseries_dict:
            log.warn('No chart data found for country: {0}'.format(country_id))
            chart_dataseries_dict = {}

        # We can do the steps below because, in this case,
        # we know that each indicator type has only one source
        chart_data_dict = {}
        for key, value in chart_dataseries_dict.iteritems():
            try:
                # we're taking the first (and only) soruce
                new_value = value.itervalues().next()
                chart_data_dict[key] = new_value
            except Exception, e:
                log.warning("Exception while iterating dataseries data: " + e)


        # for code in chart_data_dict.keys():
        #     chart_data_dict[code] = sorted(chart_data_dict[code], key=lambda x: x.get('datetime', None))

        chart_data_list = []
        for code in indicators_4_charts:
            if code in chart_data_dict and len(chart_data_list) < 5:
                chart_data_list.append(chart_data_dict[code])

        chart_ind_codes = [chart['code'] for chart in chart_data_list]
        shown_dataseries_codes = [(el, '') for el in top_line_ind_codes + chart_ind_codes]
        shown_dataseries_dao = indicator_access.IndicatorAccess(country_id, shown_dataseries_codes)

        indic_extra_dict = shown_dataseries_dao.fetch_indicator_data_from_ckan()

        for chart in chart_data_list:
            code = chart['code']
            chart_extra = indic_extra_dict.get(code, None)
            chart['data'] = json.dumps(chart['data'])
            if chart_extra:
                chart['datasetLink'] = chart_extra.get('datasetLink')
                chart['datasetUpdateDate'] = chart_extra.get(
                    'datasetUpdateDate')

        c.chart_data_list = chart_data_list

        # updating the top line info with links and dates
        for el in sorted_top_line_data:
            cps_time = el.get('time', '')
            if cps_time:
                el['datasetUpdateDate'] = \
                    dt.datetime.strptime(cps_time, '%Y-%m-%d').strftime('%b %d, %Y')

            top_line_extra = indic_extra_dict.get(
                el['indicatorTypeCode'], None)
            if top_line_extra:
                el['datasetLink'] = top_line_extra.get('datasetLink')
                # el['datasetUpdateDate'] = top_line_extra.get(
                #     'datasetUpdateDate')

    # def get_activity_stream(self, country_uuid):
    #     context = {'model': model, 'session': model.Session,
    #                'user': c.user or c.author,
    #                'for_view': True}
    #     act_data_dict = {
    #         'id': country_uuid, 'group_uuid': country_uuid, 'limit': 7}
    #     result = get_action(
    #         'hdx_get_group_activity_list')(context, act_data_dict)
    #     return result

    def get_cont_browsing(self, group_dict, vocab_topics_list):
        cont_browsing_dict = {
            'websites': self._process_websites(group_dict),
            'followers': self._get_followers(group_dict['id']),
            'topics': self._get_topics(vocab_topics_list)

        }
        return cont_browsing_dict

    def _process_websites(self, group_dict):
        site_list = []
        if 'extras' in group_dict:
            extras_dict = {el['key']: el['value']
                           for el in group_dict['extras'] if el['state'] == u'active'}

            if 'relief_web_url' in extras_dict:
                site_list.append(
                    {'name': _('ReliefWeb'), 'url': extras_dict['relief_web_url']})
            site_list.append({'name': _('UNOCHA'), 'url': 'http://unocha.org'})
            if 'hr_info_url' in extras_dict:
                site_list.append(
                    {'name': _('HumanitarianResponse'), 'url': extras_dict['hr_info_url']})
            site_list.append(
                {'name': _('OCHA Financial Tracking Service'),
                 'url': 'http://fts.unocha.org/'}
            )

        return site_list

    def _get_followers(self, country_id):
        followers = get_action('group_follower_list')(
            {'ignore_auth': True}, {'id': country_id})
        followers_list = [
            {
                'name': f['display_name'],
                'url': h.url_for(controller='user', action='read', id=f['name'])
            } for f in followers
            ]

        return followers_list

    def _get_topics(self, vocab_topics_list):
        topic_list = [
            {
                'name': topic.get('name', ''),
                'url': h.url_for(controller='package', action='search', vocab_Topics=topic.get('name')),
                'count': topic.get('count', 0)
            } for topic in vocab_topics_list
        ]

        topic_list.sort(key=lambda x: x.get('count', 0), reverse=True)

        return topic_list

    def get_dataset_search_results(self, country_code):
        package_type = 'dataset'

        suffix = '#datasets-section'

        params_nopage = {
            k: v for k, v in request.params.items() if k != 'page'}

        def pager_url(q=None, page=None):
            params = params_nopage
            params['page'] = page
            return h.url_for('country_read', id=country_code, **params) + suffix

        fq = 'groups:"{0}"'.format(country_code)
        facets = {
            'vocab_Topics': _('Topics')
        }
        full_facet_info = self._search(package_type, pager_url, additional_fq=fq, additional_facets=facets)
        locations = full_facet_info.get('facets', {}).get('groups', {}).get('items', [])
        locations[:] = [loc for loc in locations if loc.get('name', '') != country_code]

        c.other_links['current_page_url'] = h.url_for('country_read', id=country_code)

        return full_facet_info
