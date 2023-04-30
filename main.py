from datetime import date
import json

from weasyprint import HTML, CSS
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('.'))
template = env.get_template("invoice.html")

with open("customers.json") as customer_file:
    customers = customer_file.read()
customer = json.loads(customers)[0]

# print(customer)

html_out = template.render(customer=customer, invoiceNumber="2023-0001", date="today")

HTML(string=html_out).write_pdf("invoice.pdf", stylesheets=["invoice.css"])
