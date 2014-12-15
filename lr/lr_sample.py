#!/usr/bin/env python
#-*- coding: utf-8 -*-
import random

__author__ = 'heway'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from preprocess.extract import extract, get_X
import numpy as np
import pickle

from sklearn.linear_model import LogisticRegression
from sklearn import cross_validation, preprocessing
from operator import itemgetter
from preprocess import count

#get recommend
def get_avg_recommend(models, feature_select_sign, p_threshold, top_threshold, last_day):
    print '-----------------------'
    X_list, user_brand = get_X('t_alibaba_data.csv_sorted', last_day=last_day)
    probs = list()
    for i in range(0, len(X_list)):
        temp_list = list()
        temp_list.append(X_list[i])
        temp_array = np.asarray(temp_list, dtype=np.float32)
        temp_array[:, 1] = temp_array[:, 1] + temp_array[:, 0] * 1
        temp_array = temp_array[:, feature_select_sign]

        sum_p = 0
        for model in models:
            q, p = model.predict_proba(temp_array)[0]
            sum_p += p
        probs.append((sum_p / len(models), user_brand[i]))

    sorted_probs = sorted(probs, key=itemgetter(0), reverse=True)
    top = 0
    recommend = dict()
    count_file = open('out/rec_count.txt', 'w')
    for prob in sorted_probs:
        if prob[0] < p_threshold or top >= top_threshold:
            break
        else:
            top += 1
        user_id = prob[1][0]
        brand_id = prob[1][1]
        count_file.write(user_id + '^' + brand_id + '\n')
        recommend.setdefault(user_id, set())
        recommend[user_id].add(brand_id)
    count_file.close()
    print 'get top ',top
    print 'around [-2:2] is:', sorted_probs[(top - 2):(top + 2)]

    with open('out/rec.txt', 'w') as rec_file:
        for user_id in recommend.keys():
            rec_file.write(user_id + '\t' + ','.join(recommend[user_id]) + '\n')

    count.count_common(last_day=last_day, filename='rec.txt')

def get_models(feature_select_sign, last_day):
    positive_array, negative_array, test_p, test_n = extract('t_alibaba_data.csv_sorted', last_day=last_day)
    positive_array[:, 1] = positive_array[:, 1] + positive_array[:, 0] * 1

    #feature selection
    feature_select_sign = (1, 2, 3, 9)
    positive_array = positive_array[:, feature_select_sign]
    negative_array = negative_array[:, feature_select_sign]

    positive_y = np.ones(positive_array.shape[0])
    negative_y = np.zeros(positive_array.shape[0])
    y = np.append(positive_y, negative_y)

    #sample the negative, to make it 1:1
    print 'before sampling'
    print positive_array.shape, negative_array.shape

    models = list()
    for sample_step in range(0, 30):
        sample_index = random.sample(range(negative_array.shape[0]), positive_array.shape[0])
        sample_negative_array = negative_array[sample_index, :]
        print sample_step

        X = np.append(positive_array, sample_negative_array, axis=0)
        # turn down tolerance for short training time
        lr = LogisticRegression(C=100, penalty='l2', tol=0.001)
        train_model = lr.fit(X, y)

        models.append(train_model)

    return models

def main():
    positive_array, negative_array, test_positive_array, test_negative_array = extract('t_alibaba_data.csv_sorted')
    positive_array[:, 1] = positive_array[:, 1] + positive_array[:, 0] * 1
    test_positive_array[:, 1] = test_positive_array[:, 1] + test_positive_array[:, 0] * 1

    #feature selection
    feature_select_sign = (1, 2, 3, 9)
    positive_array = positive_array[:, feature_select_sign]
    negative_array = negative_array[:, feature_select_sign]

    positive_y = np.ones(positive_array.shape[0])
    negative_y = np.zeros(positive_array.shape[0])
    y = np.append(positive_y, negative_y)

    #sample the negative, to make it 1:1
    print 'before sampling'
    print positive_array.shape, negative_array.shape

    models = list()
    for sample_step in range(0, 20):
        sample_index = random.sample(range(negative_array.shape[0]), positive_array.shape[0])
        sample_negative_array = negative_array[sample_index, :]
        print sample_negative_array.shape[0]

        X = np.append(positive_array, sample_negative_array, axis=0)
        # turn down tolerance for short training time
        lr = LogisticRegression(C=100, penalty='l2', tol=0.001)
        train_model = lr.fit(X, y)

        models.append(train_model)

    get_avg_recommend(models, feature_select_sign, 0.5, 3000, 91)
    #get_recommend(train_model, feature_select_sign, p_threshold, 40000, 122)

if __name__ == '__main__':
    #main()

    #sys.exit(0)

    feature_select_sign = (1, 2, 3, 9)
    models = get_models(feature_select_sign, 122)
    get_avg_recommend(models, feature_select_sign, 0.475, 4000, 122)

