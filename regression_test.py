import math
import pandas as pd 
import numpy as np
from sklearn import linear_model
import time
import sys
import itertools

#load dataset
data = pd.read_csv("C:\Users\Brandon\Dropbox\CurrentClasses\CS 229\Project\sample_training_set.csv");

columns = ['R', 'Single', 'Double','Triple', 'HR', 'RBI', 'BB', 'HBP', 'SB', 'CS'];

stats_size = len(columns);

data = data.drop(data.columns[0], axis = 1);

col_to_check = ['R_1', 'Single_1', 'Double_1', 'Triple_1', 'HR_1', 'RBI_1', 'BB_1', 'HBP_1', 'SB_1', 'CS_1'];

num_feat = 2;
data = data.reset_index(drop = True);


sub = data.columns[stats_size:stats_size*num_feat];

data = data.dropna(subset= sub, how='all');
data = data.reset_index(drop = True);
#data = np.all(np.isfinite(data));




data.to_csv("C:\Users\Brandon\Dropbox\CurrentClasses\CS 229\Project\check.csv");


# split features for train/games_for_player sets
data_length = data.shape[0]-1;
half_index = data_length/2;

print ("num samples: " + str(data_length));
print ("data length: " + str(data_length/2));
batting_feat_train = data.iloc[0:half_index, stats_size:(stats_size)*num_feat];
#print batting_feat_train;

print ("batting feat train size: " + str(batting_feat_train.shape[0]));
batting_feat_test = data.iloc[half_index:half_index*2, stats_size:(stats_size)*num_feat];
print ("batting feat test size: " + str(batting_feat_test.shape[0]));
print batting_feat_test;

# split targets for train/games_for_player sets
batting_targ_train =  data.loc[0:half_index-1, 'fantasy_points'];
print ("batting targ train size: " + str(batting_targ_train.shape[0]));
#print batting_targ_train

batting_targ_test = data.loc[half_index:half_index*2-1, 'fantasy_points'];
print ("batting targ test size: " + str(batting_targ_test.shape[0]));
print batting_targ_test








# create linear regression object
regr = linear_model.LinearRegression();

#train 
regr.fit(batting_feat_train, batting_targ_train);

# coefficients
print("Coefficients: \n", regr.coef_);

# MSE
print("Residual sum of squares (test): %.2f" %np.mean((regr.predict(batting_feat_test) - batting_targ_test) ** 2));
print("Residual sum of squares (train): %.2f" %np.mean((regr.predict(batting_feat_train) - batting_targ_train) ** 2));

# Explained variance score: 1 is perfect prediction
print('Variance score: %.2f' % regr.score(batting_feat_test, batting_targ_test))