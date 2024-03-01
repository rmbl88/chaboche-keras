import constants
import joblib
from functions import (GRUModel, GRUModelJit, read_mesh)
from contour import plot_fields
import matplotlib.pyplot as plt
import pandas as pd
from cycler import cycler
import torch
import numpy as np
import os
from constants import *
import glob
import pyarrow.parquet as pq
from tqdm import tqdm

from gru_nn import customGRU

#-------------------------------------------------------------------------
#                          METHOD DEFINITIONS
#-------------------------------------------------------------------------
def load_pkl(file: str):
    return joblib.load(file)

def scan_ann_files(run: str, dir: str, key: str):

    SCAN_DIR = os.path.join('outputs', dir, 'models')
    
    for f in glob.glob(os.path.join(SCAN_DIR, f'*{run}*')):
    
        if key in f:
            file = f           

    return file

def load_file(run: str, dir: str, key: str):
    
    f = scan_ann_files(run, dir, key)

    return load_pkl(f)

def create_dir(dir: str, root_dir: str):

    ROOT_DIR = root_dir
    DIR = os.path.join(ROOT_DIR, dir)

    try:    
        os.makedirs(DIR)        
    except FileExistsError:
        pass

    return DIR

def get_ann_model(run: str, dir: str):
    
    f = scan_ann_files(run, dir, '.pt')
    
    return torch.load(f)

def load_data(dir: str, ftype: str):

    DIR = dir
    
    files = glob.glob(os.path.join(DIR, f'*.{ftype}'))
    
    df_list = [pd.read_csv(file) for file in tqdm(files, desc='Importing dataset files', bar_format=FORMAT_PBAR)]

    return df_list

def get_field_data(df: pd.DataFrame, vars: dict, pred_vars: dict, n_elems: int, n_tps: int):

    T_STEPS = [round((n_tps-1)*0.5), n_tps-1]
    #T_STEPS = [19,20,21,22,23]

    KEYS = sum([[v for k,v in var.items()] for k_,var in vars.items()],[])

    field_dict = {t: {k: {'abaqus': None, 'ann': None, 'err': None} for k in KEYS} for t in T_STEPS}

    for k, d in vars.items():
        for idx, v_name in d.items():
            if v_name == 'mises':
                s = df[KEYS[:-1]].values.reshape(n_tps,n_elems,-1).transpose(2,1,0)
                s_hat = pred_vars[k].reshape(n_elems, n_tps, -1).transpose(2,0,1)
                x = np.expand_dims(get_mises(*s),-1)
                y = np.expand_dims(get_mises(*s_hat),-1)
            else:
                x = df[v_name].values.reshape(n_tps,n_elems,1).transpose(1,0,2)
                y = pred_vars[k][:,idx].reshape(n_elems,n_tps,1)

            for t, d_ in field_dict.items():
                d_[v_name]['abaqus'] = x[:,t,:]
                d_[v_name]['ann'] = y[:,t,:]
                d_[v_name]['err'] = np.abs(x[:,t,:]-y[:,t,:])

    return field_dict

def import_mesh(dir: str):

    mesh, connectivity, _ = read_mesh(dir)

    nodes = mesh[:,1:]
    connectivity = connectivity[:,1:] - 1

    return nodes, connectivity

def get_re(pred,real):

    '''Calculates the Relative error between a prediction and a real value.'''
    
    re = np.abs(pred-real)*100/(1+np.abs(real))

    return re

def get_mises(s_x, s_y, s_xy):
    return np.sqrt(np.square(s_x)+np.square(s_y)-s_x*s_y+3*np.square(s_xy))

def batch_jacobian(y,x, mean, var):
    
    batch = x.size(0)
    inp_dim = x.size(-1)
    out_dim = y.size(-1)

    grad_output = torch.eye(out_dim).unsqueeze(1).repeat(1,batch,1)
    gradient = torch.autograd.grad(y,x,grad_output,retain_graph=True, create_graph=True, is_grads_batched=True)
    J = gradient[0][:,:,-1].permute(1,0,2)
    
    # for i in range(out_dim):
    #     grad_output = torch.zeros([batch,out_dim])
    #     grad_output[:,i] = 1

    #     gradient = torch.autograd.grad(y,x,grad_output,retain_graph=True, create_graph=True)
    #     J[:,i,:] = gradient[0][:,-1]
    #     #print("hey")
    
    return J*(1-mean)/var


