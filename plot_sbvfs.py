from turtle import color
from matplotlib.pyplot import draw
import numpy as np
import torch
import joblib
import matplotlib.animation as animation
import pylab as plt
from matplotlib import colors
from mpl_toolkits.axes_grid1 import make_axes_locatable
from matplotlib.gridspec import GridSpec

def animate(i):
    global contours, v_u, v_e, fig, cmap, bar_x, bar_y, bar_exx, bar_eyy, bar_exy

    k = 0
    for j,contour in enumerate(contours):

        if j == 0:
            u_ = torch.reshape(v_u[vf][i][::2],X.shape)
            contour.axes.set_title('t_inc = %i' % (i))
        elif j == 1:
            u_ = torch.reshape(v_u[vf][i][1::2],X.shape)
            contour.axes.set_title('t_inc = %i' % (i))
        else:
            u_ = torch.reshape(v_e[vf][i][:,k],XC.shape)
            k += 1
        
        v_min = torch.min(u_)
        v_max = torch.max(u_)
        bounds = np.linspace(v_min*1.1, v_max*1.1,13)
        norm = colors.BoundaryNorm(bounds,cmap.N)

        contour.set_data(u_)
        contour.set_norm(norm)
        

        # if j == 0:
        #     bar_x.set_ticks(bounds)
               
        # else:
        #     bar_y.set_ticks(bounds)
            
        
        

    return contours

x = np.linspace(0,3,4)
y = np.linspace(0,3,4)

X,Y = np.meshgrid(x,y)

xc = np.linspace(0.5,2.5,3)
yc = np.linspace(0.5,2.5,3)

XC, YC = np.meshgrid(xc,yc)

vfs = joblib.load('sbvfs.pkl')

tags = list(vfs.keys())

for tag in tags:

    v_u = torch.stack([v for k,v in vfs[tag]['u'].items() if v is not None],1)
    v_e = torch.stack([v for k,v in vfs[tag]['e'].items() if v is not None],1)

    cmap = plt.cm.get_cmap('jet')    

    for vf in range(v_u.shape[0]):

        #fig, [ax1, ax2] = plt.subplots(1,2)
        fig = plt.figure()
        fig.suptitle(tag+'_VFu_'+str(vf))
        fig.set_size_inches(16, 8, forward=True)
        gs = GridSpec(2, 6, figure=fig)

        ax1 = fig.add_subplot(gs[0,:3])
        ax1.set_xlim(0,3)
        ax1.set_ylim(0,3)
        ax1.set_xlabel('u*_x')

        ax2 = fig.add_subplot(gs[0,3:])
        ax2.set_xlim(0,3)
        ax2.set_ylim(0,3)
        ax2.set_xlabel('u*_y')

        ax3 = fig.add_subplot(gs[1,:2])
        ax3.set_xlabel('e*_xx')
        ax4 = fig.add_subplot(gs[1,2:4])
        ax4.set_xlabel('e*_yy')
        ax5 = fig.add_subplot(gs[1,4:])
        ax5.set_xlabel('e*_xy')

        #cont_x = ax1.contourf(X, Y, torch.reshape(v_u[vf][0][::2],X.shape), 21)
        cont_x=ax1.imshow(np.zeros_like(X), origin='lower', interpolation='bicubic', aspect='equal',extent=[0, 3, 0, 3], cmap=cmap)
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        divider_x = make_axes_locatable(ax1)
        cax_x = divider_x.append_axes("right", size="5%", pad=0.05)
        bar_x = plt.colorbar(cont_x,cax=cax_x)

        cont_y=ax2.imshow(np.zeros_like(X), origin='lower', interpolation='bicubic', aspect='equal',extent=[0, 3, 0, 3], cmap=cmap)
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        divider_x = make_axes_locatable(ax2)
        cax_y = divider_x.append_axes("right", size="5%", pad=0.05)
        bar_y = plt.colorbar(cont_y,cax=cax_y)
        
        cont_exx=ax3.imshow(np.zeros_like(XC), origin='lower', interpolation='bicubic', aspect='equal',extent=[0, 3, 0, 3], cmap=cmap)
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        divider_exx = make_axes_locatable(ax3)
        cax_exx = divider_exx.append_axes("right", size="5%", pad=0.05)
        bar_exx = plt.colorbar(cont_exx,cax=cax_exx)

        cont_eyy=ax4.imshow(np.zeros_like(XC), origin='lower', interpolation='bicubic', aspect='equal',extent=[0, 3, 0, 3], cmap=cmap)
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        divider_eyy = make_axes_locatable(ax4)
        cax_eyy = divider_eyy.append_axes("right", size="5%", pad=0.05)
        bar_eyy = plt.colorbar(cont_eyy,cax=cax_eyy)

        cont_exy=ax5.imshow(np.zeros_like(XC), origin='lower', interpolation='bicubic', aspect='equal',extent=[0, 3, 0, 3], cmap=cmap)
        # create an axes on the right side of ax. The width of cax will be 5%
        # of ax and the padding between cax and ax will be fixed at 0.05 inch.
        divider_exy = make_axes_locatable(ax5)
        cax_exy = divider_exy.append_axes("right", size="5%", pad=0.05)
        bar_exy = plt.colorbar(cont_exy,cax=cax_exy)
        
        
        contours = [cont_x, cont_y, cont_exx, cont_eyy, cont_exy]

        anim = animation.FuncAnimation(fig, animate,frames=v_u.shape[1], repeat=False)
        anim.save('anim_%s_vf_%i.gif'%(tag,vf), writer=animation.PillowWriter(fps=1))
        plt.close(fig)
        print('hey')


print('hey')