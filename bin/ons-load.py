import os

data_path = os.path.expanduser('~/ckan-local/data/')

def load_month(month, year):
    assert month < 13
    assert year > 2000
    data_filepath = os.path.join(data_path, 'ons_hub_{0!s}_{1:02d}.xml'.format(year, month))
    try:
        cmd = 'paster db load-onshub {0!s}'.format((data_filepath))
        print cmd
        response = os.system(cmd)
        print '\n{0!s} {1!r}'.format(data_filepath, response)
    except Exception, e:
        print '\nEXCEPTION {0!s} {1!r}'.format(data_filepath, e.args)


load_month(1, 2010)
for year in (2009, 2008, 2007, 2006, 2005, 2004):
    for month in range(12):
        load_month(month+1, year)