#--------------------------------------------------------------------------

# Initializing Matplotlib settings
# plt.rcParams.update(constants.PARAMS)
# default_cycler = (cycler(color=["#ef476f","#118ab2","#073b4c"]))
# plt.rc('axes', prop_cycle=default_cycler)

# Setting Pytorch floating point precision
torch.set_default_dtype(torch.float64)

# Defining ann model to load
#RUN = 'solar-planet-147'
RUN = 'fine-rain-207'
#RUN = 'summer-water-157'
#RUN = 'whole-puddle-134'
#RUN = 'lemon-star-431'

# Defining output directory
#DIR = 'crux-plastic_sbvf_abs_direct'
DIR = 'sbvfm_indirect_crux_gru'

# Creting output directories
RUN_DIR = create_dir(dir=RUN, root_dir=os.path.join('outputs', DIR, 'val'))

# Importing mesh
NODES, CONNECT = import_mesh(TRAIN_MULTI_DIR)

# Loading model architecture
FEATURES, OUTPUTS, INFO, N_UNITS, H_LAYERS, SEQ_LEN = load_file(RUN, DIR, 'arch.pkl')

# Loading data scaler
SCALER_DICT = load_file(RUN, DIR, 'scaler_x.pkl')

ELEMS_VAL = [1]

# MODEL_INFO = {
#     'in': FEATURES,
#     'out': OUTPUTS,
#     'info': INFO,
#     'min': MIN,
#     'max': MAX
# }

# Setting up ANN model
#model_1 = GRUModelJit(input_dim=len(FEATURES),hidden_dim=N_UNITS,layer_dim=H_LAYERS,output_dim=len(OUTPUTS))
model_1 = GRUModel(input_dim=len(FEATURES),hidden_dim=N_UNITS,layer_dim=H_LAYERS,output_dim=len(OUTPUTS))
#model_1 = customGRU(input_dim=len(FEATURES), hidden_dim=N_UNITS, layer_dim=H_LAYERS, output_dim=len(OUTPUTS), layer_norm=False)
model_1.load_state_dict(get_ann_model(RUN, DIR))   
# model_1.to(torch.device('cpu')) 
# model_1.eval()
# model_1(torch.ones(1,4,3))
# traced_model = torch.jit.trace(model_1,torch.ones(1,4,3).to(torch.device('cpu')))

# traced_model.eval()
# traced_model.save('jit_model.pt')

#Loading validation data
df_list = load_data(dir='one_elem/', ftype='csv')

cols = ['e_xx','e_yy','e_xy','s_xx','s_yy','s_xy','s_xx_pred','s_yy_pred','s_xy_pred',
        'mre_sx','mre_sy','mre_sxy']

