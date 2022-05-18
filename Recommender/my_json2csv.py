import json
import csv
import sys

"""
Json to CSV converter from GeeksForGeeks
Modified to use UTF-8 encoding
"""

if len(sys.argv) != 3:
    print("Usage: python my_json2csv.py <input_file> <output_file>")
    exit()
# print('Argument List:', str(sys.argv))
input_file = str(sys.argv[1])
output_file = str(sys.argv[2])
print(f"input: {input_file}, outputs: {output_file}")

# with open(input_file, encoding='utf8') as json_file:
#     jsondata = json.load(json_file)
jsondata = []
for line in open(input_file, encoding='utf8'):
    json_row = json.loads(line)
    if (input_file == 'yelp_academic_dataset_review.json'):
        # print(f"DEBUG: type of json_row: {type(json_row)}")
        json_row.pop('review_id', None)
        json_row.pop('useful', None)
        json_row.pop('funny', None)
        json_row.pop('cool', None)
        json_row.pop('text', None)
        json_row.pop('date', None)
    jsondata.append(json_row)

data_file = open(output_file, 'w', encoding='utf-8', newline='')
csv_writer = csv.writer(data_file)

count = 0
for data in jsondata:
    if count == 0:
        header = data.keys()
        csv_writer.writerow(header)
        count += 1
    csv_writer.writerow(data.values())

data_file.close()