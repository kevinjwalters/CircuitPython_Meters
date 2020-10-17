Introduction
============

This is `CircuitPython <https://circuitpython.org/>`_ library for meters
using NeoPixel (WS2812) or DotStar (APA102) (RGB) LEDs.

 * `PeakMeter` - looks like a VUmeter in colour but shows peak value too.

Dependencies
=============

This library depends on:

* `Adafruit CircuitPython <https://github.com/adafruit/circuitpython>`_


Usage Example
=============

.. code-block:: python

    import board
    import time
    import random
    import neopixel
    import meters

    NUM_PIXELS = 10 
    pixels = board.NEOPIXEL
    pixels = neopixel.NeoPixel(board.NEOPIXEL, NUM_PIXELS)
    meter = meters.PeakMeter(pixels)
    
    while True:
        for volume in range(0, 65535, 1000):
            meter.value = volume
            time.sleep(0.010)
        delay_s = 0.005 + random.random() / 50.0
        for volume in range(65535, 0, -1000):
            meter.value = volume
            time.sleep(delay_s)
