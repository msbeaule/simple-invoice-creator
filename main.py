from datetime import date
import json, csv, math
import decimal
from decimal import Decimal

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

from filters import j2_round_float_to_two

# setting up rounding for decimals
ctx = decimal.getcontext()
ctx.rounding = decimal.ROUND_HALF_UP


with open("customers.json") as customer_file:
    customers = customer_file.read()
    customer = json.loads(customers)[1]

class DurationSplit:
    SIXTY = 60

    def __init__(self) -> None:
        pass
    
    def add_two_together(self, dur1, dur2):
        time = dur1.split(":")
        time2 = dur2.split(":")
        # print(time)
        # print(time2)

        minutes_to_add = 0
        hours_to_add = 0

        seconds = int(time[2]) + int(time2[2])
        seconds, minutes_to_add = self._get_time_and_remaining(seconds)

        minutes = int(time[1]) + int(time2[1])
        minutes = minutes + minutes_to_add
        minutes, hours_to_add = self._get_time_and_remaining(minutes)

        hours = int(time[0]) + int(time2[0])
        hours = hours + hours_to_add

        # print(f'{hours:02}:{minutes:02}:{seconds:02}')

        return f'{hours:02}:{minutes:02}:{seconds:02}'
    
    def set_prices_from_durations(self, items):
        for item in items:
            time = item["duration"].split(":")
            # seconds don't matter for this
            # minutes get +1 to account for seconds

            minutes = int(time[1])
            minutes = (minutes) / self.SIXTY
            hours = int(time[0])

            item["price"] = round(Decimal((hours + minutes) * item["rate"]), 2)
    
    def set_all_rates(self, items):
        for item in items:
            #TODO: check tag for each to check for different rate for one task, otherwise, just assign based on the rate from the project

            item["rate"] = customer["default_rate"]

    def get_total_balance(self, items):
        balance = 0
        for item in items:
            balance = balance + item["price"]
        
        return balance

    
    def __add_all_together(self, items):
        seconds, minutes, hours = 0
        minutes_to_add, hours_to_add = 0

        for item in items:
            time = item["duration"].split(":")
            seconds = seconds + int(time[2])
            minutes = minutes + int(time[1])
            hours = hours + int(time[0])
        
        seconds, minutes_to_add = self._get_time_and_remaining(seconds)
        minutes = minutes + minutes_to_add
        minutes, hours_to_add = self._get_time_and_remaining(minutes)
        hours = hours + hours_to_add

        return hours, minutes, seconds

    def _get_time_and_remaining(self, duration):
        to_add = 0
        
        if duration > self.SIXTY:
            to_add = math.floor(duration / self.SIXTY)
            duration = duration % self.SIXTY
        return duration, to_add


def make_pdf(items, balance):
    env = Environment(loader=FileSystemLoader('.'))
    # adding custom filter
    env.filters["round_float"] = j2_round_float_to_two
    template = env.get_template("invoice.html")

    html_out = template.render(customer=customer, invoiceNumber="2023-0001", date="today", items=items, balance=balance)

    HTML(string=html_out).write_pdf("invoice.pdf", stylesheets=["invoice.css"])

def find_duplicates_with_same_description_edit(results, item, index):
    for search_index in range(index + 1, len(results)):
        if (item["project"] == customer["aliases"][0] and item["deleted"] == False):
            if item["task"] == results[search_index]["task"] and \
                item["description"] == results[search_index]["description"]:
                # print("HIT")
                # print(results[search_index]["description"])
                results[search_index]["deleted"] = True
                new_duration = duration.add_two_together(item["duration"], results[search_index]["duration"])
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

# have these work for each company, right now it's just the full list
duration.set_all_rates(results)
duration.set_prices_from_durations(results)

for x, item in enumerate(results):
    if (item["project"] == customer["aliases"][0] and item["deleted"] == False):
        find_duplicates_with_same_description_edit(results, item, x)

print(f'length before: {len(results)}')

# create a new list without all the items that were deleted bc they were duplicates
finished_list = list(filter(lambda a: a["deleted"] != True, results))

balance = duration.get_total_balance(finished_list)

print(f'length after: {len(finished_list)}')

# make a demo pdf only using the data from a certain project/customer
make_pdf( list(filter(lambda a: a["project"] == customer["aliases"][0], finished_list)), balance )
