#!/usr/bin/env python
#-*- coding: utf-8 -*-

__author__ = 'heway'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')
import numpy
from operator import itemgetter


def time_weighted(t, t0, period):
    if t >= t0:
        print 'time weighted error: ', t, t0
    ret = numpy.exp(-(t0 - t) / period)
    return ret


init_purchase_count = 0
clk_period = 5
cart_period = 30
purchase_feedback = 3

def extract(filename, last_day=91):
    """
    extract train and test from data

    :param last_day: the split data of train set and test set
    :param filename: the data filename
    """
    #{user_id: brand_id: (act, date), user_id: brand_id: (act, date), ...}
    #summarize purchase about user and brand before last_day
    all_data = dict()
    user_purchase_count = dict()
    brand_purchase_count = dict()
    user_brand_purchase_count = dict()
    user_unique_brand = dict()
    brand_unique_user = dict()

    all_user_unique_brand = dict()
    with open('in/' + filename) as sorted_file:
        for line in sorted_file:
            items = line.strip().split(",")
            if len(items) != 4:
                print line
                continue

            user_id = items[0]
            brand_id = items[1]
            act = items[2]
            date = int(items[3])

            all_data.setdefault(user_id, dict())
            all_data[user_id].setdefault(brand_id, list())
            all_data[user_id][brand_id].append((act, date))

            if act == '5':
                all_user_unique_brand.setdefault(user_id, set())
                all_user_unique_brand[user_id].add(brand_id)

                if date <= last_day:
                    user_purchase_count.setdefault(user_id, 0)
                    user_purchase_count[user_id] += 1

                    brand_purchase_count.setdefault(brand_id, 0)
                    brand_purchase_count[brand_id] += 1

                    user_unique_brand.setdefault(user_id, set())
                    user_unique_brand[user_id].add(brand_id)

                    brand_unique_user.setdefault(brand_id, set())
                    brand_unique_user[brand_id].add(user_id)

                    user_brand_purchase_count.setdefault(user_id + '^' + brand_id, 0)
                    user_brand_purchase_count[user_id + '^' + brand_id] += 1

    #make sure that acts of (user, brand) are ordered by date, act
    for user_id in all_data.keys():
        for brand_id, act_list in all_data[user_id].items():
            all_data[user_id][brand_id] = sorted(act_list, key=itemgetter(1, 0))

    #Summarize user's avg clk and std before purchase{user_id: (mean, std), ...}
    #Only the first purchase is taken into consideration
    user_avg_before_purchase = dict()
    brand_clk_count_before_purchase = dict()
    for user_id in all_data.keys():
        clk_counts = list()
        for brand_id in all_data[user_id].keys():
            for i in range(0, len(all_data[user_id][brand_id])):
                if all_data[user_id][brand_id][i][0] == '5':
                    purchase_day = all_data[user_id][brand_id][i][1]

                    count = 0
                    for j in range(0, i):
                        #only act before the purchase day should be included
                        if all_data[user_id][brand_id][j][1] == purchase_day:
                            break

                        if all_data[user_id][brand_id][j][0] == '0':
                            count += time_weighted(all_data[user_id][brand_id][j][1], purchase_day, clk_period)

                    if count != 0:
                        clk_counts.append(count)
                    brand_clk_count_before_purchase.setdefault(brand_id, list())
                    brand_clk_count_before_purchase[brand_id].append(count)

                    break
        if len(clk_counts) != 0:
            user_avg_before_purchase[user_id] = (numpy.mean(clk_counts), numpy.std(clk_counts))
        else:
            user_avg_before_purchase[user_id] = (0, 0)

    #Summarize brand's avg clk before purchase
    #Only the first purchase is taken into consideration
    brand_avg_before_purchase = dict()
    for brand_id, clk_counts in brand_clk_count_before_purchase.items():
        if len(clk_counts) != 0:
            brand_avg_before_purchase[brand_id] = (numpy.mean(clk_counts), numpy.std(clk_counts))
        else:
            brand_avg_before_purchase[brand_id] = (0, 0)

    #Get negative and positive cases
    positive_cases = open('in/positive_' + filename, 'w')
    negative_cases = open('in/negative_' + filename, 'w')
    positive_array = list()
    negative_array = list()
    test_positive_array = list()
    test_negative_array = list()

    for user_id in all_data.keys():
        if user_id in user_purchase_count:
            u_purchase_count = user_purchase_count[user_id]
        else:
            u_purchase_count = 0
        if user_id in user_unique_brand:
            u_unique_brand_count = len(user_unique_brand[user_id])
        else:
            u_unique_brand_count = 0

        for brand_id in all_data[user_id].keys():
            #ignore brands that have never been purchased
            if brand_id not in brand_purchase_count:
                continue

            pre_purchase_day = -1
            pre_purchase_count = init_purchase_count
            clk_before_purchase = 0
            cart_before_purchase = 0
            fav_before_purchase = 0

            #True means the user used to buy the brand
            if user_id in all_user_unique_brand and brand_id in all_user_unique_brand[user_id]:
                for cur_index in range(0, len(all_data[user_id][brand_id])):
                    if all_data[user_id][brand_id][cur_index][0] == '5':
                        cur_purchase_day = all_data[user_id][brand_id][cur_index][1]
                        cur_pre_purchase_day = -purchase_feedback
                        #When current purchase day is beyond last day, we actually do not know the exact purchase day
                        if cur_purchase_day > last_day:
                            cur_purchase_day = last_day + 1
                        if cur_purchase_day == pre_purchase_day:
                            #print 'More than one purchase occurs one day'
                            pre_purchase_count += 1
                            continue

                        for before_index in range(0, cur_index):
                            #ignore acts that happen in the current and pre purchase day and after the last day
                            if all_data[user_id][brand_id][before_index][1] == cur_purchase_day or \
                                            all_data[user_id][brand_id][before_index][1] > last_day:
                                break
                            if all_data[user_id][brand_id][before_index][1] < cur_pre_purchase_day + purchase_feedback:
                                continue

                            #being added to favourite should be long_terms effect
                            if all_data[user_id][brand_id][before_index][0] == '3':
                                fav_before_purchase += 1
                            elif all_data[user_id][brand_id][before_index][0] == '0':
                                clk_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                                     cur_purchase_day, clk_period)
                            elif all_data[user_id][brand_id][before_index][0] == '2':
                                cart_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                                     cur_purchase_day, cart_period)
                            elif all_data[user_id][brand_id][before_index][0] == '5':
                                cur_pre_purchase_day = all_data[user_id][brand_id][before_index][1]
                            else:
                                pass

                        #ignore no act before purchase
                        if clk_before_purchase == 0 and cart_before_purchase == 0 \
                                and pre_purchase_count <= init_purchase_count:
                            pre_purchase_day = cur_purchase_day
                            pre_purchase_count += 1
                            clk_before_purchase = 0
                            cart_before_purchase = 0
                            fav_before_purchase = 0
                            continue

                        if (user_id + '^' + brand_id) in user_brand_purchase_count:
                            u_b_count = user_brand_purchase_count[user_id + '^' + brand_id]
                        else:
                            u_b_count = 0
                        if cur_purchase_day <= last_day:
                            positive_cases.write(str(pre_purchase_count) + '\t' + str(clk_before_purchase) + '\t'
                                                 + str(cart_before_purchase) + '\t' + str(fav_before_purchase) + '\t'
                                                 + str(
                                clk_before_purchase - user_avg_before_purchase[user_id][0]) + '\t'
                                                 + str(user_avg_before_purchase[user_id][1]) + '\t'
                                                 + str(
                                clk_before_purchase - brand_avg_before_purchase[brand_id][0]) + '\t'
                                                 + str(brand_avg_before_purchase[brand_id][1]) + '\t'
                                                 + str(u_purchase_count) + '\t'
                                                 + str(brand_purchase_count[brand_id]) + '\t'
                                                 + str(u_unique_brand_count) + '\t'
                                                 + str(len(brand_unique_user[brand_id])) + '\t'
                                                 + str(u_b_count) + '\t'
                                                 + '1' + '\n'
                            )
                            positive_array.append(
                                (pre_purchase_count, clk_before_purchase, cart_before_purchase, fav_before_purchase,
                                 clk_before_purchase - user_avg_before_purchase[user_id][0],
                                 user_avg_before_purchase[user_id][1],
                                 clk_before_purchase - brand_avg_before_purchase[brand_id][0],
                                 brand_avg_before_purchase[brand_id][1],
                                 u_purchase_count, brand_purchase_count[brand_id],
                                 u_unique_brand_count, len(brand_unique_user[brand_id]),
                                 u_b_count
                                )
                            )
                        else:
                            test_positive_array.append(
                                (pre_purchase_count, clk_before_purchase, cart_before_purchase, fav_before_purchase,
                                 clk_before_purchase - user_avg_before_purchase[user_id][0],
                                 user_avg_before_purchase[user_id][1],
                                 clk_before_purchase - brand_avg_before_purchase[brand_id][0],
                                 brand_avg_before_purchase[brand_id][1],
                                 u_purchase_count, brand_purchase_count[brand_id],
                                 u_unique_brand_count, len(brand_unique_user[brand_id]),
                                 u_b_count
                                )
                            )
                            break

                        pre_purchase_day = cur_purchase_day
                        pre_purchase_count += 1
                        clk_before_purchase = 0
                        cart_before_purchase = 0
                        fav_before_purchase = 0

            else:
                cur_purchase_day = all_data[user_id][brand_id][-1][1] + 1
                #only those who has no act in recent month are treated as negative case
                #For others, we predict whether purchase will happen after last day, so we assume the purchase day as
                #(last_day + 1)
                test_cur_purchase_day = last_day + 1
                test_clk_before_purchase = 0

                for before_index in range(0, len(all_data[user_id][brand_id]) - 1):
                    if all_data[user_id][brand_id][before_index][1] > last_day:
                        break

                    #being added to favourite should be long_terms effect
                    if all_data[user_id][brand_id][before_index][0] == '3':
                        fav_before_purchase += 1
                    elif all_data[user_id][brand_id][before_index][0] == '0':
                        clk_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                             cur_purchase_day, clk_period)
                        test_clk_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                                  test_cur_purchase_day, clk_period)
                    elif all_data[user_id][brand_id][before_index][0] == '2':
                        cart_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                             cur_purchase_day, cart_period)
                    else:
                        pass

                #no click or add to cart before purchase
                if clk_before_purchase == 0 and cart_before_purchase == 0:
                    continue

                #only those who has no act in recent month
                if all_data[user_id][brand_id][-1][1] <= last_day - 30:
                    negative_cases.write(str(pre_purchase_count) + '\t' + str(clk_before_purchase) + '\t'
                                         + str(cart_before_purchase) + '\t' + str(fav_before_purchase) + '\t'
                                         + str(0) + '\t'
                                         + str(0) + '\t'
                                         + str(0) + '\t'
                                         + str(0) + '\t'
                                         + str(u_purchase_count) + '\t'
                                         + str(brand_purchase_count[brand_id]) + '\t'
                                         + str(u_unique_brand_count) + '\t'
                                         + str(len(brand_unique_user[brand_id])) + '\t'
                                         + str(0) + '\t'
                                         + '0' + '\n'
                    )
                    negative_array.append(
                        (pre_purchase_count, clk_before_purchase, cart_before_purchase, fav_before_purchase,
                         0,
                         0,
                         0,
                         0,
                         u_purchase_count, brand_purchase_count[brand_id],
                         u_unique_brand_count, len(brand_unique_user[brand_id]),
                         0
                        )
                    )

                #all of them are treated as negative
                test_negative_array.append(
                    (pre_purchase_count, test_clk_before_purchase, cart_before_purchase, fav_before_purchase,
                     0,
                     0,
                     0,
                     0,
                     u_purchase_count, brand_purchase_count[brand_id],
                     u_unique_brand_count, len(brand_unique_user[brand_id]),
                     0
                    )
                )

    with open('in/test_positive_array', 'w') as test_file:
        for test_positive in test_positive_array:
            for item in test_positive:
                test_file.write(str(item) + '\t')
            test_file.write('\n')

    positive_array = numpy.asarray(positive_array, dtype=numpy.float32)
    negative_array = numpy.asarray(negative_array, dtype=numpy.float32)
    test_positive_array = numpy.asarray(test_positive_array, dtype=numpy.float32)
    test_negative_array = numpy.asarray(test_negative_array, dtype=numpy.float32)
    return positive_array, negative_array, test_positive_array, test_negative_array


