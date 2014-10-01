#!/bin/sh -ex
thisdir=`dirname "$0"`
thisdir=`cd "$thisdir" && pwd`

$thisdir/copysdr.sh /dev/mgr
$thisdir/copysdr.sh /dom/mgr
$thisdir/copysdr.sh /dom/domain

# GPP Node
$thisdir/copysdr.sh /dev/devices/GPP
$thisdir/copysdr.sh -s "$thisdir"/../deploy /dev/nodes/RTL-GPP-Node

# RTL Front End device
$thisdir/copysdr.sh /dev/devices/RTL2832U
$thisdir/copysdr.sh /dev/nodes/RTL2832_Node

# RTL FM Waveform
$thisdir/copysdr.sh /dom/waveforms/RTL_FM_Waveform

# FM Components
$thisdir/copysdr.sh /dom/components/RTL_FM_Controller
$thisdir/copysdr.sh /dom/components/agc
$thisdir/copysdr.sh /dom/components/psd
$thisdir/copysdr.sh /dom/components/AmFmPmBasebandDemod
$thisdir/copysdr.sh /dom/components/DataConverter
$thisdir/copysdr.sh /dom/components/NOOP
$thisdir/copysdr.sh /dom/components/ScaleOutput
$thisdir/copysdr.sh /dom/components/TuneFilterDecimate

# Softpackage dependencies
$thisdir/copysdr.sh /dom/deps/dsp
$thisdir/copysdr.sh /dom/deps/fftlib

# Optional components
$thisdir/copysdr.sh -w /dev/devices/sim_RX_DIGITIZER
$thisdir/copysdr.sh -w /dev/nodes/sim_RX_DIGITIZER_Node
