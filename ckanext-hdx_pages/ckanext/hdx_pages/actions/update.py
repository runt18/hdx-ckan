import datetime

import ckan.logic as logic

import ckanext.hdx_pages.model as pages_model
import ckanext.hdx_pages.helpers.dictize as dictize
import ckanext.hdx_pages.actions.validation as validation

NotFound = logic.NotFound


def page_update(context, data_dict):

    logic.check_access('page_update', context, data_dict)

    validation.page_name_validator(data_dict, context)

    try:
        session = context['session']
        page = pages_model.Page.get(id=data_dict['id'])
        if page is None:
            raise NotFound

        page.name = data_dict['name']
        page.title = data_dict['title']
        page.description = data_dict.get('description')
        page.type = data_dict.get('type')
        page.state = data_dict.get('state')
        page.sections = data_dict.get('sections')
        page.modified = datetime.datetime.now()

        session.add(page)
        session.commit()
        return dictize.page_dictize(page)
    except Exception as e:
        ex_msg = e.message if hasattr(e, 'message') else str(e)
        message = 'Something went wrong while processing the request: {0}'.format(ex_msg)
        raise logic.ValidationError({'message': message}, error_summary=message)
