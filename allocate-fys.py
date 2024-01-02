# Standard Imports
import os
import sys
import csv
import json
import random
import argparse
from argparse import RawTextHelpFormatter

# Non-Standard Imports
import click
import numpy as np
import jinja2 as j2
import pandas as pd
import scipy.optimize as opt
from gekko import GEKKO

# PARSE COMMAND LINE ARGUMENTS ──────────────────────────────────────────────────── #
parser = argparse.ArgumentParser(description= \
"""
Allocate first-year students to color teams.

Takes a list of first-year students and allocates them to color teams based on \
there departments. The allocation is done using a mixed integer non-linear \
programming solver. I operates by minimizing the total difference between \
the number of students on each team and the difference in the number of students \
from each department on each team. For example, if there are 1000 total students \
on 10 teams, it will try to put 100 on each, and if there are 100 Mechanical students \
split between 2 teams, the allocation will try to get 50 Mechanical students on \
each team. Best efforts are made by the optimizer to get as close to the target \
as possible, but it is not guaranteed to be exact. Generally, the weighting of \
total team size is greater than the inbalance of department size, so the total \
team size will be closer to the target than the department size.

Output is either in the format of a CSV file with the allocated first-years, or \
a SQL query file that can be used to insert the allocated first-years into a \
database. The SQL query file is generated from a jinja2 template file, which can be \
modified to match the database schema. Refer to the example template file \
(fy-query.example.sql.jinja2) for more information.

If only the --csv-out, --sql, and --sql-out arguments are given, the program will \
convert the CSV file to a SQL query file. This is useful if you generated the csv file \
already, but didnt generate the SQL query along side it. It prevents you having to re-run \
the allocation algorithm, which might be helpful if you already started the implement the \
allocations in some way (ex. FY Shirt numbers). The program WILL NOT RUN THE ALLOCATION \
ALGORITHM if only these arguments are given.
""", formatter_class=RawTextHelpFormatter)

parser.epilog = \
"""
Example Allocation: python allocate-fys.py --teams colour-teams.example.json --fy fy-list.example.csv --csv-out allocated_first_years.example.csv --sql fy-query.sql.jinja2 --sql-out fy-query.example.sql

Example CSV -> SQL Conversion: python allocate_fys.py --csv-out allocated_first_years.example.csv --sql fy-query.sql.jinja2 --sql-out fy-query.example.sql
"""

parser.add_argument('--teams', type=str, help='Path to the teams JSON file', required=False)
parser.add_argument('--fy', type=str, help='Path to the first-year CSV file', required=False)
parser.add_argument('--csv-out', type=str, help='Path to the allocated first-years CSV file', required=False)
parser.add_argument('--sql', type=str, help='Path to the SQL query template file [requires --sql-out]', required=False)
parser.add_argument('--sql-out', type=str, help='Path to the generated SQL query file [requires --sql]', required=False)

# Show help menu if no arguments are given
if len(sys.argv) == 1:
    parser.print_help()
    exit()

args = parser.parse_args()

# Require either --csv-out or --sql-out
if (args.csv_out is None) and ((args.sql_out is None) or (args.sql is None)):
    parser.error('Must specify either --csv-out or --sql & --sql-out')
    exit()
    
# Require --sql if --sql-out is given, and vice versa
if (args.sql_out is not None) and (args.sql is None) or \
   (args.sql is not None) and (args.sql_out is None):
    parser.error('Must specify both --sql & --sql-out')
    exit()

# CONVERT CSV OUTPUT FILE TO SQL QUERY ──────────────────────────────────────────── #

# Convert csv output file to sql query if inputs are not given, but csv and sql args are.
if (args.teams is None) \
  and (args.fy is None) \
  and (args.csv_out is not None) \
  and (args.sql is not None) \
  and (args.sql_out is not None):
    print('Converting CSV output file to SQL query file...')
    # Check if the output file exists and ask user if they want to overwrite it
    if os.path.exists(args.sql_out):
        if not click.confirm('WARNING: File already exists. Overwrite?', default=False):
            exit()
    # Read the SQL Template file
    with open(args.sql, 'r') as file:
        sql_template = j2.Template(file.read())
    # Read in the FY list from the output CSV file
    with open(args.csv_out, 'r') as file:
        fy_list = []
        csv_reader = csv.reader(file, delimiter=',')
        header = next(csv_reader)
        for row in csv_reader:
            fy_list.append({header[i]: row[i] for i in range(len(header))})
    # Write the SQL query file
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(args.sql_out, 'w') as file:
        file.write(sql_template.render(fy_list=fy_list, timestamp=timestamp))
    print('Done.')
    exit()
        
