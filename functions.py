from sklearn import preprocessing
import pandas as pd
import os
import numpy as np
import copy
import random
import matplotlib.pyplot as plt
import constants

def plot_history(history):
    hist = pd.DataFrame(history.history)
    hist['epoch'] = history.epoch

    plt.rcParams.update(constants.PARAMS)
    
    plt.figure()
    plt.xlabel('Epoch')
    plt.ylabel('Mean Absolute Error [MPa]')
    plt.plot(hist['epoch'], hist['mae'], label='Train Error', color='#4b7394')
    plt.plot(hist['epoch'], hist['val_mae'], label = 'Test Error', color='#6db1e2')
    plt.legend()
    
    plt.figure()
    plt.xlabel('Epoch')
    plt.ylabel(r'Mean Square Error [MPa\textsuperscript{2}]')
    plt.plot(hist['epoch'], hist['mse'], label='Train Error', color='#4b7394')
    plt.plot(hist['epoch'], hist['val_mse'], label = 'Test Error', color='#6db1e2')
    plt.legend()

    plt.show()

def standardize_data(X, y, scaler_x = None, scaler_y = None):

    if scaler_x == None and scaler_y == None:
        scaler_x = preprocessing.MaxAbsScaler()
        scaler_y = preprocessing.MaxAbsScaler()
        #scaler_x = preprocessing.StandardScaler()
        #scaler_y = preprocessing.StandardScaler()

        scaler_x.fit(X)
        scaler_y.fit(y)

    X = scaler_x.transform(X)
    y = scaler_y.transform(y)

    return X, y, scaler_x, scaler_y

def select_features(df):

    X = df[['exx_t-dt','eyy_t-dt','exy_t-dt', 'exx_t', 'eyy_t', 'exy_t']]
    y = df[['sxx_t','syy_t','sxy_t']]

    return X, y

def data_sampling(df_list, n_samples, rand_seed=None):

    sampled_dfs = []
    
    # df_merged = pd.concat(df_list, axis=0, ignore_index=True)

    # random.seed(rand_seed)

    # idx = random.sample(range(0, len(df_merged.index.values)), n_samples)
    # idx.sort()
    
    # data = df_merged.iloc[idx]

    for df in df_list:
        
        if rand_seed != None:
        
            idx = random.sample(range(0, len(df.index.values)), n_samples)
        
        else:
        
            idx = np.round(np.linspace(0, len(df.index.values) - 1, n_samples)).astype(int)
        
        idx.sort()
        sampled_dfs.append(df.iloc[idx])

    return sampled_dfs

def drop_features(df, drop_list):

    new_df = df.drop(drop_list, axis=1)

    return new_df

def add_delta_t(df):

    new_df = copy.deepcopy(df)

    t_initial = df['t'].values[:-1]
    t_final = df['t'].values[1:]

    delta_t = np.append(t_final - t_initial, 0)

    new_df.insert(loc=2, column='dt', value=delta_t)

    return new_df

def add_future_step(var_list, future_var_list, df):

    new_df = copy.deepcopy(df)

    for i, vars in enumerate(var_list):

        t_future = df[vars].values[1:]
        t_future = np.vstack([t_future, [0,0,0]])

        t_future = pd.DataFrame(t_future, columns=future_var_list[i])

        new_df = pd.concat([new_df, t_future], axis=1)

        new_df.drop(new_df.tail(1).index, inplace = True)

    return new_df

def add_past_step(var_list, past_var_list, df):

    new_df = copy.deepcopy(df)

    for i, vars in enumerate(var_list):

        t_past = df[vars].values[:-1]
        t_past = np.vstack([[0,0,0], t_past])

        t_past = pd.DataFrame(t_past, columns=past_var_list[i])

        new_df = pd.concat([new_df, t_past], axis=1)

    return new_df

def pre_process(df_list):

    var_list = [['sxx_t','syy_t','sxy_t'],['exx_t','eyy_t','exy_t']]
    future_var_list = [['sxx_t+dt','syy_t+dt','sxy_t+dt'],['exx_t+dt','eyy_t+dt','exy_t+dt']]
    past_var_list = [['sxx_t-dt','syy_t-dt','sxy_t-dt'],['exx_t-dt','eyy_t-dt','exy_t-dt']]

    new_dfs = []

    # Drop vars in z-direction and add delta_t
    for df in df_list:
        
        new_df = drop_features(df, ['ezz_t', 'szz_t'])
        new_dfs.append(add_delta_t(new_df))

    # Add future variables
    for i, df in enumerate(new_dfs):

        new_dfs[i] = add_future_step(var_list, future_var_list, df)

    # Add past variables
    for i, df in enumerate(new_dfs):

        new_dfs[i] = add_past_step(var_list, past_var_list, df)

    return new_dfs

def load_dataframes(directory):

    file_list = []

    for r, d, f in os.walk(directory):
        for file in f:
            if 'train' and '.csv' in file:
                file_list.append(directory + file)

    headers = ['id', 't', 'sxx_t', 'syy_t', 'szz_t', 'sxy_t', 'exx_t', 'eyy_t', 'ezz_t', 'exy_t']

    # Loading training datasets
    df_list = [pd.read_csv(file, names=headers, sep=',') for file in file_list]

    df_list = pre_process(df_list)

    return df_list


# def plot_learning_curve(train_sizes, train_scores, test_scores):
    
#     train_scores_mean = np.mean(-train_scores, axis=1)
#     train_scores_std = np.std(-train_scores, axis=1)
#     test_scores_mean = np.mean(-test_scores, axis=1)
#     test_scores_std = np.std(-test_scores, axis=1)

#     #plt.rcParams.update(constants.PARAMS)
    
#     plt.xlabel("Training samples")
#     plt.ylabel("Score")    

#     # Plot learning curve
#     plt.grid(alpha=0.1)
#     plt.fill_between(train_sizes, train_scores_mean - train_scores_std,
#                          train_scores_mean + train_scores_std, alpha=0.1,
#                          color="r")
#     plt.fill_between(train_sizes, test_scores_mean - test_scores_std,
#                          test_scores_mean + test_scores_std, alpha=0.1,
#                          color="g")
#     plt.plot(train_sizes, train_scores_mean, 'o-', color="r",
#                  label="Training score")
#     plt.plot(train_sizes, test_scores_mean, 'o-', color="g",
#                  label="Cross-validation score")
#     plt.legend(loc="best")
    
#     # create_folder('prints')    
#     # save_fig(plt, 'prints/', 'learning','curves')
#     plt.show()