def get_X(filename, last_day=122):
    #{user_id: brand_id: (act, date), user_id: brand_id: (act, date), ...}
    #summarize purchase about user and brand before last_day
    all_data = dict()
    user_purchase_count = dict()
    brand_purchase_count = dict()
    user_brand_purchase_count = dict()
    user_unique_brand = dict()
    brand_unique_user = dict()

    all_user_unique_brand = dict()
    with open('in/' + filename) as sorted_file:
        for line in sorted_file:
            items = line.strip().split(",")
            if len(items) != 4:
                print line
                continue

            user_id = items[0]
            brand_id = items[1]
            act = items[2]
            date = int(items[3])

            all_data.setdefault(user_id, dict())
            all_data[user_id].setdefault(brand_id, list())
            all_data[user_id][brand_id].append((act, date))

            if act == '5':
                all_user_unique_brand.setdefault(user_id, set())
                all_user_unique_brand[user_id].add(brand_id)

                if date <= last_day:
                    user_purchase_count.setdefault(user_id, 0)
                    user_purchase_count[user_id] += 1

                    brand_purchase_count.setdefault(brand_id, 0)
                    brand_purchase_count[brand_id] += 1

                    user_unique_brand.setdefault(user_id, set())
                    user_unique_brand[user_id].add(brand_id)

                    brand_unique_user.setdefault(brand_id, set())
                    brand_unique_user[brand_id].add(user_id)

                    user_brand_purchase_count.setdefault(user_id + '^' + brand_id, 0)
                    user_brand_purchase_count[user_id + '^' + brand_id] += 1

    #make sure that acts of (user, brand) are ordered by date, act
    for user_id in all_data.keys():
        for brand_id, act_list in all_data[user_id].items():
            all_data[user_id][brand_id] = sorted(act_list, key=itemgetter(1, 0))

    #Summarize user's avg clk and std before purchase{user_id: (mean, std), ...}
    #Only the first purchase is taken into consideration
    user_avg_before_purchase = dict()
    brand_clk_count_before_purchase = dict()
    for user_id in all_data.keys():
        clk_counts = list()
        for brand_id in all_data[user_id].keys():
            for i in range(0, len(all_data[user_id][brand_id])):
                if all_data[user_id][brand_id][i][0] == '5':
                    purchase_day = all_data[user_id][brand_id][i][1]

                    count = 0
                    for j in range(0, i):
                        if all_data[user_id][brand_id][j][0] == '0' and all_data[user_id][brand_id][j][
                            1] != purchase_day:
                            count += time_weighted(all_data[user_id][brand_id][j][1], purchase_day, clk_period)

                    if count != 0:
                        clk_counts.append(count)
                    brand_clk_count_before_purchase.setdefault(brand_id, list())
                    brand_clk_count_before_purchase[brand_id].append(count)

                    break
        if len(clk_counts) != 0:
            user_avg_before_purchase[user_id] = (numpy.mean(clk_counts), numpy.std(clk_counts))
        else:
            user_avg_before_purchase[user_id] = (0, 0)

    #Summarize brand's avg clk before purchase
    #Only the first purchase is taken into consideration
    brand_avg_before_purchase = dict()
    for brand_id, clk_counts in brand_clk_count_before_purchase.items():
        if len(clk_counts) != 0:
            brand_avg_before_purchase[brand_id] = (numpy.mean(clk_counts), numpy.std(clk_counts))
        else:
            brand_avg_before_purchase[brand_id] = (0, 0)

    #Get negative and positive cases
    X_list = list()
    user_brand = list()
    cur_purchase_day = last_day + 1

    for user_id in all_data.keys():
        if user_id in user_purchase_count:
            u_purchase_count = user_purchase_count[user_id]
        else:
            u_purchase_count = 0
        if user_id in user_unique_brand:
            u_unique_brand_count = len(user_unique_brand[user_id])
        else:
            u_unique_brand_count = 0

        for brand_id in all_data[user_id].keys():
            #ignore brands that have never been purchased
            if brand_id not in brand_purchase_count:
                continue

            pre_purchase_day = -purchase_feedback
            pre_purchase_count = init_purchase_count

            clk_before_purchase = 0
            cart_before_purchase = 0
            fav_before_purchase = 0

            #the user has ever purchased the brand
            if user_id in all_user_unique_brand and brand_id in all_user_unique_brand[user_id]:
                for before_index in range(0, len(all_data[user_id][brand_id])):
                    if all_data[user_id][brand_id][before_index][1] > last_day:
                        #print 'get_X > last_ady'
                        break
                    if all_data[user_id][brand_id][before_index][1] < pre_purchase_day + purchase_feedback:
                        continue

                    #being added to favourite should be long_terms effect
                    if all_data[user_id][brand_id][before_index][0] == '5':
                        pre_purchase_count += 1
                        pre_purchase_day = all_data[user_id][brand_id][before_index][1]
                    elif all_data[user_id][brand_id][before_index][0] == '3':
                        fav_before_purchase += 1
                    elif all_data[user_id][brand_id][before_index][0] == '0':
                        clk_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                             cur_purchase_day, clk_period)
                    elif all_data[user_id][brand_id][before_index][0] == '2':
                        cart_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                             cur_purchase_day, cart_period)
                    else:
                        pass

                if (user_id + '^' + brand_id) in user_brand_purchase_count:
                    u_b_count = user_brand_purchase_count[user_id + '^' + brand_id]
                else:
                    u_b_count = 0

                X_list.append(
                    (pre_purchase_count, clk_before_purchase, cart_before_purchase, fav_before_purchase,
                     clk_before_purchase - user_avg_before_purchase[user_id][0],
                     user_avg_before_purchase[user_id][1],
                     clk_before_purchase - brand_avg_before_purchase[brand_id][0],
                     brand_avg_before_purchase[brand_id][1],
                     u_purchase_count, brand_purchase_count[brand_id],
                     u_unique_brand_count, len(brand_unique_user[brand_id]),
                     u_b_count
                    )
                )
                user_brand.append((user_id, brand_id))
            #the user has never purchased the brand
            else:
                for before_index in range(0, len(all_data[user_id][brand_id])):
                    if all_data[user_id][brand_id][before_index][1] > last_day:
                        #print 'get_X > last_ady'
                        break

                    #being added to favourite should be long_terms effect
                    if all_data[user_id][brand_id][before_index][0] == '3':
                        fav_before_purchase += 1
                    elif all_data[user_id][brand_id][before_index][0] == '0':
                        clk_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                             cur_purchase_day, clk_period)
                    elif all_data[user_id][brand_id][before_index][0] == '2':
                        cart_before_purchase += time_weighted(all_data[user_id][brand_id][before_index][1],
                                                             cur_purchase_day, cart_period)
                    else:
                        pass

                #if user has no act in recent month and never add the brand to cart
                #if all_data[user_id][brand_id][-1][1] < last_day - 30 and cart_before_purchase == 0:
                #    continue

                if (user_id + '^' + brand_id) in user_brand_purchase_count:
                    u_b_count = user_brand_purchase_count[user_id + '^' + brand_id]
                else:
                    u_b_count = 0
                #only those who has no act in recent month
                X_list.append(
                    (pre_purchase_count, clk_before_purchase, cart_before_purchase, fav_before_purchase,
                     0,
                     0,
                     0,
                     0,
                     u_purchase_count, brand_purchase_count[brand_id],
                     u_unique_brand_count, len(brand_unique_user[brand_id]),
                     u_b_count
                    )
                )
                user_brand.append((user_id, brand_id))

    return X_list, user_brand


if __name__ == '__main__':
    extract('t_alibaba_data.csv_sorted', 122)