# CREATE TEAMS INFORMATION FROM JSON FILE ───────────────────────────────────────── #

# Convert args to variables
TEAMS_JSON_FILE = args.teams
FY_CSV_FILE = args.fy
FY_OUT_CSV_FILE = args.csv_out
SQL_TEMLPATE_FILE = args.sql
SQL_OUT_FILE = args.sql_out

# Check if the CSV output file exists and ask user if they want to overwrite it
if FY_OUT_CSV_FILE is not None:
    if os.path.exists(FY_OUT_CSV_FILE):
        if not click.confirm(f"WARNING: Output File '{FY_OUT_CSV_FILE}'already exists. Overwrite?", default=False):
            exit()
            
# Check if the SQL output file exists and ask user if they want to overwrite it
if SQL_OUT_FILE is not None:
    if os.path.exists(SQL_OUT_FILE):
        if not click.confirm(f"WARNING: Output File '{SQL_OUT_FILE}'already exists. Overwrite?", default=False):
            exit()

# Read the 'teams' array from the json file
print('Injesting teams data...')
with open(TEAMS_JSON_FILE, 'r') as f:
    teams_dict = json.load(f)['teams']

# Create a list of possible departments from the teams array
departments = []
teams = []
for team in teams_dict:
    teams.append(team['Colour'])
    for dept in team['Departments']:
        if dept not in departments:
            departments.append(dept)
departments.sort()
teams.sort()

# Create a indentity matrix for departments in each team
team_departments = np.zeros((len(teams), len(departments)))
for i, team_colour in enumerate(teams):
    team_entry = next(team for team in teams_dict if team['Colour'] == team_colour)
    for dept in team_entry['Departments']:
        j = departments.index(dept)
        team_departments[i][j] = 1

# Create dictionary of identity matricies for each department
department_identity = {}
for dept in departments:
    department_identity[dept] = np.zeros((len(teams), len(departments)))
    for i, team in enumerate(teams):
        if dept in [entry for entry in teams_dict if entry['Colour'] is team][0]['Departments']:
            j = departments.index(dept)
            department_identity[dept][i][j] = 1

# CREATE FIRST YEAR INFORMATION FROM FY LIST ────────────────────────────────────── #
# Import values from csv file
print('Injesting first-year data...')
first_years = pd.read_csv(FY_CSV_FILE, header=0)

# Check that coloumns are correct
if list(first_years.columns) != ['Fullname', 'Department', 'Watiam']:
    raise Exception('ERROR: CSV file does not have correct columns. Must have columns: Fullname, Department, Watiam')
    exit()

# Create a list of department counts
department_counts = {}
for dept in departments:
    department_counts[dept] = first_years[first_years["Department"] == dept].shape[0]

# Check that all FYs have been matched with a department
if sum(department_counts.values()) != len(first_years):
    raise Exception("ERROR: Some FYs have not been matched with a department")
    exit()
    
# Create a dictionary of FYs by department
fy_by_dept = {}
for dept in departments:
    fy_by_dept[dept] = [fy for _, fy in first_years.iterrows() if fy['Department'] == dept]


# DEFINE THE TARGET ARRAY ───────────────────────────────────────────────────────── #
print('Configuring optimization problem...')
m = GEKKO() # Initialize gekko
first_year_counts = m.Array(m.Var, (len(teams), len(departments)), lb=0, ub=1000, integer=True) # Create an array of variables for the number of first years in each department on each team


