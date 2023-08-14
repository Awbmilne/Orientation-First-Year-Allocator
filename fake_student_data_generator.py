import csv
import random
from faker import Faker
from faker.providers import BaseProvider

class DepartmentProvider(BaseProvider):
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

student_faker = Faker()
student_faker.add_provider(DepartmentProvider)

with open('first_year_list.csv', mode='w', newline='') as file:
    writer = csv.writer(file)
    writer.writerow(['Fullname', 'Department'])

    for i in range(1600):
        writer.writerow([student_faker.name(), student_faker.department()])