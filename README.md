# First Year Allocator

This repository contains a script to allocate first years based on 2 primary goals:

- Ensure Colour Team counts are as even as possible
- Evenly distribute FYs from each deparment to the relevant colour teams

## Python Package Dependencies
To install the required python packages, run the following command:
``` bash
pip install -r requirements.txt
```

## Usage
``` bash
# Run the script
python allocate-fys.py [ARGUEMENTS]

# Get the help message (this will show all the arguments and more documentation)
python allocate-fys.py --help
```

## Fake Student Generator
This repo also contains a fake student generator to generate fake students for testing the application. The generator can be run using the following command:
``` bash
python fake-fy-gen.py
# or, you can specify the students and output file.
python fake-fy-gen.py -s [NUMBER OF STUDENTS] -o [OUTPUT FILE]

# Get the help message
python fake-fy-gen.py --help
```
