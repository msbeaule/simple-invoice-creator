from datetime import date
from dateutil.relativedelta import relativedelta

import json, csv, math, argparse
import decimal
from decimal import Decimal

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

from filters import j2_round_float_to_two

# when task is empty
DEFAULT_TASK_NAME = "Misc."

# setting up rounding for decimals
ctx = decimal.getcontext()
ctx.rounding = decimal.ROUND_HALF_UP

parser = argparse.ArgumentParser(
                    prog='SimpleInvoiceCreator',
                    description='Takes a .csv file and creates a PDF invoice with it',
                    epilog='Look at README for help with .csv file layout and more')

parser.add_argument('-i', '--input', required=True, help="Input a .csv file with data to make the invoice from")

TEST_INVOICE_FILE_NAME = "test_invoice.pdf"

parser.add_argument('-t', '--test', nargs="?", const=True, default=False, help=f'Creates an invoice with data but the file name is {TEST_INVOICE_FILE_NAME}')

parser.add_argument('-n', '--number', help=f'Manualy input an invoice number')

parser.add_argument('-c', '--customer', type=int, required=True, help=f'Enter the customer index from the customers.json file')


args = parser.parse_args()

class InvoiceHelper:
    SIXTY = 60

    def __init__(self) -> None:
        pass

    def get_customer(self):
        with open("customers.json") as file:
            customers = file.read()
            customer = json.loads(customers)[args.customer]
        return customer
    
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
    
    def set_all_rates(self, items, customer):
        for item in items:
            #TODO: check tag for each to check for different rate for one task, otherwise, just assign based on the rate from the project

            item["rate"] = customer["default_rate"]

    def get_total_balance(self, items):
        balance = 0
        for item in items:
            balance = balance + Decimal(item["price"])
        
        subtotal = balance

        # TODO: get actual paid to date
        paid_to_date = Decimal(0)

        balance = subtotal - paid_to_date

        # keeps the decimal places in check
        balance = round(balance, 2)

        paid_to_date_str = f'{paid_to_date:.2f}'

        return balance, subtotal, paid_to_date_str

    def _get_time_and_remaining(self, duration):
        to_add = 0
        
        if duration > self.SIXTY:
            to_add = math.floor(duration / self.SIXTY)
            duration = duration % self.SIXTY
        return duration, to_add

    def get_my_business(self):
        with open("my_business.json") as file:
            business_info = file.read()
            my_business = json.loads(business_info)
        return my_business

    def sort_by_invoice_number(self, item):
        return item["invoice_number"]

    def get_next_invoice_number(self):
        with open("invoices.json") as file:
            invoice_info = file.read()
            past_invoices = json.loads(invoice_info)

        # sort based on invoice numbers so I can get the most recent
        past_invoices = sorted(past_invoices, key=self.sort_by_invoice_number)

        # invoice number looks like 2023-0001, so split it by the - and get the part after the -
        last_invoice_number = int(past_invoices[-1]["invoice_number"].split("-")[1])

        # add one to the invoice number
        current_invoice_number = last_invoice_number + 1
        current_year = date.today().year

        # add the current year and the new invoice number together
        current_invoice_number = f'{current_year}-{current_invoice_number:04}'

        return current_invoice_number
    
    def find_duplicates_with_same_description_edit(self, results, item, index):
        for search_index in range(index + 1, len(results)):
            if (item["deleted"] == False):
                if self.does_task_match(item, results[search_index]) and \
                    item["description"] == results[search_index]["description"]:
                    # print("HIT")
                    # print(results[search_index]["description"])
                    results[search_index]["deleted"] = True
                    new_duration = self.add_two_together(item["duration"], results[search_index]["duration"])
                    item["duration"] = new_duration
    
    def does_task_match(self, item, result):
        task = item["task"]
        result_task = result["task"]
        
        return task == result_task
    
    def get_task_and_description(self, value: str):
        split_string = value.split(":", 1)
        # print(value)
        # print(len(split_string))
        if len(split_string) == 1:
            task = DEFAULT_TASK_NAME
            description = split_string[0]
        else:
            task = split_string[0]
            description = split_string[1]
        
        return [task, description]

    
    def get_total_hours(self, items):
        hours = 0
        minutes = 0
        seconds = 0

        for item in items:
            time = item["duration"].split(":")

            seconds += int(time[2])

            minutes += int(time[1])

            hours += int(time[0])

        minutes_to_add = 0
        hours_to_add = 0

        seconds, minutes_to_add = self._get_time_and_remaining(seconds)

        minutes += minutes_to_add
        minutes, hours_to_add = self._get_time_and_remaining(minutes)

        hours += hours_to_add

        return f'{hours:01} hours, {minutes:02} minutes, {seconds:02} seconds'
    
    def get_values_from_csv(self):
        try:
            with open(args.input, "r") as f:
                results = [
                    {
                        "project": row["Project"],
                        "task": row["Task"],
                        "description": row["Description"],
                        "duration": row["Duration"],
                        # "tags": row["Tags"],
                        "deleted": False,
                        
                    }
                    for row in csv.DictReader(f)
                ]
        except KeyError:
            with open(args.input, "r") as f:
                results = [
                    {
                        "project": row["Project"],
                        "task": self.get_task_and_description(row["Description"])[0],
                        "description": self.get_task_and_description(row["Description"])[1],
                        "duration": row["Duration"],
                        # "tags": row["Tags"],
                        "deleted": False,
                        
                    }
                    for row in csv.DictReader(f)
                ]

            # print(json.dumps(results))
        return results


def make_pdf():
    helper = InvoiceHelper()
    customer = helper.get_customer()
    if args.number:
        invoice_number = args.number
    else:
        invoice_number = helper.get_next_invoice_number()
    my_business = helper.get_my_business()

    if args.test:
        PDF_NAME = TEST_INVOICE_FILE_NAME
    else:
        PDF_NAME = f'invoice_{invoice_number}.pdf'

    today = date.today()
    due_date = today + relativedelta(months=+1)

    results = helper.get_values_from_csv()

    # temp create new list with certain project
    results = list(filter(lambda a: a["project"] == customer["aliases"][0], results))

    # have these work for each company, right now it's just the full list
    helper.set_all_rates(results, customer)

    for x, item in enumerate(results):
        if (item["deleted"] == False):
            helper.find_duplicates_with_same_description_edit(results, item, x)

    # need this after the duplicates are merged together
    helper.set_prices_from_durations(results)

    # print(f'length before: {len(results)}')

    # create a new list without all the items that were deleted bc they were duplicates
    finished_list = list(filter(lambda a: a["deleted"] != True, results))

    balance, subtotal, paid_to_date = helper.get_total_balance(finished_list)

    # print(f'length after: {len(finished_list)}')

    env = Environment(loader=FileSystemLoader('.'))
    # adding custom filter
    env.filters["round_float"] = j2_round_float_to_two
    template = env.get_template("invoice.html")
    

    html_out = template.render(customer=customer, invoice_number=invoice_number, date=today, due_date=due_date,
        my_business=my_business, items=finished_list, balance=balance, subtotal=subtotal, paid_to_date=paid_to_date
    )

    HTML(string=html_out).write_pdf(PDF_NAME, stylesheets=["invoice.css"])

    print(f'invoice created: "{PDF_NAME}"')

    print(f'Total billable hours in this invoice: {helper.get_total_hours(finished_list)}')


# make a demo pdf only using the data from a certain project/customer
make_pdf()
