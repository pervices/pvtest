# Stacked RX/TX Command GNURadio Examples

    python2 test_stacked_rx_commands.py
        -> Stacks 5 RX commands in the FPGA buffer at 1 second intervals,
           and polls python buffer size for incoming samples.

    python2 test_stacked_tx_commands.py
        -> Stacks 5 TX commands in GNURadio buffer at 5 second intervals.
           Hookup scope to any one of the channels for verification.

    python2 test_tx_rx_loopback.py
        -> Combines the above two tests into one two-threaded example
           having 4 stacked TX commands feeding 4 stacked RX commands.
           The output is one I/Q column for each channel (8 columns in total).
