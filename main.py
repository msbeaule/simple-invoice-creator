from datetime import date
from dateutil.relativedelta import relativedelta

import json, csv, math
import decimal
from decimal import Decimal

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

from filters import j2_round_float_to_two

# setting up rounding for decimals
ctx = decimal.getcontext()
ctx.rounding = decimal.ROUND_HALF_UP


with open("customers.json") as file:
    customers = file.read()
    customer = json.loads(customers)[1]

with open("my_business.json") as file:
    business_info = file.read()
    my_business = json.loads(business_info)

def sort_by_invoice_number(item):
    return item["invoice_number"]

def get_next_invoice_number():
    with open("invoices.json") as file:
        invoice_info = file.read()
        past_invoices = json.loads(invoice_info)

    # sort based on invoice numbers so I can get the most recent
    past_invoices = sorted(past_invoices, key=sort_by_invoice_number)

    # invoice number looks like 2023-0001, so split it by the - and get the part after the -
    last_invoice_number = int(past_invoices[-1]["invoice_number"].split("-")[1])

    # add one to the invoice number
    current_invoice_number = last_invoice_number + 1
    current_year = date.today().year

    # add the current year and the new invoice number together
    current_invoice_number = f'{current_year}-{current_invoice_number:04}'

    return current_invoice_number


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

        return f'{hours:01}:{minutes:02}:{seconds:02}'
    
    def set_prices_from_durations(self, items):
        for item in items:
            time = item["duration"].split(":")
            # nvm seconds DO matter for this

            seconds = int(time[2])
            seconds = seconds / self.SIXTY
            minutes = int(time[1])
            minutes = minutes + seconds
            # this rounding here is important
            minutes = round(Decimal(minutes / self.SIXTY), 4)
            hours = int(time[0])
            final_hours = hours + minutes

            price = final_hours * item["rate"]

            # then round it to two
            price = round(Decimal(price), 2)

            # then format with two 0's and save it
            item["price"] = f'{price:.2f}'
    
    def set_all_rates(self, items):
        for item in items:
            #TODO: check tag for each to check for different rate for one task, otherwise, just assign based on the rate from the project

            item["rate"] = customer["default_rate"]

    def get_total_balance(self, items):
        balance = 0
        for item in items:
            balance = balance + Decimal(item["price"])
        
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

    today = date.today()
    due_date = today + relativedelta(months=+1)

    html_out = template.render(customer=customer, invoice_number=get_next_invoice_number(), date=today, due_date=due_date,
        my_business=my_business, items=items, balance=balance
    )

    HTML(string=html_out).write_pdf("invoice.pdf", stylesheets=["invoice.css"])

def find_duplicates_with_same_description_edit(results, item, index):
    for search_index in range(index + 1, len(results)):
        if (item["deleted"] == False):
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

# temp create new list with certain project
results = list(filter(lambda a: a["project"] == customer["aliases"][0], results))

# have these work for each company, right now it's just the full list
duration.set_all_rates(results)

for x, item in enumerate(results):
    if (item["deleted"] == False):
        find_duplicates_with_same_description_edit(results, item, x)

# need this after the duplicates are merged together
duration.set_prices_from_durations(results)

print(f'length before: {len(results)}')

# create a new list without all the items that were deleted bc they were duplicates
finished_list = list(filter(lambda a: a["deleted"] != True, results))

balance = duration.get_total_balance(finished_list)

print(f'length after: {len(finished_list)}')

# make a demo pdf only using the data from a certain project/customer
make_pdf(finished_list, balance )
