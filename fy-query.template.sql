
-- Clear existing FYs
DELETE FROM students where position = 'fy';

-- Insert FYs into students table
INSERT INTO students (watiam, fullname, department, colour_team)
VALUES
    {%- for fy in fy_list %}
        ("{{fy['Watiam']}}", "{{fy['Fullname']}}", "{{fy['Department']}}", "{{fy['Colour Team']}}"){% if loop.last %};{%else%},{% endif %}
    {%- endfor %}
