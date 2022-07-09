# Infiniium Waveform File Format Converter

# bin2csv.py

bin2csv.py is a Python script to convert Infiniium bin waveform file format to the Infiniium CSV wavefrom file format.

## Installation

Use the github clone feature.

```shell
$ git clone https://github.com/YOUR-USERNAME/YOUR-REPOSITORY
```

## Usage

```shell

$ python bin2csv.py SinsoidalWaveform.bin

```

will create a SinusoidalWaveform.csv file.
 

or, one can specify the filename or the csv file

```shell

$ python bin2csv.py SinsoidalWaveform.bin --newfile Sine.csv

```

will create a Sine.csv file.

## Acknowledgements

Utilization of https://github.com/FaustinCarter/agilent_read_binary

## Contributing
Pull requests are welcome.

Plan is to expand to other file conversion formats as needed. 

## License
[MIT](https://choosealicense.com/licenses/mit/)
