import numpy as np
import pickle
import pandas as pd
#import matplotlib.pyplot as plt


test_path = 'data/dengue_features_test.csv'
train_path = 'data/dengue_features_train.csv'
output_path = 'result/result.csv'

def preprocess(feature_path):
    train_features = pd.read_csv(feature_path,index_col=[0,1])

    sj_train_features = train_features.loc['sj']

    iq_train_features = train_features.loc['iq']

    sj_train_features.drop('week_start_date', axis=1, inplace=True)
    #sj_train_features.drop('ndvi_se', axis=1, inplace=True)
    #sj_train_features.drop('ndvi_sw', axis=1, inplace=True)
    sj_train_features.drop('ndvi_ne', axis=1, inplace=True)
    #sj_train_features.drop('ndvi_nw', axis=1, inplace=True)
    iq_train_features.drop('week_start_date', axis=1, inplace=True)
    #iq_train_features.drop('ndvi_se', axis=1, inplace=True)
    #iq_train_features.drop('ndvi_sw', axis=1, inplace=True)
    #iq_train_features.drop('ndvi_ne', axis=1, inplace=True)
    #iq_train_features.drop('ndvi_nw', axis=1, inplace=True)

    sj_train_features.fillna(method='ffill', inplace=True)
    iq_train_features.fillna(method='ffill', inplace=True)

    sj_train_features = np.array(sj_train_features)
    iq_train_features = np.array(iq_train_features)

    return (sj_train_features,iq_train_features)

def add_time(lag,train):
    new_train = np.array([np.append(train[j],train[j-lag:j]) for j in range(lag,len(train),1)])
    return new_train

def moving_average(a, n=3) :
    ret = np.cumsum(a, dtype=float)
    t = ret[n:] - ret[:-n]
    return np.append(ret[n-1],t) / n
    #ret[n:] = ret[n:] - ret[:-n]
    #return ret[n - 1:] / n


def main():
    (sj_test,iq_test) = preprocess(test_path)
    (sj_train,iq_train) = preprocess(train_path)
    lag = 3
    sj_mean = np.load('npy/s_mean.npy')
    sj_std = np.load('npy/s_std.npy')
    iq_mean = np.load('npy/i_mean.npy')
    iq_std = np.load('npy/i_std.npy')
    sj_label_mean = np.load('npy/sj_label_mean.npy')
    sj_label_std = np.load('npy/sj_label_std.npy')
    iq_label_mean = np.load('npy/iq_label_mean.npy')
    iq_label_std = np.load('npy/iq_label_std.npy')

    sj_test = (sj_test-sj_mean)/sj_std
    iq_test = (iq_test-iq_mean)/iq_std
    sj_train = (sj_train-sj_mean)/sj_std
    iq_train = (iq_train-iq_mean)/iq_std

    sj_test = add_time(lag,np.concatenate((sj_train[-lag:],sj_test),axis=0))
    iq_test = add_time(lag,np.concatenate((iq_train[-lag:],iq_test),axis=0))
    length = sj_test.shape[0]
    #print(sj_test.shape)
    #print(iq_test.shape)
    
    s_clf_1 = pickle.load(open('model/s_clf_xgb_try.pkl','rb'))
    s_clf_2 = pickle.load(open('model/s_clf_bag_try.pkl','rb'))
    s_clf_3 = pickle.load(open('model/s_clf_xtree_try.pkl','rb'))
    s_clf_4 = pickle.load(open('model/s_clf_gb_try.pkl','rb'))

    i_clf_1 = pickle.load(open('model/i_clf_xgb_try.pkl','rb'))
    i_clf_2 = pickle.load(open('model/i_clf_bag_try.pkl','rb'))
    i_clf_3 = pickle.load(open('model/i_clf_xtree_try.pkl','rb'))
    #i_clf_4 = pickle.load(open('i_clf_ada.pkl','rb'))
    
    sj_predictions_1 = s_clf_1.predict(sj_test)
    sj_predictions_2 = s_clf_2.predict(sj_test)
    sj_predictions_3 = s_clf_3.predict(sj_test)
    sj_predictions_4 = s_clf_4.predict(sj_test)
    sj_predictions = np.ones(len(sj_predictions_1))
    sj_predictions[0:52] = sj_predictions_3[0:52]
    sj_predictions[50:104] = (sj_predictions_4[50:104] + sj_predictions_3[50:104])/2
    sj_predictions[102:156] = (sj_predictions_4[102:156])
    sj_predictions[154:208] = (sj_predictions_3[154:208] + sj_predictions_1[154:208])/2
    sj_predictions[206:] = (sj_predictions_3[206:] + sj_predictions_4[206:])/2

    iq_predictions_1 = i_clf_1.predict(iq_test)
    iq_predictions_2 = i_clf_2.predict(iq_test)
    iq_predictions_3 = i_clf_3.predict(iq_test)
    iq_predictions = (iq_predictions_1+iq_predictions_2+iq_predictions_3)/3

    sj_predictions = sj_predictions.reshape(-1,52)
    sj_predictions = sj_predictions*sj_label_std + sj_label_mean
    sj_predictions = sj_predictions.reshape(-1,1)
    sj_predictions = sj_predictions.reshape(len(sj_predictions))

    iq_predictions = iq_predictions.reshape(-1,52)
    iq_predictions = iq_predictions*iq_label_std + iq_label_mean
    iq_predictions = iq_predictions.reshape(-1,1)
    iq_predictions = iq_predictions.reshape(len(iq_predictions))

    sj_predictions = np.round(sj_predictions).astype(int)
    iq_predictions = np.round(iq_predictions).astype(int)

    new_sj = moving_average(sj_predictions,n=3) # n=3
    new_iq = moving_average(iq_predictions) # n=3

    sj_predictions[2:] = new_sj
    iq_predictions[2:] = new_iq
    shift = 2
    sj_predictions[shift:] = sj_predictions[:-shift]
    iq_predictions[shift:] = iq_predictions[:-shift]
    #print('len',sum(sj_predictions>=75))
    #print(np.where(sj_predictions>75))
    #print(sj_predictions[sj_predictions>75])
    #sj_predictions[sj_predictions >= 75] += 10
    '''    
    fig = plt.figure()
    index = np.arange(len(sj_predictions))
    plt.title('ada result')
    plt.plot(index,sj_predictions)
    plt.xticks(10*np.arange(25))
    plt.show()
    '''
    submission = pd.read_csv('data/submission_format.csv',index_col=[0,1,2])
    submission.total_cases = np.concatenate([sj_predictions, iq_predictions])
    submission.to_csv(output_path)


if __name__=='__main__':
    main()
