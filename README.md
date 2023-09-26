## Simple python invoice creator

Give it a .csv from Toggl and it will make an invoice. You need to create a few json files though. TODO: add the files and examples of what goes into them

## Installation

Follow the weasyprint instructions (need to install the prereq first then weasyprint): https://doc.courtbouillon.org/weasyprint/stable/first_steps.html#installation

Then install the requirements file.

## Converting hours into duration

Use `python hours_to_duration.py -i <FILE>` and it will convert hours (if it's in the 4th column) into duration for each row. Outputs to a new file `OUTPUT.csv`. Then you can use `main.py` on the new file. 

## Notes

The .csv needs to be saved in not utf8, otherwise this program doesn't work.
