#!/bin/sh -ex
thisdir=`dirname "$0"`
thisdir=`cd "$thisdir" && pwd`

./copysdr.sh /dev/mgr
./copysdr.sh /dom/mgr
./copysdr.sh /dom/domain

# GPP Node
./copysdr.sh /dev/devices/GPP
./copysdr.sh -s "$thisdir"/../deploy /dev/nodes/RTL-GPP-Node

# RTL Front End device
./copysdr.sh /dev/devices/RTL2832U
./copysdr.sh /dev/nodes/RTL2832_Node

# RTL FM Waveform
./copysdr.sh /dom/waveforms/RTL_FM_Waveform

# FM Components
./copysdr.sh /dom/components/RTL_FM_Controller
./copysdr.sh /dom/components/agc
./copysdr.sh /dom/components/psd
./copysdr.sh /dom/components/AmFmPmBasebandDemod
./copysdr.sh /dom/components/DataConverter
./copysdr.sh /dom/components/NOOP
./copysdr.sh /dom/components/ScaleOutput
./copysdr.sh /dom/components/TuneFilterDecimate

# Softpackage dependencies
./copysdr.sh /dom/deps/dsp
./copysdr.sh /dom/deps/fftlib

# Optional components
./copysdr.sh -w /dev/devices/sim_RX_DIGITIZER
./copysdr.sh -w /dev/nodes/sim_RX_DIGITIZER_Node
