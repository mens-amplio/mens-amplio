Simple python interface to NeuroSky Mindwave Mobile headset.

python example_usage.py

Based on the communications spec from Neurosky: http://wearcam.org/ece516/mindset_communications_protocol.pdf

Note: Even though this was originally forked from another repo, it's unrecognizably different now. I ended up gutting the other code (which I felt was unclear and hard to work with) and rewriting from scratch using the neurosky communications spec. I'm leaving this as forked since that code helped me understand some things and deserves credit for being a useful jump-start.

Files:
* mindwave.py -- has Headset class that interacts with the headset and has a few simple function calls to get data out of it (Datapoint objects, defined there as well)
* example_usage.py -- these four lines of code show the bare bones of reading data from the headset.
* pay_attention.py -- another simple program that prints a different message depending on your 'attention' level. Try keeping your eyes still, then moving them.
* record_to_csv.py -- records readings from the headset to a file for later usage

Pi setup:
1) Plug in the usb bluetooth dongle
2) run "sudo apt-get install python-bluetooth" on your pi
3) Clone this repo to your pi
4) Run "python example.usage.py"

If that doesn't work, follow the tutorial [here](http://cttoronto.com/03/04/2013/interfacing-with-the-mindwave-mobile/) to get your Pi set up. It links to another tutorial for getting bluetooth working first. Then takes you through pairing, etc.

