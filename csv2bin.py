# -*- coding: utf-8 -*-
"""
Title: csv2bin.py
Purpose: Convert Infiniium CSV format waveform file to Infiniium bin format waveform file.
Author: luis.boluna@keysight.com
Known issues/limitations:
    Need to correct  loop for multiple waveforms in csv file.
    Need to clean up error handling by adding proper try-exemption.
    Expand to do other conversions.
Examples:
    
python csv2bin.py filename.bin
python csv2bin.py filename.bin --newfile foo.csv
    
   
File Header
There is only one file header in a binary file. The file header consists of the following information.
Cookie
Two byte characters, 'AG', that indicate the file is in the Agilent Binary Data file format.
Version
Two bytes that represent the file version.
File Size
A 32-bit integer that is the number of bytes that are in the file.
Number of Waveforms
A 32-bit integer that is the number of waveforms that are stored in the file.
Waveform Header
It is possible to store more than one waveform in the file, and each waveform stored will have a waveform header. When using segmented memory, each segment is treated as a separate waveform. The waveform header contains information about the type of waveform data that is stored following the waveform data header.
Header Size
A 32-bit integer that is the number of bytes in the header.
Waveform Type
A 32-bit integer that is the type of waveform stored in the file:
0 = Unknown
1 = Normal
2 = Peak Detect
3 = Average
4 = Not used in InfiniiVision oscilloscopes
5 = Not used in InfiniiVision oscilloscopes
6 = Logic
Number of Waveform Buffers
A 32-bit integer that is the number of waveform buffers required to read the data.
Points (included in metadata)
A 32-bit integer that is the number of waveform points in the data.
Count (included in metadata)
A 32-bit integer that is the number of hits at each time bucket in the waveform record when the waveform was created using an acquisition mode like averaging. For example, when averaging, a count of four would mean every waveform data point in the waveform record has been averaged at least four times. The default value is 0.
X Display Range (included in metadata)
A 32-bit float that is the X-axis duration of the waveform that is displayed. For time domain waveforms, it is the duration of time across the display. If the value is zero then no data has been acquired.
X Display Origin (included in metadata)
A 64-bit double that is the X-axis value at the left edge of the display. For time domain waveforms, it is the time at the start of the display. This value is treated as a double precision 64-bit floating point number. If the value is zero then no data has been acquired.
X Increment (included in metadata)
A 64-bit double that is the duration between data points on the X axis. For time domain waveforms, this is the time between points. If the value is zero then no data has been acquired.
X Origin (included in metadata)
A 64-bit double that is the X-axis value of the first data point in the data record. For time domain waveforms, it is the time of the first point. This value is treated as a double precision 64-bit floating point number. If the value is zero then no data has been acquired.
X Units (included in metadata)
A 32-bit integer that identifies the unit of measure for X values in the acquired data:
0 = Unknown
1 = Volts
2 = Seconds
3 = Constant
4 = Amps
5 = dB
6 = Hz
Y Units (included in metadata)
A 32-bit integer that identifies the unit of measure for Y values in the acquired data. The possible values are listed above under “X Units”.
Date (included in metadata)
A 16-byte character array, left blank in InfiniiVision oscilloscopes.
Time (included in metadata)
A 16-byte character array, left blank in the InfiniiVision oscilloscopes.
Waveform Label (used as dict key)
A 16 byte character array that contains the label assigned to the waveform.
Time Tags (included in metadata of segment_data key)
A 64-bit double, only used when saving multiple segments (requires segmented memory option). This is the time (in seconds) since the first trigger.
Segment Index (included in metadata of segment_data key)
A 32-bit unsigned integer. This is the segment number. Only used when saving multiple segments.
Waveform Data Header
A waveform may have more than one data set. Each waveform data set will have a waveform data header. The waveform data header consists of information about the waveform data set. This header is stored immediately before the data set.
Waveform Data Header Size
A 32-bit integer that is the size of the waveform data header.
Buffer Type
A 16-bit short that is the type of waveform data stored in the file:
0 = Unknown data
1 = Normal 32-bit float data
2 = Maximum float data
3 = Minimum float data
4 = Not used in InfiniiVision oscilloscopes
5 = Not used in InfiniiVision oscilloscopes
6 = Digital unsigned 8-bit char data (for digital channels)
Bytes Per Point
A 16-bit short that is the number of bytes per data point.
Buffer Size
A 32-bit integer that is the size of the buffer required to hold the data points.
"""

