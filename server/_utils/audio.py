#
# This file is protected by Copyright. Please refer to the COPYRIGHT file
# distributed with this source distribution.
#
# This file is part of REDHAWK server.
#
# REDHAWK server is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 3 of the License, or (at your option) any
# later version.
#
# REDHAWK server is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see http://www.gnu.org/licenses/.
#
import struct
import numpy

def wav_hdr(num_channels, sample_rate, sample_width):
  '''
  Returns a string that is a valid WAVE header. Useful for web streams/sockets.

  :param num_channels: 1 = Mono, 2 = Stereo
  :param sample_rate:
  :param sample_width: bytes per sample, ie 16bit PCM = 2
  :return:
  '''
  chunk_hdr = struct.pack('4si4s',
                          'RIFF',
                          0, # Chunk Size
                          'WAVE')

  # fmt chunk
  byte_rate = sample_rate * sample_width * num_channels
  block_align = num_channels * sample_width
  bits_per_sample = sample_width * 8

  format_chunk = struct.pack('4sihHIIHH',
                             'fmt ',
                             16, # Fmt Sub Chunk Size
                             1,  # AudioFormat (1 = PCM)
                             num_channels,
                             sample_rate,
                             byte_rate,
                             block_align,
                             bits_per_sample)

  output = chunk_hdr + format_chunk + 'data'
  return output

def pcm2wav(data, num_channels, sample_rate):
  '''
  Converts PCM to Wave format. Converts PCM to 16-bit

  :param data:
  :param num_channels: 1 = Mono, 2 = Stereo
  :param sample_rate:
  :return:
  '''

  # TODO: Handle different data formats. Current implementation just
  #       casts. Need to handle the more standard normalized floats
  sample_width = 2
  pcm_data = numpy.array(data).astype('int16')

  chunk_hdr = struct.pack('4si4s',
                          'RIFF',
                          36 + pcm_data.nbytes, # Chunk Size
                          'WAVE')

  # fmt chunk
  byte_rate = sample_rate * sample_width * num_channels
  block_align = num_channels * sample_width
  bits_per_sample = sample_width * 8

  format_chunk = struct.pack('4sihHIIHH',
                             'fmt ',
                             16, # Fmt Sub Chunk Size
                             1,  # AudioFormat (1 = PCM)
                             num_channels,
                             sample_rate,
                             byte_rate,
                             block_align,
                             bits_per_sample)

  output = chunk_hdr + format_chunk + 'data' + pcm_data.tostring()
  return output