import dominion_tabs
from __init__ import __version__
from zipfile import ZipFile,ZIP_DEFLATED

prefix = 'sumpfork_dominion_tabs_'
postfix = 'v' + __version__ + '.pdf'

tabs = dominion_tabs.DominionTabs()

def doit(args,main):
    args = args + ' ' + prefix+main+postfix
    args = args.split()
    fname = args[-1]
    print ':::Generating ' + fname
    tabs.main(args)
    return fname

argsets = [
    ('',''),
    ('--orientation=vertical','vertical_'),
    ('--papersize=A4','A4_'),
    ('--papersize=A4','vertical_A4_'),
    ('--size=sleeved','sleeved_'),
    ('--size=sleeved --orientation=vertical','vertical_sleeved_')
]

fnames = [doit(args[0],args[1]) for args in argsets]
print fnames

zip = ZipFile('sumpfork_dominion_tabs_v' + __version__ + '.zip','w',ZIP_DEFLATED)
for f in fnames:
    zip.write(f)
zip.close()

