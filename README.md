# PySonde
*Open source, cross-platform universal radiosonde decoder written in Python*

## Please note that PySonde is heavily under development. For the time being, please have understanding for bugs, crashes and weird behavior.

PySonde represents an effort to create an decent radiosonde decoder for Linux.
When the idea for such a program emerged, the only known decoder was a paid Windows software called SondeMonitor.
The only free and functional alternative as of May 2016 is [this repository](https://github.com/rs1729/RS) made by [zilog80](http://www.fingers-welt.de/phpBB/memberlist.php?mode=viewprofile&u=871).
It's not a single tool but a collection of small independent decoders written in C which have a lot of functions in common.
While it's functional and reliable (I'm still using it daily while developing PySonde), it's lacking some of the core functionalities of SondeMonitor - GUI, audio interface, fall prediction, KML generator, etc.
Being written in C, these are difficult to develop, so the decoder has to be wrapped with scripts which is not the ideal solution.

*PySonde is based on the logic of zilog80's decoder. To be precise, with his permission, demodulation and processing logic was studied and rewritten in Python.*

Simply said:
**PySonde's goal is to be an free, full-featured and easy to use cross-platform radiosonde decoder which anyone can contribute to.**
Any feature suggestions, pull requests and bug reports are welcome.

## License
Licensed under GNU AGPLv3 license. You will never have to pay for PySonde.
Full copy of the license is in the LICENSE file.

## Requirements
PySonde is developed on Ubuntu 16.04 with Python 3.5.
Compatibility with older Python versions (especially <3.4) cannot be guaranteed.
- at least python3.4
- python3-tk
- python3-twisted

On Ubuntu 16.04, use:
`sudo apt install python3 python3-tk python3-twisted`

## Usage
**Preview version supports only decoding Vaisala RS41 data from the .wav file.**

To start PySonde, run `./main.py` from terminal.

Click on "Open WAV" to locate .wav recording (note to hackers: grab Gqrx's UDP stream and send it to named pipe which you'll open with PySonde).
After that, click on "Process WAV" to decode the data. Data will be output to the big text box.
