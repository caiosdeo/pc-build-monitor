#!/usr/bin/env python3

import re
import requests
import gspread
import configparser
from datetime import datetime
from bs4 import BeautifulSoup
from oauth2client.service_account import ServiceAccountCredentials

config = configparser.ConfigParser()
config.read('config.ini')

def next_available_row(worksheet):
    str_list = list(filter(None, worksheet.col_values(1)))
    return len(str_list)+1

print(f"Accessing the build")
url = config['MEUPCNET']['URL']
page = requests.get(url)

soup = BeautifulSoup(page.content, "html.parser")

result = soup.find_all("tbody")[-1]
parts = result.find_all("tr")

pc_parts_dict = {
    'Cooler do processador': 'Cooler',
    'Placa-mãe': 'MoBo',
    'Armazenamento': 'SSD',
    'Fonte': 'Fonte',
    'Memória': 'RAM',
    'Processador': 'CPU',
    'Placa de vídeo': 'GPU',
    'Gabinete': 'Gabinete'
}

# Retrieving date
today = datetime.now()
log_date = today.strftime("%d/%m %H:%M")

print(f"Connecting to the spreadsheet")
# use creds to create a client to interact with the Google Drive API
scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/drive.file']
creds = ServiceAccountCredentials.from_json_keyfile_name('client_secret.json', scope)
client = gspread.authorize(creds)

# Opening the spreadsheets
spreadsheet = client.open(config['SPREADSHEET']['NAME'])

# Main sheet
build_sheet = spreadsheet.sheet1

# Auxiliar to manage spreadsheet
build_index = next_available_row(build_sheet)
parts_index = build_index - 2

print(f"Retrieving data for now: {log_date}")

for part in parts:
    part_info = list(part.descendants)
    if len(part_info) > 8:
        # * Part_info content
        # 0 - \n
        # 1 - <td><b> Part
        # 2 - <b> Part
        # 3 - Part
        # 4 - \n
        # 5 - <td><a> partURL
        # 6 - <a> partURL
        # 7 - Part product
        # 8 - \n
        # 9 - <td> Price
        # 10 - Price
        # 11 - \n
        part_name = part_info[3]
        prices = re.findall(r"[1-9]\d{0,2}(?:\.\d{3})*,\d{2}", part_info[10])
        price = prices[0]
        billet_price = prices[1]
        
        row = [log_date, price, billet_price]
        part_sheet = spreadsheet.worksheet(pc_parts_dict[part_name]) # Sheet specific by part
        part_sheet.insert_row(row, parts_index, value_input_option='USER_ENTERED')


print("Adding the prices")

row = [log_date, 
        f"=SOMA(CPU!B{parts_index};Cooler!B{parts_index};GPU!B{parts_index};MoBo!B{parts_index};RAM!B{parts_index};SSD!B{parts_index};Gabinete!B{parts_index};Fonte!B{parts_index})", 
        f"=SOMA(CPU!C{parts_index};Cooler!C{parts_index};GPU!C{parts_index};MoBo!C{parts_index};RAM!C{parts_index};SSD!C{parts_index};Gabinete!C{parts_index};Fonte!C{parts_index})"]

build_sheet.insert_row(row, build_index, value_input_option='USER_ENTERED')

print("Complete! Check the spreadsheet!")
