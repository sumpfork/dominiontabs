import os
from zipfile import ZIP_DEFLATED, ZipFile

import domdiv
import domdiv.main

gen_dir = "sumpfork_dividers"
prefix = f"{gen_dir}/sumpfork_dominion_tabs_"
postfix = "v" + domdiv.__version__ + ".pdf"
argsets = [
    ("", ""),
    ("--orientation=vertical", "vertical_"),
    ("--papersize=A4", "A4_"),
    ("--papersize=A4 --orientation=vertical", "vertical_A4_"),
    ("--size=sleeved", "sleeved_"),
    ("--size=sleeved --orientation=vertical", "vertical_sleeved_"),
]
additional = ["--expansion-dividers", "--tab-artwork-resolution=300"]


def run_generator(args, main):
    args = args + " --outfile " + prefix + main + postfix
    args = args.split()
    fname = args[-1]
    print(args)
    print(":::Generating " + fname)
    options = domdiv.main.parse_opts(args)
    options = domdiv.main.clean_opts(options)
    domdiv.main.generate(options)
    return fname


def make_bgg_release():
    if not os.path.exists(gen_dir):
        print(f"Making dir '{gen_dir}'")
        os.mkdir(gen_dir)

    fnames = [
        run_generator(args[0] + " " + " ".join(additional), args[1]) for args in argsets
    ]
    print(fnames)

    with ZipFile(
        f"{gen_dir}/sumpfork_dominion_tabs_v" + domdiv.__version__ + ".zip",
        "w",
        ZIP_DEFLATED,
        compresslevel=9,
    ) as zip:
        for f in fnames:
            zip.write(f)
