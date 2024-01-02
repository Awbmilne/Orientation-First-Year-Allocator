import csv
import string
import random
from faker import Faker
from faker.providers import BaseProvider
import argparse
class DepartmentProvider(BaseProvider):
    # Roughly based on the number of incoming students in 2023
    # Useful for testing the allocator application, and can be adjusted to match
    # the actual numbers for your year if you want to test that allocation will
    # work. DOES NOT PRODUCE EXACT COUNTS, it just balances the odds of
    # generation!!!
    DEPARTMENTS: list[[str, int]] = [
        ['arch', 0],
        ['ae',   407],
        ['bme',  444],
        ['chem', 622],
        ['civ',  559],
        ['ece',  1466+388],
        ['env',  277],
        ['geo',  48],
        ['mgmt', 459],
        ['mech', 1009],
        ['tron', 1128],
        ['nano', 525],
        ['se',   620],
        ['syde', 519]
    ]
    
    def department(self):
        PROBABILITIES: list[float] = [(d[0], d[1]/sum(n for _,n in self.DEPARTMENTS))for d in self.DEPARTMENTS]
        return random.choices([d[0] for d in PROBABILITIES], weights=[d[1] for d in PROBABILITIES], k=1)[0]

    def watiam(self):
        letters = string.ascii_lowercase
        return ''.join(random.choice(letters) for i in range(8))

student_faker = Faker()
student_faker.add_provider(DepartmentProvider)

def generate_student_data(num_students, output_file):
    # Generate a list of students
    students = []
    for i in range(num_students):
        # Generate a unique watiam
        watiam = student_faker.watiam()
        while watiam in [s[2] for s in students]:
            watiam = student_faker.watiam()
        # Append the new student to the list
        students.append([student_faker.name(), student_faker.department(), watiam])
    
    # Write the list to a csv file
    with open(output_file, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Fullname', 'Department', 'Watiam'])
        for student in students:
            writer.writerow(student)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Generate fake student data.', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-o', '--output', type=str, help='Output file name', default='generated_fy_list.csv')
    parser.add_argument('-s', '--students', type=int, help='Number of students to generate', default=1700)
    
    args = parser.parse_args()

    generate_student_data(args.students, args.output)
