Fork of a fork of a repo to manipulate **Neurosky Mindwave Mobile** Headset over bluetooth on Linux (e.g. Raspberry Pi).

Follow tutorial [here](http://cttoronto.com/03/04/2013/interfacing-with-the-mindwave-mobile/) to get your Pi set up. It links to another tutorial for getting bluetooth working first. Then takes you through pairing, etc.
I personally also had to run ```sudo apt-get install python-bluetooth``` to get the code to run

To use, run ```python read_mindwave_mobile.py``` which connects to the headset, starts streaming data, prints the data to the screen, as well as saves the values to ```datapoints.csv``` in the local directory.
Read that file as a starting point for writing.

For those who are curious -- the basic principle, it seems, is that the headset reports every ~1s a block of some bytes which are a bunch of concatenated values that you have to know how to interpret. MindwaveDataPointsReader.py does most of this. It's not too complicated and whoever wrote it is clunky with Python, but you shouldn't need to really dig into it.