import numpy as np
import sys

file_header_dtype = np.dtype([('file_cookie', 'S2'),
                               ('file_version', 'S2'),
                               ('file_size', 'i4'),
                               ('num_waveforms', 'i4')])

waveform_header_dtype = np.dtype([('header_size', 'i4'),
                                ('waveform_type', 'i4'),
                                ('num_waveform_buffers', 'i4'),
                                ('num_points', 'i4'),
                                ('count', 'i4'),
                                ('x_display_range', 'f4'),
                                ('x_display_origin', 'f8'),
                                ('x_increment', 'f8'),
                                ('x_origin', 'f8'),
                                ('x_units', 'i4'),
                                ('y_units', 'i4'),
                                ('date_string', 'S16'),
                                ('time_string', 'S16'),
                                ('frame_string', 'S24'),
                                ('waveform_string', 'S16'),
                                ('time_tag', 'f8'),
                                ('segment_index', 'u4')])

buffer_header_dtype = np.dtype([('header_size', 'i4'),
                                ('buffer_type', 'i2'),
                                ('bytes_per_point', 'i2'),
                                ('buffer_size', 'i4')])

def waveformtype(wavetype):
    """
    Convert Keysight Waveform Type values to Infiniiium Binary file based values
    Since using Python 3.8 used if-elif instead of match case
    (for future use)
    """
    wavetype = str(wavetype)
    if wavetype == "Unknown":
           return 0
    elif wavetype == "Normal":
           return 1 
    elif wavetype == "Peak Detect":
           return 2 
    elif wavetype == "Average":
           return 3
    elif wavetype == "Not Used":
           return 4
    elif wavetype == "Not Used2":
           return 5
    elif wavetype =="Logic":
           return 6

       # If an exact match is not confirmed, this last case will be used if provided
    else:
           return np.nan

def units2num(units):
    """
    Convert Infiniium string based unit values to Infiniiium Binary file based values
    Since using Python 3.8 used if-elif instead of match case
    (for future use)
    """
    unit = str(units)
    if unit == "Unknown":
           return 0
    elif unit.startswith("Volt"):
           return 1 
    elif unit.startswith("Second"):
           return 2 
    elif unit == "Constant":
           return 3
    elif unit.startswith("Amp"):
           return 4
    elif unit == "dB":
           return 5
    elif unit =="Hz":
           return 6

       # If an exact match is not confirmed, this last case will be used if provided
    else:
           return np.nan

def buffertype2num(buffertype):
    """
    Convert Infiniium string based unit values to Infiniiium Binary file based values
    Since using Python 3.8 used if-elif instead of match case
    (for future use)
    """
    bftype = str(buffertype)
    if bftype == "Unknown":
           return 0
    elif bftype == "Normal":
           return 1 
    elif bftype == "Maximum Float":
           return 2 
    elif bftype == "Min Float":
           return 3
    elif bftype == "Not Used":
           return 4
    elif bftype == "Not Used2":
           return 5
    elif bftype =="Digital":
           return 6

       # If an exact match is not confirmed, this last case will be used if provided
    else:
           return np.nan


