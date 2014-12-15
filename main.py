#!/usr/bin/env python
#-*- coding: utf-8 -*-
__author__ = 'heway'

import sys

reload(sys)
sys.setdefaultencoding('utf-8')

from preprocess import sort, union
from lr import lr, lr_sample, lr_click_sample


#sort the record by user_id, brand_id, visit_datetime in ascending order
print '>> sort the input data'
sort.main()

#the first logistic regression model, only put the short terms click into consideration, that means ignore the click
#before the most recent purchase
#the recommend result of this model is saved in out/rec.txt
print '>> the first logistic regression model with p(0.46)'
feature_select_sign = (1, 2, 3, 9)
models = lr.get_model(feature_select_sign, 122)
lr.get_recommend(models, feature_select_sign, 0.46, 3000, 122)

#the second logistic regression model, put all the click before the assumed purchase day into consideration
#the recommend result of this model is saved in out/rec_click.txt
print '>> the second logistic regression model with p(0.45)'
models = lr_click_sample.get_models(feature_select_sign, 122)
lr_click_sample.get_avg_recommend(models, feature_select_sign, 0.45, 5000, 122)


#union the result, the result is in out/union.txt, f1-socre is 7.06%
union.union_all(['rec.txt', 'rec_click.txt'])

#union the result above and the result when set the p threshold is 0.475, the f1-score is 7.12%
print '>> the improved first logistic regression model with p(0.475)'
models = lr_sample.get_models(feature_select_sign, 122)
lr_sample.get_avg_recommend(models, feature_select_sign, 0.475, 3000, 122)
union.union_all(['union.txt', 'rec.txt'])







