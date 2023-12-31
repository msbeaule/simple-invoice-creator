import csv, math, argparse
import decimal
from decimal import Decimal

# setting up rounding for decimals
ctx = decimal.getcontext()
ctx.rounding = decimal.ROUND_HALF_UP

parser = argparse.ArgumentParser(
                    prog='SimpleInvoiceCreator',
                    description='Takes a .csv file converts hours (1.5) to duration (01:30:00)',
                    epilog='Look at README for help with .csv file layout and more')

parser.add_argument('-i', '--input', required=True, help="Input a .csv file to add a column for Duration")

args = parser.parse_args()



def get_values_from_csv():
    with open(args.input, "r") as csvinput:
        with open("OUTPUT-hours-to-duration.csv", "w") as csvoutput:
            writer = csv.writer(csvoutput, lineterminator='\n')

            for row in csv.reader(csvinput):
                hour_field  = row[3]
                

                if row[0] == "Project":
                    # the first row in the csv, add the heading here
                    writer.writerow(row + ["Duration"])
                else:
                    try:
                        hour_field = Decimal(hour_field)
                        duration = get_duration_from_hour(hour_field)
                    except decimal.InvalidOperation:
                        duration = ""
                    #print(hour_field, "\t", duration)

                    writer.writerow(row + [duration])


def get_duration_from_hour(hour_field):
    hours = 0
    minutes = 0
    duration = ""
    
    hour_field = Decimal(hour_field)
    # splits the number from the decimal point, so it gets the hours (whole number) and the minutes (the decimal)
    minutes, hours = math.modf(hour_field)

    # convert float into whole number of minutes
    minutes = int(minutes * 60)
    # format the minutes to two
    minutes = f'{minutes:02d}'
    # put hours and minutes together in the duration format
    duration = str(int(hours)) + ":" + minutes + ":" + "00"
    
    return duration

get_values_from_csv()
