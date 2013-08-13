mens-amplio
===========

Main repo for code that controls lighting and flame effects and handles hardware interfacing

Instructions to get lighting simulator running on a dev machine (no additional hardware required):
* Clone this repo
* Clone https://github.com/stappon/openpixelcontrol and pull branch mens-amplio-tweaks
* Install dependencies
* Build OPC and launch visualizer:
  * cd [whatever]/openpixelcontrol
  * make
  * bin/gl_server [whatever]/mens-amplio/modeling/opc-layout.json &
* Build Perlin noise C module:
  * cd [whatever]/mens-amplio
  * python setup.py build --build-platlib= (OK to ignore compiler warnings)
* Launch MA display scripts:
  * cd [whatever]/mens-amplio
  * ./led_plaything.py (to test single effects)
  * ./run.py test (to test with headset/flame emulation - edit effects playlist in testplaylists.py) 

Dependencies:
* python-scipy (includes numpy; make sure that numpy is version 1.7*)
* python-matplotlib
* mesa-common-dev and freeglut3-dev (for OPC gl_server on Linux; not needed on Pi or Mac)
* bluetooth, blueman, bluez-utils, python-bluez (for Neurosky headset)
* python-smbus (for flame board)

Instructions to run on Raspberry Pi with WS2801 LEDs:
* Connect MOSI pin on Pi to data pin to LED data pin, SCLK pin on Pi to LED clock pin, share ground between Pi and LEDs (do NOT power LEDs from Pi directly)
* Connect SDA/SCL pins on flame relay board (http://propaneandelectrons.com/projects/wifire16) to SDA/SCL pins on Pi, share ground
* Same as above, but ignore gl_server build error and run bin/ws2801_server & instead of gl_server
