# First Year Allocator

This repository contains a non-linear solving script to allocate first years to orientation colour teams based on 2 primary goals:

- Ensure Colour Team counts are as even as possible
- Evenly distribute FYs from each deparment to the relevant colour teams

This was designed for Waterloo engineering orientation, so is tailored to that specific use case and desired student distribution scheme.

## Table of Contents
- [First Year Allocator](#first-year-allocator)
  - [Table of Contents](#table-of-contents)
  - [Technical Information](#technical-information)
    - [Python Package Dependencies](#python-package-dependencies)
    - [Usage](#usage)
    - [Fake Student Generator](#fake-student-generator)
  - [Example Usage](#example-usage)


## Technical Information

### Python Package Dependencies
To install the required python packages, run the following command:
``` bash
pip install -r requirements.txt
```

### Usage
``` bash
# Run the script
python allocate-fys.py [ARGUEMENTS]

# Get the help message (this will show all the arguments and more documentation)
python allocate-fys.py --help
```

Help message:

```
> python allocate-fys.py --help
usage: allocate-fys.py [-h] [--teams TEAMS] [--fy FY] [--csv-out CSV_OUT] [--sql SQL] [--sql-out SQL_OUT]

Allocate first-year students to color teams.

Takes a list of first-year students and allocates them to color teams based on there departments. The allocation is done using a mixed integer non-linear programming solver. I operates by minimizing the total difference between the number of students on each team and the difference in the number of students from each department on each team. For example, if there are 1000 total students on 10 teams, it will try to put 100 on each, and if there are 100 Mechanical students split between 2 teams, the allocation will try to get 50 Mechanical students on each team. Best efforts are made by the optimizer to get as close to the target as possible, but it is not guaranteed to be exact. Generally, the weighting of total team size is greater than the inbalance of department size, so the total team size will be closer to the target than the department size.

Output is either in the format of a CSV file with the allocated first-years, or a SQL query file that can be used to insert the allocated first-years into a database. The SQL query file is generated from a jinja2 template file, which can be modified to match the database schema. Refer to the example template file (fy-query.example.sql.jinja2) for more information.



If only the --csv-out, --sql, and --sql-out arguments are given, the program will convert the CSV file to a SQL query file. This is useful if you generated the csv file already, but didnt generate the SQL query along side it. It prevents you having to re-run the allocation algorithm, which might be helpful if you already started the implement the allocations in some way (ex. FY Shirt numbers). The program WILL NOT RUN THE ALLOCATION ALGORITHM if only these arguments are given.

options:
  -h, --help         show this help message and exit
  --teams TEAMS      Path to the teams JSON file
  --teams TEAMS      Path to the teams JSON file
  --fy FY            Path to the first-year CSV file
  --csv-out CSV_OUT  Path to the allocated first-years CSV file
  --sql SQL          Path to the SQL query template file [requires --sql-out]
  --sql-out SQL_OUT  Path to the generated SQL query file [requires --sql]

Example Allocation: python allocate-fys.py --teams colour-teams.example.json --fy fy-list.example.csv --csv-out allocated_first_years.example.csv --sql fy-query.sql.jinja2 --sql-out fy-query.example.sql        

Example CSV -> SQL Conversion: python allocate-fys.py --csv-out allocated_first_years.example.csv --sql fy-query.sql.jinja2 --sql-out fy-query.example.sql
```

### Fake Student Generator
This repo also contains a fake student generator to generate fake students for testing the application. The generator can be run using the following command:
``` bash
python fake-fy-gen.py
# or, you can specify the students and output file.
python fake-fy-gen.py -s [NUMBER OF STUDENTS] -o [OUTPUT FILE]

# Get the help message
python fake-fy-gen.py --help
```

Help Message:
```
> python fake-fy-gen.py --help
usage: fake-fy-gen.py [-h] [-o OUTPUT] [-s STUDENTS]

Generate fake student data.

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output file name (default: generated-fy-list.csv)
  -s, --students STUDENTS
                        Number of students to generate (default: 1700)
```


## Example Usage

To start the example, lets create a fake student list to work from:

```
python fake-fy-gen.py -s 1753 -o fy-list-example.csv
```

This should generate a file of fake students that looks like this:

**fy-list-example.csv**
``` csv
Fullname,Department,Watiam
Richard Walker,ece,tltkcozs
Charlene Kline,tron,qlexuyzz
Casey Morrison,nano,mochzdym
Craig Sims,ece,kjhjjngj
Andrew Salazar,ece,lcptzcxp
Janet Lane,syde,kdleqaux
...
```

When running on a real student list, follow this same format to ensure the system works as expected.

Next, we need to create our colour team descriptor file. This is a simple JSON file with a list of the colour teams and what departments should be included on that team. This should be determined ahead of time by doing some estimates on department size and team size and splitting them somewhat evenly. Here is an example of the format:

**colour-teams.example.json**
```json
{
    "teams":
    [
        {
            "Colour": "Light Red",
            "Departments": ["civ", "mech", "nano", "tron"]
        },
        {
            "Colour": "Light Orange",
            "Departments": ["ece", "mgmt", "nano", "tron"]
        },
        ...
    ]
}
```

As the final prep, we need to format our SQL query template. The existing template provides a queary in this format:
```sql
-- Clear existing FYs
DELETE FROM students where position = 'fy';

-- Insert FYs into students table
INSERT INTO students (watiam, fullname, department, colour_team)
VALUES
        ("kcozaecw", "Clayton Harris", "bme", "Dark Blue"),
        ("dvrkcmpq", "David Smith Jr.", "bme", "Dark Blue"),
        ("lhxgtgap", "Taylor Brown", "bme", "Dark Blue"),
        ...
```

Ensure this is relevant to the existing database and modify the template as needed. The template uses Jinja2 formatting, refer to docs here (https://jinja.palletsprojects.com/en/stable/templates/).

With all that out of the way, we can start allocating!

Run the allocator with your created CSV and JSON files, include the SQL template and desired output file names. The allocator will do its magic and generate the files. It should give you an output array showing the number of each department in each colour team:

```
Colour Team Allocations:
              ae  bme  chem  civ  ece  env  geo  mech  mgmt  nano  se  syde  tron  Sum
Dark Blue      0    8     0    0   34    0    0    27     0     0   0     0    21   90
Dark Brown     9    0     0   32   31    0    0     0     0     0   0     0    19   91
Dark Green     0    0     0   28   26    0    0    22     0     0   0     0    15   91
Dark Orange    0    0    14   28   28    0    0    21     0     0   0     0     0   91
Dark Orange    0    0    14   28   28    0    0    21     0     0   0     0     0   91
Dark Pink      0    0    25    0    0    0    0    33    11     0   0    18     0   87
Dark Purple    0    0    16    0   31    0    0    25     0     0   0     0    18   90
Dark Red       0    0     0    0   33    0    0     0     0    24   0    14    20   91
Dark Teal      0   11     0    0   37    0    0    31     9     0   0     0     0   88
Dark Yellow    0   29     0    0    0   23    6     0    27     0   0     0     0   85
Light Blue    21   17     0    0    0    0    0     0    15     0  34     0     0   87
Light Brown    0    0     0    0    0    8    0     0     0    31   0    20    28   87
Light Green   17   13     0    0   39    0    0     0     0     0   0    18     0   87
Light Orange   0    0     0    0   38    0    0     0     5    26   0     0    22   91
Light Pink     0    0     0    0   33    0    0     0     0     0  25    12    20   90
Light Purple   0    0    22    0    0    6    0    31     0     0  29     0     0   88
Dark Orange    0    0    14   28   28    0    0    21     0     0   0     0     0   91
Dark Pink      0    0    25    0    0    0    0    33    11     0   0    18     0   87
Dark Purple    0    0    16    0   31    0    0    25     0     0   0     0    18   90
Dark Red       0    0     0    0   33    0    0     0     0    24   0    14    20   91
Dark Teal      0   11     0    0   37    0    0    31     9     0   0     0     0   88
Dark Yellow    0   29     0    0    0   23    6     0    27     0   0     0     0   85
Light Blue    21   17     0    0    0    0    0     0    15     0  34     0     0   87
Light Brown    0    0     0    0    0    8    0     0     0    31   0    20    28   87
Light Green   17   13     0    0   39    0    0     0     0     0   0    18     0   87
Light Orange   0    0     0    0   38    0    0     0     5    26   0     0    22   91
Light Pink     0    0     0    0   33    0    0     0     0     0  25    12    20   90
Light Purple   0    0    22    0    0    6    0    31     0     0  29     0     0   88
Light Red      0    0     0   30    0    0    0    23     0    20   0     0    17   90
Light Teal    11    0     0    0   33    0    0     0     0     0  25     0    21   90
Light Yellow   0   18    29    0    0    0    0     0    16     0   0    23     0   86
```
This can be helpful in ensuring the allocation worked as expected.

With the files generated, you can now use the allocated list CSV in Excel to cross-reference students colour teams and generate a list for each team. You can also use the SQL query to quickly add all the FYs to the orientation website!

Best of Luck!