# DEFINE THE OPTIMIZATION PROBLEM ───────────────────────────────────────────────── #
# Target function
def allocation_scoring(x):
    score = 0
    """
    Take the sum of the squared differences between the actual and the average of FY dept. count / available dept. teams
    Goal: Minimize the difference in count of FYs from one deparment in various teams.
    Example: If 2 teams can have MECH and there are 100 MECH students, get as close to 50 on each team as possible.
    """
    # Iterate through every department
    for i, dept in enumerate(departments):
        dept_count = department_counts[dept] # Get the number of students in the department
        dept_team_count = department_identity[dept].sum() # Get the number of teams that can have the department
        dept_avg = dept_count / dept_team_count # Get the target average number of students per available team
        dept_students = x * department_identity[dept] # Get the colour team FY array for the department
        # Iterate through the teams
        for j, team in enumerate(teams):
            score += (dept_students[j][i] - dept_avg)**2 # Add the squared difference between the actual and the average to the score
    
    """
    Take the sum of the cubed differences between the actual and the average of FY count / available teams
    Goal: Keep the size of all the colour teams as even as possible.
    Example: If 10 colour teams and 1000 students, get as close to 100 students on each team as possible.
    """
    team_count_avg = len(first_years) / len(teams) # Get the target average number of students per team
    # Iterate through the teams
    for i, team in enumerate(teams):
        team_count = x.sum(axis=1)[i] # Get the number of students in the team
        score += abs((team_count - team_count_avg)**3) # Add the absolute value of the cubed difference between the actual and the average to the score
    
    """
    Return the total score (higher is worse)
    """
    return score


# DEFINE THE CONTRAINTS FOR THE SYSTEM ──────────────────────────────────────────── #
constraints = []
# Contrain disallowed departments on colour teams to 0
for i, row in enumerate(team_departments):
    for j, val in enumerate(row):
        if (val == 0):
            m.Equation(first_year_counts[i][j] == 0)

# Constrain the total number of students in each department to the actual number of students
for i, dept in enumerate(departments):
    m.Equation((first_year_counts * department_identity[dept]).sum() == department_counts[dept])
    
m.Minimize(allocation_scoring(first_year_counts))
m.options.SOLVER=1
m.solver_options=['minlp_maximum_iterations 1000', \
                  # minlp iterations with integer solution
                  'minlp_max_iter_with_int_sol 100', \
                  # treat minlp as nlp
                  'minlp_as_nlp 0', \
                  # nlp sub-problem max iterations
                  'nlp_maximum_iterations 50', \
                  # 1 = depth first, 2 = breadth first
                  'minlp_branch_method 1', \
                  # maximum deviation from whole number
                  'minlp_integer_tol 0.001', \
                  # covergence tolerance
                  'minlp_gap_tol 0.001']
print('Running optimization problem...')
m.solve(disp=True)

# Output the list of First Year department count per colour team
first_year_counts_int = [ [0]*len(departments) for i in range(len(teams))]
for i, row in enumerate(first_year_counts):
    for j, val in enumerate(row):
        first_year_counts_int[i][j] = int(val.VALUE[0])
counts = pd.DataFrame(first_year_counts_int, index=teams, columns=departments) # Create printable dataframe with named rows and columns
counts['Sum'] = counts.sum(axis=1)
pd.set_option('display.max_colwidth', None)
print('Colour Team Allocations:')
print(counts)

# DEBUGGING: Print out list of department sums and targets
# print('\nDepartment Sums:')
# dept_stats = pd.DataFrame.from_dict(department_counts, orient='index', columns=['Target'])
# dept_stats['Actual'] = counts.sum(axis=0)
# print(dept_stats)

# ASSIGN FYS TO COLOUR TEAMS ────────────────────────────────────────────────────── #
fy_by_colour_team = {}
for i, team in enumerate(teams):
    fy_by_colour_team[team] = []
    for j, dept in enumerate(departments):
        for k in range(first_year_counts_int[i][j]):
            fy_by_colour_team[team].append(fy_by_dept[dept].pop(random.randint(0, len(fy_by_dept[dept])-1)))

# Output the list of FYs with Colour Teams Added
if FY_OUT_CSV_FILE is not None:
    with open(FY_OUT_CSV_FILE, 'w') as file:
        csv_writer = csv.writer(file, delimiter=',', quoting=csv.QUOTE_NONE, lineterminator='\n')
        # Write the header row
        header = first_years.columns.tolist()
        header.append('Colour Team')
        csv_writer.writerow(header)
        # Write fy data
        fy_list = []
        for team in fy_by_colour_team:
            for fy in fy_by_colour_team[team]:
                vals = [fy[key] for key in fy.keys()]+[team]
                csv_writer.writerow(vals)
                fy_list.append({header[i]: vals[i] for i in range(len(header))})

# Fill out SQL query template with FY information
if SQL_OUT_FILE is not None:
    with open(SQL_TEMLPATE_FILE, 'r') as file:
        sql_template = j2.Template(file.read())
        
    timestamp = pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(SQL_OUT_FILE, 'w') as file:
        file.write(sql_template.render(fy_list=fy_list, timestamp=timestamp))
