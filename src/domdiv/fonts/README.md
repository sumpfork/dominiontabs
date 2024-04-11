## Fonts

I believe I cannot distribute some fonts (Minion Pro, Trajan, Charlgemagne) domdiv uses as they are owned by Adobe with a License that I understand to disallow redistribution. You can look for them on fontsgeek.com or similar sites.

Alternatively, many font files are included with every install of the free Adobe Reader. For example, on Windows 7 they are in `C:\Program Files (x86)\Adobe\Reader 9.0\Resource\Font`.

Sadly, all these fonts use features that are not support by the reportlab package. Thus, they need to first be converted to ttf (TrueType) format. I used the open source package fontforge to do the conversion. Included as 'tools/convert.ff' is a script for fontforge to do the conversion, on Mac OS X with fontforge installed through homebrew you can just run, for example, `./tools/convert.ff MinionPro-Regular.otf`.

Copy the converted `.ttf` files to the `fonts` directory in the `domdiv` package/directory, then perform the package install below. Or, you can put them into any directory and provide the `--font-dir` option to point to it when you call the script, even if it's installed from pypi.

If you select language in `domdiv` options which is not supported in [ISO/IEC 8859-1:1998 (Latin1)](https://en.wikipedia.org/wiki/ISO/IEC_8859-1#Modern_languages_with_complete_coverage) (e.g. Czech), you will have to obtain Times Roman TTF fonts as well:

- Times-Roman.ttf
- Times-Roman-Bold.ttf
- Times-Roman-Italic.ttf

The reason is that reportlab package only [supports Windows-1252 / ISO-8859-1 encoding](https://docs.reportlab.com/reportlab/userguide/ch3_fonts/#standard-single-byte-font-encodings) using the default embedded fonts and non Latin1 characters will render as black boxes. For example, on Windows OS the Times TTF fonts are located in C:\Windows\Fonts called `times.ttf`, `timesbd.ttf` and `timesi.ttf`.
