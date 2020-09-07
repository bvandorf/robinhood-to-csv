from __future__ import print_function
from Robinhood import Robinhood
from login_data import collect_login_data
from profit_extractor import profit_extractor
import getpass
import collections
import argparse
import ast
from dotenv import load_dotenv, find_dotenv
import os

logged_in = False

parser = argparse.ArgumentParser(
    description='Export Robinhood trades to a CSV file')
parser.add_argument(
    '--debug', action='store_true', help='store raw JSON output to debug.json')
parser.add_argument(
    '--username', default='', help='your Robinhood username')
parser.add_argument(
    '--password', default='', help='your Robinhood password')
parser.add_argument(
    '--mfa_code', help='your Robinhood mfa_code')
parser.add_argument(
    '--device_token', help='your device token')
parser.add_argument(
    '--fetch_rows', type=int, help='how many rows to fetch')
parser.add_argument(
    '--save_file', default='', help='file name to save as')
parser.add_argument(
    '--default_name', action='store_true', help='save the file with the defult name')
parser.add_argument(
    '--pending', action='store_true', help='include pending transactions')
parser.add_argument(
    '--profit', action='store_true', help='calculate profit for each sale')
args = parser.parse_args()
username = args.username
password = args.password
mfa_code = args.mfa_code
device_token = args.device_token

load_dotenv(find_dotenv())

robinhood = Robinhood()

# login to Robinhood
logged_in = collect_login_data(robinhood_obj=robinhood, username=username, password=password, device_token=device_token, mfa_code=mfa_code)

print("Pulling trades. Please wait...")

fields = collections.defaultdict(dict)
trade_count = 0
queued_count = 0

# fetch order history and related metadata from the Robinhood API
#orders = robinhood.get_endpoint('orders')
events = robinhood.get_endpoint('optionsEvents');
# load a debug file
# raw_json = open('debug.txt','rU').read()
# orders = ast.literal_eval(raw_json)

# store debug
if args.debug:
    # save the CSV
    try:
        with open("debug.txt", "w+") as outfile:
            outfile.write(str(events))
            print("Debug infomation written to debug.txt")
    except IOError:
        print('Oops.  Unable to write file to debug.txt')

if args.save_file == '':
    # choose a filename to save to
    if args.fetch_rows != None and int(args.fetch_rows) > 0:
        defaultFilename = "option-events-trades-last" + str(args.fetch_rows) + ".csv"
    else:
        defaultFilename = "option-events-trades.csv"
else:
    defaultFilename = args.save_file




# do/while for pagination
paginated = True
page = 0
row = 0
while paginated:
    for i, order in enumerate(events['results']):
        counter = row + (page * 100)

        if order['state'] == "confirmed":
            trade_count += 1
        
        for key, value in enumerate(order):
            if value == 'equity_components':
                for key1, value1 in enumerate(order[value]):
                    for key2, value2 in enumerate(value1):
                        fields[counter][value2] = value1[value2]
            
            else:
                fields[counter][value] = order[value]
                
            row += 1
    if args.fetch_rows != None and int(args.fetch_rows) > 0 and (row > int(args.fetch_rows)):
        paginated = False
    # paginate
    if events['next'] is not None:
        page = page + 1
        events = robinhood.get_custom_endpoint(str(events['next']))
    else:
        paginated = False

# for i in fields:
#   print fields[i]
#   print "-------"

# check we have trade data to export
if trade_count > 0 or queued_count > 0:
    print("%d queued trade%s and %d executed trade%s found in your account." %
          (queued_count, "s" [queued_count == 1:], trade_count,
           "s" [trade_count == 1:]))
    # print str(queued_count) + " queded trade(s) and " + str(trade_count) + " executed trade(s) found in your account."
else:
    print("No trade history found in your account.")
    quit()

# CSV headers
keys = fields[0].keys()
#keys = sorted(keys)
csv = ','.join(keys) + "\n"

# CSV rows
for row in fields:
    for idx, key in enumerate(keys):
        if (idx > 0):
            csv += ","
        try:
            csv += str(fields[row][key])
        except:
            csv += ""

    csv += "\n"

if (args.default_name):
    filename = defaultFilename
elif args.save_file == '':
    print("Choose a filename or press enter to save to `" + defaultFilename + "`:")
    try:
        input = raw_input
    except NameError:
        pass
    filename = input().strip()
    if filename == '':
        if args.fetch_rows != None and int(args.fetch_rows) > 0:
            filename = "option-events--trades-last" + str(args.fetch_rows) + ".csv"
        else:
            filename = "option-events--trades.csv"
else:
    filename = defaultFilename


# save the CSV
try:
    with open(filename, "w+") as outfile:
        outfile.write(csv)
    print("file saved as " + filename)
except IOError:
    print("Oops. Unable to write file to " + filename + ". Close the file if it is open and try again.")

if args.profit:
    profit_csv = profit_extractor(csv, filename)
