from gnuradio import blocks
from gnuradio import uhd
from gnuradio import gr
import crimson
import time

#                                                 x x x x x x - - - x - - - - - x x x x x x x x x x x x x x x x x x x x x x x x x
# 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1 1
# 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0 9 8 7 6 5 4 3 2 1 0
#       6                   5                   4                   3                   2                   1

def gpio_write(csrc, pins, mask, time):
    """ GPIO command queues to FPGA FIFO with timespec when register address 0x3 is written to """
    csrc.set_command_time(uhd.time_spec(time))
    csrc.set_user_register(0, (pins >>  0) & 0xFFFFFFFF) # 32bit.
    csrc.set_user_register(1, (pins >> 32) & 0xFFFFFFFF)
    csrc.set_user_register(2, (mask >>  0) & 0xFFFFFFFF)
    csrc.set_user_register(3, (mask >> 32) & 0xFFFFFFFF) # Queue.

def test_gpio_commands():
    csrc = crimson.get_src_c(range(4), 20e6, 15e6, 0.0) # Does not matter if sink or source is used here.
    pins = 0x0
    all = 0xFFFFFFFFFFFFFFFF; # 64bit.
    for second in range(1, 128, 1):
        pins ^= all
        gpio_write(csrc, pins, all, second);

if __name__ == '__main__':
    test_gpio_commands()
