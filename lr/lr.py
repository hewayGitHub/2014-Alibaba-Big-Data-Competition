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

purchase_weight = 1

#get recommend
def get_recommend(model, feature_select_sign, p_threshold, top_threshold, last_day):
    print '-----------------------'
    X_list, user_brand = get_X('t_alibaba_data.csv_sorted', last_day=last_day)
    probs = list()
    for i in range(0, len(X_list)):
        temp_list = list()
        temp_list.append(X_list[i])
        temp_array = np.asarray(temp_list, dtype=np.float32)
        temp_array[:, 1] = temp_array[:, 1] + temp_array[:, 0] * purchase_weight
        temp_array = temp_array[:, feature_select_sign]
        q, p = model.predict_proba(temp_array)[0]
        probs.append((p, user_brand[i]))

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

def get_model(feature_select_sign, last_day):
    positive_array, negative_array, test_p, test_n = extract('t_alibaba_data.csv_sorted', last_day=last_day)
    positive_array[:, 1] = positive_array[:, 1] + positive_array[:, 0] * purchase_weight

    #feature selection
    positive_array = positive_array[:, feature_select_sign]
    negative_array = negative_array[:, feature_select_sign]

    #sample the negative, to make it 1:1
    print 'before sampling'
    print positive_array.shape, negative_array.shape
    random.seed(0)
    index = random.randint(0, negative_array.shape[0] - positive_array.shape[0])
    negative_array = negative_array[index:index + positive_array.shape[0], :]
    print 'after sampling'
    print positive_array.shape, negative_array.shape

    positive_y = np.ones(positive_array.shape[0])
    negative_y = np.zeros(negative_array.shape[0])

    X = np.append(positive_array, negative_array, axis=0)
    y = np.append(positive_y, negative_y)

    #normolize X according to each feature
    #preprocessing.normalize(X, 'l2', axis=0)

    # Set regularization parameter
    for i, C in enumerate(10. ** np.arange(2, 3)):
        # turn down tolerance for short training time
        lr = LogisticRegression(C=C, penalty='l2', tol=0.001)
        #print cross_validation.cross_val_score(lr, X, y)
        model = lr.fit(X, y)
        pickle.dump(model, open('in/lr_model', 'w'))

        coef = model.coef_.ravel()
        print feature_select_sign
        print coef

    return model

def main():
    positive_array, negative_array, test_positive_array, test_negative_array = extract('t_alibaba_data.csv_sorted')
    positive_array[:, 1] = positive_array[:, 1] + positive_array[:, 0] * purchase_weight
    test_positive_array[:, 1] = test_positive_array[:, 1] + test_positive_array[:, 0] * purchase_weight

    #feature selection
    feature_select_sign = (1, 2, 3, 9)
    positive_array = positive_array[:, feature_select_sign]
    negative_array = negative_array[:, feature_select_sign]
    test_positive_array = test_positive_array[:, feature_select_sign]
    test_negative_array = test_negative_array[:, feature_select_sign]

    #sample the negative, to make it 1:1
    print 'before sampling'
    print positive_array.shape, negative_array.shape
    random.seed(0)
    index = random.randint(0, negative_array.shape[0] - positive_array.shape[0])
    negative_array = negative_array[index:index + positive_array.shape[0], :]
    print 'after sampling'
    print positive_array.shape, negative_array.shape

    positive_y = np.ones(positive_array.shape[0])
    negative_y = np.zeros(negative_array.shape[0])
    test_positive_y = np.ones(test_positive_array.shape[0])
    test_negative_y = np.zeros(test_negative_array.shape[0])

    X = np.append(positive_array, negative_array, axis=0)
    y = np.append(positive_y, negative_y)
    test_X = np.append(test_positive_array, test_negative_array, axis=0)
    test_y = np.append(test_positive_y, test_negative_y)

    #normolize X according to each feature
    #preprocessing.normalize(X, 'l2', axis=0)

    # Set regularization parameter
    for i, C in enumerate(10. ** np.arange(2, 3)):
        # turn down tolerance for short training time
        lr = LogisticRegression(C=C, penalty='l2', tol=0.001)
        #print cross_validation.cross_val_score(lr, X, y)
        train_model = lr.fit(X, y)
        pickle.dump(train_model, open('in/train_model', 'w'))

        coef = train_model.coef_.ravel()
        print feature_select_sign
        print coef

        print '-----------------'
        print 'positive:', test_positive_y.shape
        print 'accuracy:', train_model.score(test_positive_array, test_positive_y)
        print 'negative:', test_negative_y.shape
        print 'accuracy:', train_model.score(test_negative_array, test_negative_y)
        print 'all:', test_y.shape
        print 'accuracy:', train_model.score(test_X, test_y)

        print 'test recommend hit:'
        result = list()
        has_purchase_count = 0
        rec_has_purchase_count = 0
        for j in range(0, test_positive_y.shape[0]):
            q, p = train_model.predict_proba(test_positive_array[j, :])[0]
            result.append((p, 1))

        for j in range(0, test_negative_y.shape[0]):
            q, p = train_model.predict_proba(test_negative_array[j, :])[0]
            result.append((p, 0))

        sorted_result = sorted(result, key=itemgetter(0), reverse=True)

        hit = 0
        top = 0
        p_threshold = 0.455
        top_threshold = 3000
        for prob in sorted_result:
            if prob[0] < p_threshold or top >= top_threshold:
                break
            else:
                top += 1
            if prob[1] == 1:
                hit += 1
        print 'get top ',top
        print 'around [-2:2] is:', sorted_result[(top - 2):(top + 2)]
        print top, hit
        precision = hit * 1.0 / top
        recall = hit * 1.0 / test_positive_array.shape[0]
        print precision, recall, 2 * precision * recall / (precision + recall)

        get_recommend(train_model, feature_select_sign, p_threshold, top_threshold, 91)
        #get_recommend(train_model, feature_select_sign, p_threshold, 40000, 122)

if __name__ == '__main__':
    #main()

    #sys.exit(0)

    feature_select_sign = (1, 2, 3, 9)
    model = get_model(feature_select_sign, 122)
    get_recommend(model, feature_select_sign, 0.475, 3000, 122)

