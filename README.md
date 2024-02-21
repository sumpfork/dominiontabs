# Dominion Divider Generation

![Tests](https://github.com/sumpfork/dominiontabs/actions/workflows/lint_and_test.yml/badge.svg)

## Introduction

This is a script and library to generate card dividers for storing cards for the game [Dominion](https://boardgamegeek.com/boardgame/36218/dominion). If you are just looking go generate some dominion dividers, there is no need to install this script as I host a [live version of this generator code](http://domdiv.bgtools.net/). However, if you want to use arguments that I don't expose on that page, or change the code, or contribute to the project the full generation code (not the web interface or the fonts) is included here, and contributions are more than welcome.

Again, to generate tabs go to the **[Online Generator](http://domdiv.bgtools.net/)**.

## Installation

If you do need to install the package locally (the script provides a lot more options than the web-based generator), a simple `pip install domdiv` should suffice, providing a command by the name of `dominion_dividers`. However, see the note under Prerequisites->Fonts below as the default install will fall back on a font that doesn't match the cards (though most people don't notice). Run `dominion_dividers <outfile>` to get a pdf of all dividers with the default options, or run `dominion_dividers --help` to see the (extensive) list of options.

Linux only: to ensure the dividers are generated sorted by correct alphabetical order in your selected language, you have to generate the appropriate locale on your system. Run `sudo apt-get -y install locales`, followed by `sudo locale-gen xx_XX.UTF-8`, where `xx_XX` is one of the following: `cs_CZ`, `de_DE`, `en_US`, `es_ES`, `fr_FR`, `it_IT`, `nl_NL` (according to your selected language). In Windows OS this step is not necessary.


## Documentation

The script has an extensive set of options that are relatively well documented via `dominion_dividers --help`. Some are hard to describe unless you see output samples, so we recommend running the script with various options to see which configuration you like. The help output is replicated [here](https://github.com/sumpfork/dominiontabs/wiki/Documentation-%28Script-Options%29) for reference.

## Translations

When changing any of the [card database files](card_db_src) you should run the language update tool via `doit update_languages`. This produces [the package version of the card db](src/domdiv/card_db) from the card db source. This will also be run automatically and checked into git when you push to github. You should make sure that the resulting changes to the package are what you intend by generating dividers in the relevant languages.

If you would like to help with translations to new (or updating existing) languages, please see [instructions here](src/domdiv/card_db/translation.md).

## Fonts

There are a number of fonts used in Dominion and many of them we cannot distribute with the package. We use fallbacks to commonly distributed fonts that work fine if you don't care the match the game exactly. If you do want to match, the script prints the preferred fonts if it uses fallbacks. Some come with programs like Adobe Reader and you can grab them from there.

Sadly, many of these fonts use features that are not support by the reportlab package. Thus, they need to first be converted to ttf (TrueType) format. I used the open source package fontforge to do the conversion. Included as 'tools/convert_font.ff' is a script for fontforge to do the conversion, on Mac OS X with fontforge installed through macports or homebrew you can just run commands like `./tools/convert_font.ff MinionPro-Regular.otf`.

If you select language in `domdiv` options which is not supported in [ISO/IEC 8859-1:1998 (Latin1)](https://en.wikipedia.org/wiki/ISO/IEC_8859-1#Modern_languages_with_complete_coverage) (e.g. Czech), you will have to obtain Times Roman TTF fonts as well (see `./src/domdiv/fonts/README.md` for details).

To supply fonts locally, put them in a directory and supply the relative path to it to the script via the `--font-dir` option. Alternatively you can copy the converted `.ttf` files to the `fonts` directory in the `domdiv` package/directory, then perform the package install below.

## Using as a library

The library will be installed as `domdiv` with the main entry point being `domdiv.main.generate(options)`. It takes a `Namespace` of options as generated by python's `argparser` module. You can either use `domdiv.main.parse_opts(cmdline_args)` to get such an object by passing in a list of command line options (like `sys.argv`), or directly create an appropriate object by assigning the correct values to its attributes, starting from an empty class or an actual argparse `Namespace` object.

## Developing

Install requirements via `pip install -r requirements.txt`. Then, run `pre-commit install`. You can use `python setup.py develop` to install the `dominion_dividers` script so that it calls your checked out code, enabling you to run edited code without having to perform an install every time.

Feel free to comment on boardgamegeek at <https://boardgamegeek.com/thread/926575/web-page-generate-tabbed-dividers> or file issues on github (<https://github.com/sumpfork/dominiontabs/issues>).

Tests can be run (and their dependencies installed) via `python setup.py test`, which will also happen if/when you push a branch or make a PR.

## Image Sources

There is a separate [repo](https://github.com/sumpfork/dominiontabs_img_sources) for the image sources. While these are optional, they can be useful reference and/or used for creating new or recreating old tab banners, icons, etc. Many of these were originally scans of the physical game. Some of them have a lot of layers and are approaching 1GB in size, so they are hosted via [Git LFS](https://git-lfs.com/). As the Github version of that incurs a higher monthly cost, I instead host them on a private LFS server. If you would like the images or would like to contribute images let me know and I can make you an account on said server, or you I can copy them for you for easier access.

## Docker

The project can be compiled into a container:

`docker build . -t dominiontabs`

Once you have the `dominiontabs` container you can run it from your CLI and pass it arguments like so:

`docker run dominiontabs`

<!--TODO update this doc to pull pre-built images from GitHub once those are set up-->

Which will, by default, dump the output of the help text of the CLI tool. But we're going to want to add in some extra args 99% of the time.

1. Bind mount to an output directory (`-v`) and tell the script to output there so that we get a PDF in the local filesystem when things are done (`--outfile ./output/foo.pdf`).
1. Add the `--rm` argo to tell docker not to save a container each time it runs.
1. Point to the fonts built in to the image with `--font-dir /fonts`
1. Add a few CLI args to reduce the runtime and file size (`--expansions cornucopia`).

So now we have

`docker run -v $PWD/output:/app/output --rm dominiontabs --font-dir /fonts --expansions cornucopia --outfile ./output/dominion_dividers_docker.pdf`

Once that runs you should have under your current directory:

`./output/dominion_dividers_docker.pdf`

From there you feel free to add other arguments as you like!
