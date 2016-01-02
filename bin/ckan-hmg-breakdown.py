import os

import loadconfig
path = os.path.abspath('development.ini')
loadconfig.load_config(path)

import ckan.model as model
from ckan.lib.dumper import SimpleDumper


q_packages = model.Session.query(model.Package)
print 'Total packages: {0:d}'.format(q_packages.count())

active = model.State.ACTIVE
q_active = q_packages.filter_by(state=active)
print 'Active packages: {0:d}'.format(q_active.count())

q_group = q_packages.join('groups').filter(model.Group.name==u'ukgov')
print 'Packages in group ukgov: {0:d}'.format(q_group.count())

print_those_not_in_group = True
if print_those_not_in_group:
    in_group = [pkg.name for pkg in q_group]
    not_in_group = []

pkgs_by_source = {}
for pkg in q_packages:
    if pkg.extras.get('national_statistic', None) == 'yes':
        print pkg.extras.get('national_statistic'), pkg.extras.get('import_source', u'')
    if pkg.extras.has_key('import_source'):
        source = pkg.extras['import_source']
        if '-' in source:
            source = source[:source.find('-')]
    elif pkg.extras.has_key('co_id'):
        source = 'CO Spreadsheet Dec 2009'
    elif pkg.extras.has_key('update frequency'):
        source = 'DATA4NR Dec 2009'
    elif pkg.extras.get('external_reference', u'').startswith('DATA4NR'):
        source = 'DATA4NR Jan 2010'
    elif pkg.extras.get('external_reference', u'') == u'ONSHUB':
        source = 'ONS'
    else:
        source = 'manual'

    if not pkgs_by_source.has_key(source):
        pkgs_by_source[source] = []
    pkgs_by_source[source].append(pkg)

    if print_those_not_in_group:
        if pkg.name not in in_group:
            not_in_group.append(pkg.name)
if print_those_not_in_group:
    if not_in_group:
        print ' Not in the group: {0!s}'.format(', '.join(not_in_group))
    
for source, pkgs in pkgs_by_source.items():
    print 'Source: {0!s} \t items: {1:d}'.format(source, len(pkgs))

##ons_pkgs_titles = []
##for pkg in pkgs_by_source['ONS']:
##    ons_pkgs_titles.append('%s (%s)' % (pkg.title, len(pkg.resources)))
##ons_pkgs_titles.sort()
##print 'ONS Packages:'
##for title in ons_pkgs_titles:
##    print title
