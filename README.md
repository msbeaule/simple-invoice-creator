## Simple python invoice creator

Give it a .csv from Toggl and it will make an invoice. You need to create a few json files though.

## Installation

Follow the weasyprint instructions (need to install the prereq first then weasyprint): https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation

Then install the requirements file:

```
pip install -r requirements.txt
```

## Run the invoice creator

```
python main.py -i <csv file> -c <customer position in customers.json list> [-n <manual invoice number>] [--test]
```

Examples:

```
python main.py --help
```

```
python main.py -i input.csv -c 2 -n 2023-0001
```

```
python main.py -i input.csv -c 0 --test
```

```
python main.py -i input.csv -c 0
```

### Converting hours into duration

Use `python hours_to_duration.py -i <csv file>` and it will convert hours (if it's in the 4th column) into duration for each row. Outputs to a new file `OUTPUT-<file name>.csv`. Then you can use `main.py` on the new file.

## Notes

The .csv needs to be saved in not utf8, otherwise this program doesn't work.

## .json files

You will need to make the following .json files:

- customers.json
- my_business.json
- invoices.json

TODO: add what's in each file

## .csv file format

The .csv files this program can use must contain one of these three heading configurations.

### Heading one (export from paid Toggl account)

- There is no specific order
- The headings listed are required
- `Price` is an optional heading
- There can be additional headings but the program will ignore them

```
Project, Duration, Task, Description
sample project, 0:50:00, a task, a description
```

### Heading two (export from free Toggl account)

- There is no specific order
- The headings listed are required
- The `Description` field can be used for both task and description in the invoice by using a `:`
- `Price` is an optional heading
- There can be additional headings but the program will ignore them

```
Project, Duration, Description
sample project, 1:05:00, task: description
```

### Heading three (custom)

- `Hours` must be in the 3rd spot, the rest can be in any order
- The headings listed are required
- The `Description` field can be used for both task and description in the invoice by using a `:`
- `Price` is an optional heading
- There can be additional headings but the program will ignore them

```
Project, Description, Hours
sample project, task: description, 1.5
```
