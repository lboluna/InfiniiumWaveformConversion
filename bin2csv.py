# -*- coding: utf-8 -*-
"""
Title: bin2csv.py
Purpose: Convert Infiniium bin format waveform file to Infiniium CSV format waveform file.
Author: luis.boluna@keysight.com


Known issues/limitations:
    Need to correct  loop for multiple waveforms in csv file.
    Need to clean up error handling by adding proper try-exemption.
    Expand to do other conversions.


Examples:
    
python bin2csv.py filename.bin


python bin2csv.py filename.bin --newfile foo.csv


    
   

Used code from https://github.com/FaustinCarter/agilent_read_binary for binary read.


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
import dateutil.parser as dp

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

def num2units(number):
    """
    Convert Infiniium binary file based unit values to strings
    Since using Python 3.8 used if-elif instead of match case
    """
    if number == 0:
        return "Unknown"
    elif number == 1:
        return "Volts"
    elif number == 2:
        return "Seconds"
    elif number == 3:
        return "Constant"
    elif number == 4:
        return "Amps"
    elif number == 5:
        return "dB"
    elif number == 6:
        return "Hz"

    # If an exact match is not confirmed, this last case will be used if provided
    else:
        return None
       
def units2num(units):
    """
    Convert Infiniium string based unit values to Infiniiium Binary file based values
    Since using Python 3.8 used if-elif instead of match case
    (for future use)
    """
    unit = str(units)
    if unit == "Unknown":
           return 0
    elif unit == "Volts":
           return 1 
    elif unit == "Seconds":
           return 2 
    elif unit == "Constant":
           return 3
    elif unit == "Amps":
           return 4
    elif unit == "dB":
           return 5
    elif unit =="Hz":
           return 6

       # If an exact match is not confirmed, this last case will be used if provided
    else:
           return np.nan
       
        
def read_agilent_binary(fname, use_segments=False, include_time_vector=False, include_datetime=True):
    """Reads all the channel data from an Agilent/Infinium Oscilloscope into a dict
    indexed by scope channel number. Optionally computes the time vector, and adds that to
    the output dict also.
    https://github.com/FaustinCarter/agilent_read_binary"""
    with open(fname, 'rb') as f:
        file_header = np.fromfile(f, dtype=file_header_dtype, count=1)

        wf_dict = {}

        #Agilent uses 1-indexing for their waveforms
        for wfx in np.arange(file_header['num_waveforms'][0])+1:

            #Read the waveform header
            wf_header = np.fromfile(f, dtype=waveform_header_dtype, count=1)

            #Grab important strings in a python 2/3 compatible way
            channel_string = bytes(wf_header['waveform_string'][0]).decode('utf-8').replace(' ', '_')
            date_string = bytes(wf_header['date_string'][0]).decode('utf-8')
            time_string = bytes(wf_header['time_string'][0]).decode('utf-8')


            #Start a new dictionary
            wf_dict[channel_string] = {}

            #Might need to allow for multiple segments, in which case y_data is a dict
            if use_segments:
                wf_dict[channel_string]['segment_data'] = []
                segment_index = int(wf_header['segment_index'][0])
                time_tag = wf_header['time_tag'][0]

            #Fill with metadata
            for key in wf_header.dtype.names:
                if key not in ['header_size', 'waveform_type', 'num_waveform_buffers', 'segment_index', 'time_tag']:
                    wf_dict[channel_string][key] = wf_header[key][0]

            if include_datetime:
                datetime = dp.parse(date_string + ' ' + time_string)
                wf_dict[channel_string]['datetime'] = datetime

            #Loop through all the data buffers for this waveform (usually just one)
            for bfx in range(wf_header['num_waveform_buffers'][0]):
                #Read the buffer header
                bf_header = np.fromfile(f, dtype=buffer_header_dtype, count=1)

                #Format the dtype for the array
                bf_type = bf_header['buffer_type'][0]

                if bf_type in [1,2,3]:
                    #Float
                    f_str = 'f4'
                elif bf_type == 4:
                    #Integer
                    f_str = 'i4'
                else:
                    #Boolean or other
                    f_str = 'u1'

                ch_dtype = np.dtype([('data', f_str)])

                num_points = int(bf_header['buffer_size'][0]/bf_header['bytes_per_point'][0])

                #This hstacks buffers if there are more than one. Don't know if that is right or not...
                #Maybe should be vstacking them instead? Never seen more than one anyhow.
                if bfx == 0:
                    ch_data = np.fromfile(f, dtype=ch_dtype, count=num_points)
                else:
                    ch_data = np.hstack[[ch_data, np.fromfile(f, dtype=ch_dtype, count=num_points)]]

            assert num_points == len(ch_data), "Points mismatch in buffer!"

            if use_segments:
                y_data = {}
                y_data['segment_index'] = segment_index
                y_data['time_tag'] = time_tag
                y_data['y_data'] = ch_data['data']
                wf_dict[channel_string]['segment_data'].append(y_data)
            else:
                wf_dict[channel_string]['y_data'] = ch_data['data']

            if include_time_vector:
                #Build up the time vector
                if wfx == 1:
                    tvec = wf_header['x_increment'][0]*np.arange(wf_header['num_points'][0])+wf_header['x_origin']
                    wf_dict[channel_string]['x_data'] = tvec

                assert len(tvec) == len(ch_data), "The person who programmed this almost certainly handled the buffers wrong!"

    return wf_dict

