#Dominion Divider Generation

## Introduction
 
This is a script to generate card dividers for storing cards for the game [Dominion](https://boardgamegeek.com/boardgame/36218/dominion). If you are just looking go generate some dominion dividers, there is no need to install this script as I host a [live version of this generator code](http://domtabs.sandflea.org). However, if you want to use arguments that I don't expose on that page, or change the code, or contribute to the project the full generation code (not the web interface or the fonts) is included here, and contributions are more than welcome.

Again, to generate tabs go to the ***[Online Generator](http://domtabs.sandflea.org)***.

## Prerequisites

#### Python Packages
You need the python packages for reportlab (http://www.reportlab.com/software/opensource/rl-toolkit/download/) and PIL (http://www.pythonware.com/products/pil/) installed. You can install them manually or use the included setup.py via 'python setup.py install' (perhaps run via 'sudo' if not in a virtual env) which should install everything for you.

#### Fonts
I believe I cannot distribute one font (Minion Pro) dominion\_tabs uses as they are commercially sold by Adobe. However, the font files are included with every install of the free Adobe Reader. For example, on Windows 7 they are in C:\Program Files (x86)\Adobe\Reader 9.0\Resource\Font called MinionPro-Regular.otf and MinionPro-Bold.otf. Copy these two files to a subdirectory called 'fonts' in the dominion_tabs directory.

Sadly, these fonts use features of the otf format that are not support by the reportlab package. Thus, they need to first be converted to ttf (TrueType) format. I used the open source package fontforge to do the conversion. Included as 'convert.ff' is a script for fontforge to do the conversion, on Mac OS X with fontforge installed through macports you can just run './convert.ff MinionPro-Regular.otf' and './convert.ff MinionPro-Bold.otf'. With other fontforge installations, you'll need to change the first line of convert.ff to point to your fontforge executable. I have not done this step under Windows - I imagine it may be possible with a cygwin install of fontforge or some such method.

## Install/Running
Once the prerequisites exist, just run 'python dominiontabs.py <outfile>' to produce a pdf file of dominion tabs. You can use a '-h' flag to see various options, such as changing to vertical tabs.

Feel free to comment on boardgamegeek at <http://boardgamegeek.com/filepage/59848/horizontal-double-sided-dominion-tabs-for-all-expa> or file issues on github (<https://github.com/sumpfork/dominiontabs/issues>).

