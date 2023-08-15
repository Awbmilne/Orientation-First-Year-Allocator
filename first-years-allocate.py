
import csv
import json
import random
import numpy as np
import jinja2 as j2
import pandas as pd
import scipy.optimize as opt
from gekko import GEKKO
m = GEKKO()

TEAMS_JSON_FILE = './colour_teams.json'
FY_CSV_FILE = './first_year_list.csv'
FY_OUT_CSV_FILE = './allocated_first_years.csv'
SQL_TEMLPATE_FILE = './fy-query.template.sql'
SQL_OUT_FILE = './fy-query.sql'

# CREATE TEAMS INFORMATION FROM JSON FILE ───────────────────────────────────────── #
 
# Read the 'teams' array from the json file
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
first_years = pd.read_csv(FY_CSV_FILE, header=0)

# Create a list of department counts
department_counts = {}
for dept in departments:
    department_counts[dept] = first_years[first_years["Department"] == dept].shape[0]
    
# Create a dictionary of FYs by department
fy_by_dept = {}
for dept in departments:
    fy_by_dept[dept] = [fy for _, fy in first_years.iterrows() if fy['Department'] == dept]


# DEFINE THE TARGET ARRAY ───────────────────────────────────────────────────────── #
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
    
# res = opt.minimize(allocation_scoring, np.ndarray.flatten(first_year_counts), constraints=constraints)
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
m.solve(disp=False)

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

# Print out list of department sums and targets
print('\nDepartment Sums:')
dept_stats = pd.DataFrame.from_dict(department_counts, orient='index', columns=['Target'])
dept_stats['Actual'] = counts.sum(axis=0)
print(dept_stats)


# ASSIGN FYS TO COLOUR TEAMS ────────────────────────────────────────────────────── #
fy_by_colour_team = {}
for i, team in enumerate(teams):
    fy_by_colour_team[team] = []
    for j, dept in enumerate(departments):
        for k in range(first_year_counts_int[i][j]):
            fy_by_colour_team[team].append(fy_by_dept[dept].pop(random.randint(0, len(fy_by_dept[dept])-1)))

# Output the list of FYs with Colour Teams Added
with open(FY_OUT_CSV_FILE, 'w') as file:
    csv_writer = csv.writer(file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL, lineterminator='\n')
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
with open(SQL_TEMLPATE_FILE, 'r') as file:
    sql_template = j2.Template(file.read())
    
with open(SQL_OUT_FILE, 'w') as file:
    file.write(sql_template.render(fy_list=fy_list))
