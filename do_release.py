import domdiv
import domdiv.main
from zipfile import ZipFile, ZIP_DEFLATED

prefix = "generated/sumpfork_dominion_tabs_"
postfix = "v" + domdiv.__version__ + ".pdf"


def doit(args, main):
    args = args + " --outfile " + prefix + main + postfix
    args = args.split()
    fname = args[-1]
    print(args)
    print(":::Generating " + fname)
    options = domdiv.main.parse_opts(args)
    options = domdiv.main.clean_opts(options)
    domdiv.main.generate(options)
    return fname


argsets = [
    ("", ""),
    ("--orientation=vertical", "vertical_"),
    ("--papersize=A4", "A4_"),
    ("--papersize=A4 --orientation=vertical", "vertical_A4_"),
    ("--size=sleeved", "sleeved_"),
    ("--size=sleeved --orientation=vertical", "vertical_sleeved_"),
]
additional = ["--expansion-dividers"]

fnames = [doit(args[0] + " " + " ".join(additional), args[1]) for args in argsets]
print(fnames)

zip = ZipFile(
    "generated/sumpfork_dominion_tabs_v" + domdiv.__version__ + ".zip",
    "w",
    ZIP_DEFLATED,
)
for f in fnames:
    zip.write(f)
zip.close()
