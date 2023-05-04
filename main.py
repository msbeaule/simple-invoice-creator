from datetime import date
import json, csv, math

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

with open("customers.json") as customer_file:
    customers = customer_file.read()
    customer = json.loads(customers)[1]

class DurationSplit:
    SECONDS = 60
    MINUTES = 60

    def __init__(self) -> None:
        pass
    
    def addTogether(self, dur1, dur2):
        time = dur1.split(":")
        time2 = dur2.split(":")
        # print(time)
        # print(time2)

        minutes_to_add = 0
        hours_to_add = 0

        seconds = int(time[2]) + int(time2[2])
        if seconds > self.SECONDS:
            minutes_to_add = math.floor(seconds / self.SECONDS)
            seconds = seconds % self.SECONDS

        minutes = int(time[1]) + int(time2[1])
        minutes = minutes + minutes_to_add
        if minutes > self.MINUTES:
            hours_to_add = math.floor(minutes / self.MINUTES)
            minutes = minutes % self.MINUTES

        hours = int(time[0]) + int(time2[0])
        hours = hours + hours_to_add

        # print(f'{hours:02}:{minutes:02}:{seconds:02}')

        return f'{hours:02}:{minutes:02}:{seconds:02}'
    

def make_pdf(items):
    env = Environment(loader=FileSystemLoader('.'))
    template = env.get_template("invoice.html")

    html_out = template.render(customer=customer, invoiceNumber="2023-0001", date="today", items=items)

    HTML(string=html_out).write_pdf("invoice.pdf", stylesheets=["invoice.css"])

def find_duplicates_with_same_description_edit(results, item, index):
    for search_index in range(index + 1, len(results)):
        if (item["project"] == customer["aliases"][0] and item["deleted"] == False):
            if item["task"] == results[search_index]["task"] and \
                item["description"] == results[search_index]["description"]:
                # print("HIT")
                # print(results[search_index]["description"])
                results[search_index]["deleted"] = True
                new_duration = duration.addTogether(item["duration"], results[search_index]["duration"])
                item["duration"] = new_duration



duration = DurationSplit()

with open("2023-04.csv", "r") as f:
    results = [
        {
            "project": row["Project"],
            "task": row["Task"],
            "description": row["Description"],
            "duration": row["Duration"],
            "tags": row["Tags"],
            "deleted": False,
            
        }
        for row in csv.DictReader(f)
    ]

    #print(json.dumps(results))

for x, item in enumerate(results):
    if (item["project"] == customer["aliases"][0] and item["deleted"] == False):
        find_duplicates_with_same_description_edit(results, item, x)

print(f'length before: {len(results)}')

# create a new list without all the items that were deleted bc they were duplicates
finished_list = list(filter(lambda a: a["deleted"] != True, results))

print(f'length after: {len(finished_list)}')

# make a demo pdf only using the data from a certain project/customer
make_pdf( list(filter(lambda a: a["project"] == customer["aliases"][0], results)) )
