#!/usr/bin/env python
#-*- coding: utf-8 -*-
__author__ = 'heway'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

import time
from datetime import datetime, timedelta
from operator import itemgetter

def format_date(old_format, new_format, date):
    return time.strftime(new_format, time.strptime(date, old_format))

def date_delta(format, date, base_date):
    return (datetime.strptime(date, format) - datetime.strptime(base_date, format)).days

def main():
    #file_name = raw_input('Input the file name to be sorted: ')
    file_name = 't_alibaba_data.csv'
    file_name = 'in/' + file_name

    #read record to list
    records = list()
    with open(file_name) as in_file:
        for line in in_file:
            items = line.split(',')
            if len(items) != 4:
                print line
                continue
            #date = format_date('%m月%d日', '%m%d', items[3].strip())
            date = date_delta('%m月%d日', items[3].strip(), '4月15日')
            if items[2].strip() == '1':
                items[2] = '5'
            record = (items[0].strip(), items[1].strip(), items[2].strip(), date)
            records.append(record)

    #sort the record by user_id, brand_id, visit_datetime in ascending order
    sorted_records = sorted(records, key=itemgetter(0, 1, 3, 2))

    with open(file_name + '_sorted', 'w') as out_file:
        for record in sorted_records:
            out_file.write(','.join(record[0:3]) + ',' + str(record[3]) + '\n')

if __name__ == '__main__':
    main()
    #print date_delta('%m月%d日', '7月15日', '4月15日')