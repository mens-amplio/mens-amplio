mens-amplio
===========

Main repo for code that controls lighting and flame effects and handles hardware interfacing

Instructions to get lighting simulator running on a laptop:
* Clone this repo
* Clone https://github.com/stappon/openpixelcontrol and switch to branch mens-amplio-tweaks
* Install dependencies
* Build OPC:
  cd openpixelcontrol
  make
* Launch OPC visualizer:
  bin/gl_server [path-to]/mens-amplio/modeling/opc-layout.json & - this launches the visualizer
* Launch MA display scripts:
  cd ../mens-amplio
  run led_plaything.py or responsive_led_test.py. (If you don't have a Neurosky headset, make sure the latter is passing a FakeHeadset to the headset thread)

Dependencies:
* scipy
* matplotlib
* noise
* pybluez
* smbus

Instructions to run on Raspberry Pi with WS2801 LEDs:
* Connect MOSI pin on Pi to data pin to LED data pin, SCLK pin on Pi to LED clock pin, share ground between Pi and LEDs (do NOT power LEDs from Pi directly)
* Connect SDA/SCL pins on flame relay board (http://propaneandelectrons.com/projects/wifire16) to SDA/SCL pins on Pi, share ground
* Same as above, but ignore gl_server build error and run bin/ws2801_server & instead of gl_server
