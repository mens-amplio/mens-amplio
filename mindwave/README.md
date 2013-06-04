Fork of a fork of a repo to manipulate **Neurosky Mindwave Mobile** Headset over bluetooth on Linux (e.g. Raspberry Pi).

Follow tutorial [here](http://cttoronto.com/03/04/2013/interfacing-with-the-mindwave-mobile/) to get your Pi set up. It links to another tutorial for getting bluetooth working first.
I also had to run ```sudo apt-get install python-bluetooth```

To use, run ```python read_mindwave_mobile.py``` which starts recording, prints the data to the screen, as well as saves the values to ```datapoints.csv``` in the local directory.
Read that file as a starting point for writing
