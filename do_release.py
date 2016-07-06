import domdiv
from __init__ import __version__
from zipfile import ZipFile, ZIP_DEFLATED

prefix = 'generated/sumpfork_dominion_tabs_'
postfix = 'v' + __version__ + '.pdf'


def doit(args, main):
    args = args + ' ' + prefix + main + postfix
    args = args.split()
    fname = args[-1]
    print ':::Generating ' + fname
    domdiv.main(args, '.')
    return fname


argsets = [
    ('', ''), ('--orientation=vertical', 'vertical_'),
    ('--papersize=A4', 'A4_'),
    ('--papersize=A4 --orientation=vertical', 'vertical_A4_'),
    ('--size=sleeved', 'sleeved_'),
    ('--size=sleeved --orientation=vertical', 'vertical_sleeved_')
]
additional = ['--expansion_dividers']

fnames = [doit(args[0] + ' ' + ' '.join(additional), args[1])
          for args in argsets]
print fnames

zip = ZipFile('generated/sumpfork_dominion_tabs_v' + __version__ + '.zip', 'w',
              ZIP_DEFLATED)
for f in fnames:
    zip.write(f)
zip.close()
