
import json
import numpy as np
import pandas as pd
import scipy.optimize as opt

TEAMS_JSON_FILE = './colour_teams.json'
FY_CSV_FILE = './first_year_list.csv'

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

first_year_counts = np.zeros((len(teams), len(departments)))


# DEFINE THE OPTIMIZATION PROBLEM ───────────────────────────────────────────────── #

# Target function
def allocation_scoring(y):
    x = np.reshape(y, (len(teams), len(departments))) # Reshape the input array into a 2D array
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
for i, dept in enumerate(departments):
    opt.LinearConstraint(np.ndarray.flatten(department_identity[dept]), 0, 0)

# Constrain the total number of students in each department to the actual number of students
for i, dept in enumerate(departments):
    opt.NonlinearConstraint(lambda y: {
        (np.reshape(y, (len(teams), len(departments))) * department_identity[dept]).sum(axis=1)
        }, department_counts, department_counts)
    
res = opt.minimize(allocation_scoring, np.ndarray.flatten(first_year_counts), constraints=constraints)
print(res)
exit()


# Output the list of First Year department count per colour team
# counts = pd.DataFrame(first_year_counts, index=teams, columns=departments) # Create printable dataframe with named rows and columns
counts = pd.DataFrame(team_departments, index=teams, columns=departments) # Create printable dataframe with named rows and columns
counts = counts.astype(int) # Convert all values to integer, for cleaner output
print('Colour Team Allocations:')
print(counts)

# Print out list of department sums
print('\nDepartment Sums:')
print(counts.sum(axis=0))

# Print out list of team sums
print('\nTeam Sums:')
print(counts.sum(axis=1))