def readcsv_writebin(filename, outfilename):
    d = {}
    flag = True
    with open(filename, 'r', encoding='utf-8') as f:
        f_str = '<f4'
        #ch_dtype = np.dtype([('xdata', f_str),('ydata', f_str)])
        ch_dtype = np.dtype([('ydata', f_str)])
        for i, line in enumerate(f):
            
            if line[0] not in '.-0123456789':
                values = [value.strip() for value in line.split(":")]
                d[values[0]] = values[1]
                flag = -1
            else:
                if flag:
                    f.seek(i)
                    flag = False         
                raw = np.genfromtxt(f,delimiter=',', dtype = ch_dtype, skip_header=22, usecols=(-1))            
    
    
    file_cookie = np.array('AG', dtype = 'S2')
    file_version = np.array('10', dtype = 'S2')
    file_size = np.array(int(64040), dtype = 'i4')  #guess
    num_waveforms = np.array(int(d['Count']), dtype = 'i4')
    #assemble file_header
    file_header = np.array((file_cookie, file_version, file_size, num_waveforms), dtype = file_header_dtype)
    
    header_size = np.array(int(100), dtype = 'i4')  # guess
    waveform_typ = np.array(waveformtype("Normal"), dtype = 'i4')
    num_waveform_buffers = np.array(1, dtype = 'i4')
    num_points = np.array(d['Points'], dtype = 'i4')
    count = np.array(d['Count'], dtype = 'i4')
    
    x_display_range = np.array(d['XDispRange'], dtype = 'f4')
    x_display_origin = np.array(d['XDispOrg'], dtype = 'f8')
    x_increment = np.array(d['XInc'], dtype = 'f8')
    x_origin = np.array(d['XOrg'], dtype = 'f8')
    x_units = np.array(units2num(d['XUnits']), dtype = 'i4')
    y_units = np.array(units2num(d['YUnits']), dtype = 'i4')
    date_string = np.array(d['Date'], dtype = 'S16')
    
    
    time_string = np.array(d['Time'], dtype = 'S16')
    frame_string = np.array('N8900A:AT79587422', dtype = 'S24')  #guess
    waveform_string = np.array('Channel 1', dtype = 'S16')  #best guess
    time_tag = np.array(0.0, dtype = 'f8')
    segment_index = np.array(0, dtype = 'u4')
    
    #assemble waveform_header
    waveform_header = np.array((header_size, waveform_typ, num_waveform_buffers, num_points, \
              count, x_display_range, x_display_origin, x_increment, x_origin, \
              x_units, y_units, date_string, time_string, frame_string, waveform_string, \
              time_tag, segment_index), dtype = waveform_header_dtype)
    
    #fix wavefrom header size
    waveform_header['header_size'] = sys.getsizeof(waveform_header)
    
        
    header_size = np.array(int(4+2+2+4), dtype = 'i4')  # guess
    buffer_type = np.array(int(buffertype2num("Normal")), dtype = 'i2')  
    bytes_per_point = np.array(int(4), dtype = 'i2')  # locked at 4 bytes per point
    buffer_size = np.array(int(num_points*bytes_per_point), dtype = 'i4')
    #assemble buffer_header
    buffer_header = np.array((header_size, buffer_type, bytes_per_point, buffer_size), dtype = buffer_header_dtype)
    
    #fix wavefrom header size
    buffer_header['header_size'] = sys.getsizeof(buffer_header)
    
    #nump.tofile()
    with open(outfilename,'wb') as g:
        np.array((file_cookie, file_version, file_size, num_waveforms), dtype = file_header_dtype).tofile(g)
        np.array((header_size, waveform_typ, num_waveform_buffers, num_points, \
                  count, x_display_range, x_display_origin, x_increment, x_origin, \
                  x_units, y_units, date_string, time_string, frame_string, waveform_string, \
                  time_tag, segment_index), dtype = waveform_header_dtype).tofile(g)
        np.array((header_size, buffer_type, bytes_per_point, buffer_size), dtype = buffer_header_dtype).tofile(g)
        np.array(raw['ydata'], dtype=f_str).tofile(g)
    print(">>>File: {:} successfully written.".format(outfilename))
    
    return


def main():
    import argparse
    import os
    
    help_header = "\n" \
                  "Converts Infiniium CSV formatted waveform file to bin formatted waveform file.\n"\
                  "\n" \
                  "Example:\n" \
                  "python csv2bin.py filename.csv"\
                  "\n" \
                  "or," \
                  "\n" \
                  "python csv2bun.py filename.csv --newfile foo.bin" \
                  "\n\n" \
                  "luis.boluna@keysight.com"

    parser = argparse.ArgumentParser(help_header)
    parser.add_argument('file', metavar = 'file', type=str, help = "The filename of the csv formatted waveform file")
    parser.add_argument('--newfile', type=str, required=False, help = "New filename if it is not same as original")
    args = parser.parse_args()
    
    if args.newfile:
        readcsv_writebin(args.file, args.newfile)
    else:
        ext = os.path.splitext(args.file)[-1]
        if ext == ".csv":
            filename = args.file.split(ext)[0] + '.bin'
            readcsv_writebin(args.file, filename)
        else:
            raise ValueError('file extention: '+ext+' is not .bin. Throwing extention as safe guard to file overwrite')
    
if __name__ == "__main__":
       
        main()