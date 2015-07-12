'''
Created on July 2nd, 2015

@auth
'''
import ckan.plugins as plugins
# import ckan.plugins.toolkit as toolkit

import ckanext.hdx_user_extra.actions.create as create
import ckanext.hdx_user_extra.actions.get as get
import ckanext.hdx_user_extra.actions.update as update


class HDX_User_ExtraPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        pass
        # toolkit.add_template_directory(config_, 'templates')
        # toolkit.add_public_directory(config_, 'public')
        # toolkit.add_resource('fanstatic', 'hdx_user_extra')

    def get_actions(self):
        return {
            'user_extra_create': create.user_extra_create,
            'user_extra_show': get.user_extra_show,
            'user_extra_update': update.user_extra_update
        }
