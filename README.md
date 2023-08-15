# First Year Allocator

This repository contains a script to allocate first years based on 2 primary goals:
- Ensure Colour Team counts are as even as possible
- Evenly distribute FYs from each deparment to the relevant colour teams

The Colour teams and available departments should be specified in the [`colour_teams.json`](./colour_teams.json) file. An example of the file is provided as [`colour_teams.example.json`](./colour_teams.example.json).

The First Year input should be specified in the [`first_year_list.csv`](./first_year_list.csv) file. An example of the file is provided as [`first_year_list.example.csv`](./first_year_list.example.csv).

The SQL template is specified in the [`fy-query.template.sql`](./fy-query.template.sql) file. It is set up for the website database as initially created in 2023. Ensure the database config and Query parameters align for any future versions of the website.

The script, [`first-years-allocate.py`](./first-years-allocate.py), will output two files:
- [`fy-query.sql`](./fy-query.sql) file which can be used to write the FYs into an SQL database
- [`allocated_firts_years.csv`](./allocated_firts_years.csv) file which contains a CSV list of the first years and their allocated colour teams
