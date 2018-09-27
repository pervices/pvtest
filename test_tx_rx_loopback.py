from gnuradio import analog
from gnuradio import blocks
from gnuradio import uhd
from gnuradio import gr

import math
import crimson
import threading
import sys
import time
import numpy

# Threads make exiting upon a failure complicated. This boolean
# will be returned to the command line once the test is complete.
failure = False

def fail(message):
    sys.stderr.write("failure: " + message + "\n")

    global failure
    failure = True

def dump(vsnk, sample_count, channels):
    """
    Prints a vsnk in channel column layout in IQ format for all channels.
    """
    for sample in xrange(sample_count):
        for channel in channels:
            datum = vsnk[channel].data()[sample]
            sys.stdout.write("%10.5f %10.5f\t" % (datum.real, datum.imag))
        sys.stdout.write("\n")

    sys.stdout.write("\n")

def absolute_area(data):
    """
    Takes and IQ wave.
    Absolutes then integrates.
    The complex module of the integral is returned.
    """
    return abs(numpy.trapz(numpy.absolute(data)))

def test_fullness(vsnk, sample_count, start_time_specs):
    """
    Here, 'x' denotes a wave, and '-' denotes no data (zero DC).

    { ------- lhs ------ } { ------- rhs ------ }
    t[0]                                        t[1]
    ------------------xxxxxxxxxxxxxxxxxxxxxxxxxxx------------------xxxxx ... xxxxx
    |                     |                     |                                |
    0                     sample_count / 2      sample_count                     total_sample_count

    The fullness test assumes the right hand side (rhs) of the waveform has more signal present
    than the left hand side (lhs) of the waveform.

    """
    for v in vsnk:

        for i in range(len(start_time_specs)):

            a = int(i * sample_count)
            b = int(a + sample_count / 2)
            c = int(a + sample_count - 1)

            lhs = absolute_area(v.data()[a : b])
            rhs = absolute_area(v.data()[b : c])

            print "lhs %f: rhs %f" % (lhs, rhs)

            # Noise threshold checks.
            thresh = 0.1
            if lhs < thresh: fail("timespec %d: lhs was noise" % i)
            if rhs < thresh: fail("timespec %d: rhs was noise" % i)

            # Expected waveform check.
            if lhs > rhs:
                fail("timespec %d: unexpected waveform (lhs was greater than rhs)" % i)

def tx_run(csnk, channels, sample_count, start_time_specs, sample_rate):
    """                                       +-----------+
    +---------+   +---------+   +---------+   |           |
    | sigs[0] |-->| heds[0] |-->| c2ss[0] |-->|ch[0]      |
    +---------+   +---------+   +---------+   |           |
    +---------+   +---------+   +---------+   |           |
    | sigs[1] |-->| heds[1] |-->| c2ss[1] |-->|ch[1]      |
    +---------+   +---------+   +---------+   |           |
                                              |           |
    +---------+   +---------+   +---------+   |           |
    | sigs[N] |-->| heds[N] |-->| c2ss[N] |-->|ch[N]      |
    +---------+   +---------+   +---------+   |      csnk |
                                              +-----------+
    """

    sigs = [analog.sig_source_c(
        sample_rate, analog.GR_SIN_WAVE, 1.0e6, 2.0e4, 0.0)
        for ch in channels]

    heds = [blocks.head(gr.sizeof_gr_complex, sample_count)
        for ch in channels]

    c2ss = [blocks.complex_to_interleaved_short(True)
        for ch in channels]

    flowgraph = gr.top_block()
    for ch in channels:
        flowgraph.connect(sigs[ch], heds[ch])
        flowgraph.connect(heds[ch], c2ss[ch])
        flowgraph.connect(c2ss[ch], (csnk, ch))

    for start_time_spec in start_time_specs:
        csnk.set_start_time(start_time_spec)

        flowgraph.run()
        for hed in heds:
            hed.reset()

def rx_run(csrc, channels, sample_count, start_time_specs, sample_rate, vsnks):
    """
    +-----------+
    |           |   +---------+
    |      ch[0]|-->| vsnk[0] |
    |           |   +---------+
    |           |   +---------+
    |      ch[1]|-->| vsnk[1] |
    |           |   +---------+
    |           |
    |           |   +---------+
    |      ch[N]|-->| vsnk[N] |
    | csrc      |   +---------+
    +-----------+
    """

    vsnk = [blocks.vector_sink_c() for channel in channels]

    flowgraph = gr.top_block()
    for channel in channels:
        flowgraph.connect((csrc, channel), vsnk[channel])

    # The flowgraph must be started before stream commands are sent.
    flowgraph.start()

    for start_time_spec in start_time_specs:
        cmd = uhd.stream_cmd_t(uhd.stream_cmd_t.STREAM_MODE_NUM_SAMPS_AND_DONE)
        cmd.num_samps = sample_count
        cmd.stream_now = False
        cmd.time_spec = start_time_spec
        csrc.issue_stream_cmd(cmd)

    total_sample_count = len(start_time_specs) * sample_count

    # Wait for completion.
    while len(vsnk[0].data()) < total_sample_count:
        time.sleep(0.1)

    flowgraph.stop()
    flowgraph.wait()

    # Save for later use.
    vsnks.append(vsnk)

    dump(vsnk, total_sample_count, channels)

    test_fullness(vsnk, sample_count, start_time_specs)

def test_tx_rx_loopback():

    vsnks = []

    for iteration in range(1):

        channels = range(4)

        sample_rate = 10e6
        sample_count = 200
        center_freq = 15e6
        gain = 30.0 # Do not change - noise integration threshold checks are hard coded.

        csnk = crimson.get_snk_s(channels, sample_rate, center_freq, gain)
        csrc = crimson.get_src_c(channels, sample_rate, center_freq, gain)

        start_time_specs = [
            uhd.time_spec( 7),
            uhd.time_spec( 9),
            uhd.time_spec(11),
            uhd.time_spec(13),
            ]

        threads = [
            threading.Thread(target = tx_run, args = (csnk, channels, sample_count, start_time_specs, sample_rate)),
            threading.Thread(target = rx_run, args = (csrc, channels, sample_count, start_time_specs, sample_rate, vsnks)),
            ]
        for thread in threads: thread.start()
        for thread in threads: thread.join()

        # For loops in python do not call desctructors when leaving scope.
        del csnk
        del csrc

        print "vsnk length: %d" % len(vsnks)

    quit(1 if failure else 0)

if __name__ == '__main__':
    test_tx_rx_loopback()
