### meters.py v0.3
### A CircuitPython library for the meters on NeoPixels

### Tested with an Adafruit CLUE and CircuitPython 5.3.1 and edu:bit NeoPixels

### MIT License

### Copyright (c) 2020 Kevin J. Walters

### Permission is hereby granted, free of charge, to any person obtaining a copy
### of this software and associated documentation files (the "Software"), to deal
### in the Software without restriction, including without limitation the rights
### to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
### copies of the Software, and to permit persons to whom the Software is
### furnished to do so, subject to the following conditions:

### The above copyright notice and this permission notice shall be included in all
### copies or substantial portions of the Software.

### THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
### IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
### FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
### AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
### LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
### OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
### SOFTWARE.


import time


class PeakMeter:
    GREEN = (0,24,0)
    YELLOW = (52,22,0)
    RED = (110,0,0)


    def __init__(self, pixels,
                 *,
                 fractions=True, dB=False, show=False, reverse=True,
                 decay=0.4, peak_hold=0.75
                 ):
        self._pixels = pixels
        self._fractions = fractions
        self._show = show
        self._reverse = reverse

        red_num = 1
        yellow_num = round(len(pixels) / 4.0)
        green_num = len(pixels) - yellow_num - red_num

        self._colours = ([self.GREEN] * green_num +
                         [self.YELLOW] * yellow_num +
                         [self.RED] * red_num)

        pixels_num = len(pixels)
        if dB:
            if pixels_num == 3:
                self._thresholds = [-30, -6, 0, 3]
            elif pixels_num == 4:
                self._thresholds = [-40, -12, -6, 0, 3]
            else:
                self._thresholds = [(x - pixels_num + 1) * 6
                                    for x in range(pixels_num)] + [3]
                if self._thresholds[0] > -40:
                    self._thresholds[0] = -40
            self._value = float("-Inf")
        else:
            if pixels_num == 3:
                self._thresholds = [15000, 45000, 57500, 62500]
            elif pixels_num == 4:
                self._thresholds = [5000, 25000, 45000, 57500, 62500]
            else:
                self._thresholds = [5000 + round(x * 52500 / (pixels_num - 1))
                                    for x in range(pixels_num)] + [62500]
            self._value = 0

        try:
            self._time_func = time.monotonic_ns
            self._time_div = 1e9
            self._peak_hold = round(peak_hold * self._time_div)
            self._decay_time = round(decay * self._time_div)
        except AttributeError:
            self._time_func = time.monotonic
            self._time_div = 1
            self._peak_hold = peak_hold
            self._decay_time = decay
        self._peak = self._value
        self._peak_ts = self._time_func()
        self._decayed_value = self._value
        self._decayed_value_ts = self._time_func()


    def _updatePeakAndDecay(self, value):
        now = self._time_func()
        if value > self._decayed_value or not self._decay_time:
            self._decayed_value = value
        else:
            decay_factor = (now - self._decayed_value_ts) / self._decay_time
            ### Reduce the value between 0 and 100% of the way to value

            self._decayed_value -= (min(decay_factor, 1.0)
                                    * (self._decayed_value - value))
        self._decayed_value_ts = now

        if (value > self._peak
                or now - self._peak_ts > self._peak_hold):
            self._peak = value
            self._peak_ts = self._time_func()


    ### for self._thresholds = [ -40, -10, 0, 6, 8]
    ### -Inf to -40 all off
    ### -40 to -10  G1
    ### -10 to 0    G2
    ### 0 to 6      Y
    ### 6 to 8      R
    ### 8 to Inf    full R
    def _valToPos(self, value):
        position = -1
        brightness = 0
        if value < self._thresholds[0]:
            return (position, brightness)

        for idx in range(len(self._thresholds) - 1):
            threshold_lower = self._thresholds[idx]
            threshold_upper = self._thresholds[idx + 1]
            if threshold_lower <= value < threshold_upper:
                position = idx
                brightness = (value - threshold_lower) / (threshold_upper - threshold_lower)
                return (position, brightness)

        return (idx, 1.0)  ### full brightness on final pixel


    def _updatePixels(self):
        if self._decay_time:
            value_pos, value_bri = self._valToPos(self._decayed_value)
        else:
            value_pos, value_bri = self._valToPos(self._value)
        peak_pos, peak_bri = self._valToPos(self._peak)

        new_pixels = [(0, 0, 0)] * len(self._pixels)
        for idx in range(value_pos + 1):
            if idx == value_pos:  ### last one?
                new_pixels[idx] = [round(ch * value_bri) for ch in self._colours[idx]]
            else:
                new_pixels[idx] = self._colours[idx]

        ### Add the peak value which will always be >= current value
        if peak_pos >= 0:
            new_pixels[peak_pos] = [round(ch * peak_bri) for ch in self._colours[peak_pos]]

        ### One slice assignment for single, fast update
        self._pixels[:] = list(reversed(new_pixels)) if self._reverse else new_pixels
        if self._show:
            self._pixels.show()


    @property
    def peak(self):
        return self._peak


    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        self._value = value
        self._updatePeakAndDecay(value)
        self._updatePixels()
