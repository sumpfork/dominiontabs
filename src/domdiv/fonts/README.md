## Fonts

I believe I cannot distribute one font (Minion Pro) domdiv uses as they are owned by Adobe with a License that I understand to disallow redistribution. However, you can download the [3 font files from a third party here](https://www.dropbox.com/s/tsqk69mayoa3pfz/MinionPro-ForDominionTabs.zip?dl=1).

Other sources for the font files (included for historical record but probably unneeded as long as long as the download above works:

- http://fontsgeek.com/fonts/Minion-Pro-Regular
- http://fontsgeek.com/fonts/Minion-Pro-Italic
- http://fontsgeek.com/fonts/Minion-Pro-Bold

Alternatively, the font files are included with every install of the free Adobe Reader. For example, on Windows 7 they are in C:\Program Files (x86)\Adobe\Reader 9.0\Resource\Font called `MinionPro-Regular.otf`, `MinionPro-Bold.otf` and `MinionPro-It.otf`.

Sadly, all these fonts use features that are not support by the reportlab package. Thus, they need to first be converted to ttf (TrueType) format. I used the open source package fontforge to do the conversion. Included as 'convert.ff' is a script for fontforge to do the conversion, on Mac OS X with fontforge installed through macports or homebrew you can just run `./convert.ff MinionPro-Regular.otf`, `./convert.ff MinionPro-Bold.otf` and `./convert.ff MinionPro-It.otf`. With other fontforge installations, you'll need to change the first line of convert.ff to point to your fontforge executable. I have not done this step under Windows - I imagine it may be possible with a cygwin install of fontforge or some such method.

Copy the converted `.ttf` files to the `fonts` directory in the `domdiv` package/directory, then perform the package install below.
