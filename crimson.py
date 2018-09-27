from gnuradio import uhd

def make_snk_s(channels):
    snk = uhd.usrp_sink("crimson", uhd.stream_args(cpu_format="sc16", otw_format="sc16", channels=channels))
    snk.set_time_now(uhd.time_spec(0.0))
    return snk;

def make_src_c(channels):
    src = uhd.usrp_source("crimson", uhd.stream_args(cpu_format="fc32", otw_format="sc16", channels=channels), False)
    src.set_time_now(uhd.time_spec(0.0))
    return src

def calibrate(end, channels, sample_rate, center_freq, gain):
    """
    Calibrates a TX or RX radio end to the parameters specicified.
    """
    end.set_samp_rate(sample_rate)
    end.set_clock_source("internal")
    for channel in channels:
        end.set_center_freq(center_freq, channel)
        end.set_gain(gain, channel)

def get_snk_s(channels, sample_rate, center_freq, gain):
    """
    Connects to the crimson and returns a sink object expecting interleaved shorts of complex data.
    """
    snk = make_snk_s(channels)
    calibrate(snk, channels, sample_rate, center_freq, gain)
    return snk

def get_src_c(channels, sample_rate, center_freq, gain):
    """
    Connects to the crimson and returns a source object which provides floats of complex date.
    """
    src = make_src_c(channels)
    calibrate(src, channels, sample_rate, center_freq, gain)
    return src