with torch.no_grad():
    last_tag = ''
    for i, df in enumerate(df_list):
        
        # Identifying mechanical test
        tag = df['tag'][0]

        #------------------------------------------------------------------------------------
        #                       CREATING OUTPUT DIRECTORIES
        #------------------------------------------------------------------------------------
        TRIAL_DIR = create_dir(dir=tag,root_dir=RUN_DIR)
        
        DATA_DIR = create_dir(dir='data',root_dir=TRIAL_DIR)

        PLOT_DIR = create_dir(dir='plots',root_dir=TRIAL_DIR)

        #------------------------------------------------------------------------------------
        
        # Number of time steps and number of elements
        n_tps = len(list(set(df['t'])))
        n_elems = len(list(set(df['id'])))
        
        X = df[FEATURES].values
        y = df[OUTPUTS].values
        #info = df[INFO]

        pad_zeros = torch.zeros((SEQ_LEN-1) * n_elems, X.shape[-1])
        
        #pad_zeros = torch.zeros(SEQ_LEN * n_elems, X.shape[-1])

        X = torch.cat([pad_zeros, torch.from_numpy(X)], 0)

        # x_std = (X - MIN) / (MAX - MIN)
        # X_scaled = x_std * (MAX - MIN) + MIN
        if SCALER_DICT['type'] == 'standard':
            X_scaled = (X-SCALER_DICT['stat_vars'][1])/SCALER_DICT['stat_vars'][0]
        elif SCALER_DICT['type'] == 'minmax':
            x_std = (X - SCALER_DICT['stat_vars'][0]) / (SCALER_DICT['stat_vars'][1] - SCALER_DICT['stat_vars'][0])
            X_scaled = x_std * (SCALER_DICT['stat_vars'][2][1] - SCALER_DICT['stat_vars'][2][0]) + SCALER_DICT['stat_vars'][2][0]
        # else:
        #     pass
            #x_std = (X - MIN) / (MAX - MIN)
            #X_scaled = x_std * (MAX - MIN) + MIN
        
        x = X_scaled.reshape(n_tps + SEQ_LEN-1, n_elems, -1)
        
        x = x.unfold(0,SEQ_LEN,1).permute(1,0,3,2)
        x = x.reshape(-1,*x.shape[2:])
        
        y = torch.from_numpy(y)
        
        y = y.reshape(n_tps,n_elems,-1).permute(1,0,2)
        y = y.reshape(-1,y.shape[-1])



        t = torch.from_numpy(df['t'].values).reshape(n_tps, n_elems, 1)
       
        s = model_1(x) # stress rate.

        #------------------------------------------------------------------------------------
        #                              RESHAPING DATA
        #------------------------------------------------------------------------------------

        s = s.reshape(n_elems,n_tps,-1)
        y = y.reshape(n_elems,n_tps,-1)

        for elem in ELEMS_VAL:
            idx = elem - 1
            # Strain values - Abaqus
            ex_abaqus = df[df['id']==elem]['exx_t'].values.reshape(-1,1)
            ey_abaqus = df[df['id']==elem]['eyy_t'].values.reshape(-1,1)
            exy_abaqus = df[df['id']==elem]['exy_t'].values.reshape(-1,1)
            

            # Stress values - Abaqus
            sx_abaqus = df[df['id']==elem]['sxx_t'].values.reshape(-1,1)
            sy_abaqus = df[df['id']==elem]['syy_t'].values.reshape(-1,1)
            sxy_abaqus = df[df['id']==elem]['sxy_t'].values.reshape(-1,1)

            # Stress predictions - ANN
            sx_pred = s[idx,:,0].reshape(-1,1)
            sy_pred = s[idx,:,1].reshape(-1,1)
            sxy_pred= s[idx,:,2].reshape(-1,1)

            ###################################################################################
            #                             RELATIVE ERRORS
            ###################################################################################

            mre_sx = get_re(sx_pred, sx_abaqus).numpy().reshape(-1,1)
            mre_sy = get_re(sy_pred, sy_abaqus).numpy().reshape(-1,1)
            mre_sxy = get_re(sxy_pred, sxy_abaqus).numpy().reshape(-1,1)

            ###################################################################################

            if tag != last_tag:
                print("\n%s\t\tSxx\tSyy\tSxy\tS1\tS2\n" % (tag))
            
            print("Elem #%i\t\t%0.3f\t%0.3f\t%0.3f" % (elem, np.mean(mre_sx), np.mean(mre_sy), np.mean(mre_sxy)))

            # cols = ['e_xx','e_yy','e_xy','s_xx','s_yy','s_xy','s_xx_pred','s_yy_pred','s_xy_pred',
            #         'e_1','e_2','s_1','s_2','s_1_pred','s_2_pred','de_1','de_2','ds_1','ds_2',
            #         'dy_1','dy_2','mre_sx','mre_sy','mre_sxy','mre_s1','mre_s2']

            res = np.concatenate([ex_abaqus,ey_abaqus,exy_abaqus,sx_abaqus,sy_abaqus,sxy_abaqus,sx_pred,sy_pred,sxy_pred, mre_sx, mre_sy, mre_sxy], axis=1)
            
            results = pd.DataFrame(res, columns=cols)
            
            results.to_csv(os.path.join(DATA_DIR, f'{tag}_el-{elem}.csv'), header=True, sep=',', float_format='%.12f')

            last_tag = tag