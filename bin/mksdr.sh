#!/bin/sh -ex
#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK rtl-demo-app.
#
# REDHAWK rtl-demo-app is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK rtl-demo-app is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
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
$thisdir/copysdr.sh /dev/nodes/Digitizer_Node

# RTL FM Waveform
$thisdir/copysdr.sh /dom/waveforms/RTL_FM_Waveform

# FM Components
$thisdir/copysdr.sh /dom/components/AmFmPmBasebandDemod
$thisdir/copysdr.sh /dom/components/ArbitraryRateResampler
$thisdir/copysdr.sh /dom/components/DataConverter
$thisdir/copysdr.sh /dom/components/fastfilter
$thisdir/copysdr.sh /dom/components/FrontEndController
$thisdir/copysdr.sh /dom/components/NOOP
$thisdir/copysdr.sh /dom/components/psd
$thisdir/copysdr.sh /dom/components/TuneFilterDecimate

# Softpackage dependencies
$thisdir/copysdr.sh /dom/deps/dsp
$thisdir/copysdr.sh /dom/deps/fftlib

# Optional components
$thisdir/copysdr.sh -w /dev/devices/FmRdsSimulator
#$thisdir/copysdr.sh -w /dev/nodes/sim_RX_DIGITIZER_Node