def WriteKeysightCsv(filename, wf_dict):
    """Writes filename file in CSV format with data from dictionary wf_dict.
       CSV file will have header defined from Infiniium CSV format.     
    """
    import csv

    # for each waveform, create csv header.
    # note this is a not a flattened dictionary
    for channel in wf_dict.keys():
        
        y = wf_dict[channel]['y_data']
        x = wf_dict[channel]['x_data']
        y_inc = y[1]-y[0]
        y_disp_range = max(y)-min(y)
        y_disp_org = np.average(y)
        metadata = \
        "Revision:0\n" \
        "Type:interpolation\n" \
        "Start:0\n" \
        "Points:{points}\n" \
        "Count:{count}\n" \
        "XDispRange:{xdisprange}\n" \
        "XDispOrg:{xdisporg}\n" \
        "XInc:{xincrement}\n" \
        "XOrg:{xorg}\n" \
        "XUnits:{xunits}\n" \
        "YDispRange:{ydisprange}\n" \
        "YDispOrg:{ydisporg}\n" \
        "YInc:{yincrement}\n" \
        "YOrg:{yorg}\n" \
        "YUnits:{yunits}\n" \
        "YReference:1\n" \
        "Frame:{frame}\n" \
        "Date:{date}\n" \
        "Time:{time}\n" \
        "Max Bandwidth:62000000000\n" \
        "Min Bandwidth:0\n" \
        "Data:\n" \
        .format(points = wf_dict[channel]['num_points'], \
        count =  wf_dict[channel]['count'], \
        xdisprange =  wf_dict[channel]['x_display_range'], \
        xdisporg =  wf_dict[channel]['x_display_origin'], \
        xincrement =  wf_dict[channel]['x_increment'], \
        xorg = wf_dict[channel]['x_data'][0], \
        xunits =  num2units(wf_dict[channel]['x_units']), \
            
        ydisprange =  y_disp_range, \
        ydisporg =  y_disp_org, \
        yincrement =  y_inc, \
        yorg = wf_dict[channel]['y_data'][0], \
        yunits =  num2units(wf_dict[channel]['y_units']), \
            
        frame =  wf_dict[channel]['frame_string'].decode("utf-8"), \
        date =  wf_dict[channel]['date_string'].decode("utf-8"), \
        time =  wf_dict[channel]['time_string'].decode("utf-8")  )
        
        # open file to be written
        with open(filename, 'w', newline='', encoding='UTF8') as f:
            
            #write header to csv file
            f.write(metadata)
            
            #create csv writer
            writer = csv.writer(f)
            
            #cycle through each value
            for index, val in enumerate(x):
                
                #convert each vectorized value to scientific notation
                xval = np.format_float_scientific(val)
                yval = np.format_float_scientific(y[index])
                row = [xval, yval]
                
                # write x, y values to csv file
                writer.writerow(row)
        print(">>>File: {:} successfully written.".format(filename))
                        

def main():
    import argparse
    import os
    
    help_header = "\n" \
                  "Converts Infiniium Bin formatted waveform file to CSV formatted waveform file.\n"\
                  "\n" \
                  "Example:\n" \
                  "python bin2csv.py filename.bin"\
                  "\n" \
                  "or," \
                  "\n" \
                  "python bin2csv.py filename.bin --newfile foo.csv" \
                  "\n\n" \
                  "luis.boluna@keysight.com"

    parser = argparse.ArgumentParser(help_header)
    parser.add_argument('file', metavar = 'file', type=str, help = "The filename of the bin formatted waveform file")
    parser.add_argument('--newfile', type=str, required=False, help = "New filename if it is not same as original")
    args = parser.parse_args()
    
    dict = read_agilent_binary(args.file, include_time_vector=True)
    if args.newfile:
        WriteKeysightCsv(args.newfile, dict)
    else:
        ext = os.path.splitext(args.file)[-1]
        if ext == ".bin":
            filename = args.file.split(ext)[0] + '.csv'
            WriteKeysightCsv(filename, dict)
        else:
            raise ValueError('file extention: '+ext+' is not .bin. Throwing extention as safe guard to file overwrite')
    
if __name__ == "__main__":
        main()
 
        
        
