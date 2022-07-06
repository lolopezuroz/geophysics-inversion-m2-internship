import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
from scipy import signal

tif = Image.open('/home/lorenzo/geophysic_inversion/process/create_dataset/dem_crop.tif')
#tif = Image.open('/home/lorenzo/geophysic_inversion/create_dataset/output_data/SwissALTI3D_r2019_tiles/SwissALTI3D_r2019_tile_150.tif')
array = np.array(tif)

def coherence(x,y):

    #return (x * y)/(np.abs(x**2)*np.abs(y**2))**.5
    return (y/x)

def slope1(array):
    
    sq2 = 2**.5

    window = np.array([[sq2*(-1+1j), 1j, sq2*(1+1j)],
                       [-1         , 0 , 1         ],
                       [sq2*(-1-1j),-1j, sq2*(1-1j)]])

    slope = signal.convolve2d(array,window)

    return slope

def slope2(array):

    sq2 = 2**.5

    distance = np.array([[sq2,1     ,sq2],
                         [1  ,1     ,1  ],
                         [sq2,1     ,sq2]])

    angles = np.array([[np.pi*3/4,np.pi/2  ,np.pi/4  ],
                       [np.pi    ,np.nan   ,0        ],
                       [np.pi*5/4,np.pi*3/2,np.pi*7/4]])

    slope = np.zeros_like(array)*1j

    xn, yn = np.shape(array)

    for x in range(1,xn-1):
        for y in range(1,yn-1):

            gradient = (array[x,y] - array[x-1:x+2,y-1:y+2])/distance

            slope[x,y] = np.max(gradient) * np.exp(angles.flatten()[np.argmax(gradient)]*1j)

    return slope

slopeA = slope1(array)
slopeB = slope2(array)

fig = plt.figure()

ax1 = fig.add_subplot(2,4,1)
ax2 = fig.add_subplot(2,4,2)
ax3 = fig.add_subplot(2,4,3)
ax4 = fig.add_subplot(2,4,4)

ax5 = fig.add_subplot(2,4,5)
ax6 = fig.add_subplot(2,4,6)
ax7 = fig.add_subplot(2,4,7)
ax8 = fig.add_subplot(2,4,8)

ax1.imshow(np.abs(slopeA)  ,cmap="plasma"  ,vmin=0     ,vmax=100  )
ax2.imshow(np.angle(slopeA),cmap="hsv"     ,vmin=-np.pi,vmax=np.pi)
ax3.imshow(slopeA.real     ,cmap="coolwarm",vmin=-100  ,vmax=100  )
ax4.imshow(slopeA.imag     ,cmap="coolwarm",vmin=-100  ,vmax=100  )

ax5.imshow(np.abs(slopeB)  ,cmap="plasma"  ,vmin=0     ,vmax=100  )
ax6.imshow(np.angle(slopeB),cmap="hsv"     ,vmin=-np.pi,vmax=np.pi)
ax7.imshow(slopeB.real     ,cmap="coolwarm",vmin=-100  ,vmax=100  )
ax8.imshow(slopeB.imag     ,cmap="coolwarm",vmin=-100  ,vmax=100  )


fig2 = plt.figure()

ax21 = fig2.add_subplot(1,2,1)
ax22 = fig2.add_subplot(1,2,2)

coherenceZ = coherence(slopeA[1:-1,1:-1],slopeB)

ax21.imshow(np.abs(coherenceZ)  ,cmap="plasma"  ,vmin=0     ,vmax=1)
ax22.imshow(np.angle(coherenceZ),cmap="coolwarm"     ,vmin=-np.pi,vmax=np.pi)
plt.show()