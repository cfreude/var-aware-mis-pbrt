
# this script loads all .exr files generated by the test scripts and:
#  - converts them to png
#  - stores specified insets (depending on the scene) as png files

import os
from glob import glob
import pyexr
import numpy as np
import scipy.misc

def lin_to_srgb(rgba):
    """
    Linear to sRGB conversion of n-d numpy array:
    rgb<=0.0031308?rgb*12.92:(1.055*(rgb**(1.0/2.4)))-0.055
    """
    return np.clip(np.where(
        np.less_equal(rgba, 0.0031308),
        np.multiply(rgba,  12.92),
        np.subtract(np.multiply(1.055, np.power(rgba, 1.0 / 2.4)), 0.055)), 0.0, 1.0)

# find all .exr files
filenames = []
start_dir = os.getcwd()
pattern   = "*.exr"
for dir,_,_ in os.walk(start_dir):
    filenames.extend(glob(os.path.join(dir,pattern)))

# remove the stratification factor files form the list
factorImages = []
for name in filenames:
    if 'stratfactor-d' in name:
        factorImages.append(name)
for name in factorImages:
    filenames.remove(name)

# separate the reference images for error computation
refGlobal = {}
refDirect = {}
for name in filenames:
    if 'ref-bdpt' in name:
        buffer = refGlobal
    elif 'ref-di' in name:
        buffer = refDirect
    else:
        continue

    if 'bathroom' in name:
        buffer['bathroom'] = pyexr.read(name)
    if 'breakfast' in name:
        buffer['breakfast'] = pyexr.read(name)
    if 'veach-mis' in name:
        buffer['veach-mis'] = pyexr.read(name)
    if 'livingroom' in name:
        buffer['livingroom'] = pyexr.read(name)
    if 'staircase1' in name:
        buffer['staircase1'] = pyexr.read(name)

def relativeError(img, ref):
    return np.sum((img - ref)**2 / (ref + 0.0001)) / (ref.shape[0] * ref.shape[1])

def getReference(name):
    if 'direct-only' in name or 'defsampling' in name or 'optimalmis' in name or 'ref-di' in name:
        buffer = refDirect
    else:
        buffer = refGlobal

    if 'bathroom' in name:
        return buffer['bathroom']
    if 'breakfast' in name:
        return buffer['breakfast']
    if 'veach-mis' in name:
        return buffer['veach-mis']
    if 'livingroom' in name:
        return buffer['livingroom']
    if 'staircase1' in name:
        return buffer['staircase1']

# convert each file to png
for f in filenames:
    img = pyexr.read(f)
    fnamePng = f.replace('.exr', '.png')

    exposure = 0.0
    if 'bathroom' in f:
        exposure = 0.0
    elif 'livingroom' in f:
        exposure = 1.0
    elif 'staircase1' in f:
        exposure = 2.0

    tmapped = lin_to_srgb(img * pow(2, exposure))
    scipy.misc.toimage(tmapped, cmin=0.0, cmax=1.0).save(fnamePng)

    # compute error across whole image
    myRef = getReference(f)
    errorFull = relativeError(img, myRef)

    # generate the insets for each file
    left = 0
    top = 0
    w = 50
    h = 50

    # first inset
    if 'bathroom' in f:
        left = 570
        top = 130
        w = 100
        h = 100
        exposure = -1.0
    elif 'breakfast' in f:
        left = 470
        top = 430
        w = 100
        h = 100
    elif 'livingroom' in f:
        left = 360
        top = 0
        h = 100
        w = 100
    elif 'veach-mis' in f:
        left = 560
        top = 170
        w = 100
        h = 100
    elif 'staircase1' in f:
        left = 280
        top = 100
        w = 100
        h = 100
        exposure = 1.0

    fnameInset1 = fnamePng.replace('.png', '-inset1.png')

    tmapped = lin_to_srgb(img[top:top+h,left:left+w,:] * pow(2, exposure))
    scipy.misc.toimage(tmapped, cmin=0.0, cmax=1.0).save(fnameInset1)

    errorInset1 = relativeError(img[top:top+h,left:left+w,:], myRef[top:top+h,left:left+w,:])

    # second inset
    if 'bathroom' in f:
        left = 260
        top = 520
        w = 100
        h = 100
        exposure = 0.0
    elif 'breakfast' in f:
        left = 880
        top = 500
        w = 100
        h = 100
    elif 'livingroom' in f:
        left = 920
        top = 40
        h = 100
        w = 100
    elif 'veach-mis' in f:
        left = 600
        top = 280
        w = 100
        h = 100
        exposure = -5.5
    elif 'staircase1' in f:
        left = 210
        top = 1150
        w = 100
        h = 100
        exposure = 2.0

    fnameInset2 = fnamePng.replace('.png', '-inset2.png')

    tmapped = lin_to_srgb(img[top:top+h,left:left+w,:] * pow(2, exposure))
    scipy.misc.toimage(tmapped, cmin=0.0, cmax=1.0).save(fnameInset2)

    errorInset2 = relativeError(img[top:top+h,left:left+w,:], myRef[top:top+h,left:left+w,:])

    import math
    roundToN = lambda x, n: 0 if x==0.0 else round(x, -int(math.floor(math.log10(x))) + (n-1))

    errValuesFile = fnamePng.replace('.png', '-error.txt')
    with open(errValuesFile, 'w') as errFile:
        errFile.write('relative errors (i - r)^2 / (r^2): \n')
        errFile.write('full image: ' + str(roundToN(errorFull, 3)) + ' \n')
        errFile.write('first inset: ' + str(roundToN(errorInset1, 3)) + ' \n')
        errFile.write('second inset: ' + str(roundToN(errorInset2, 3)) + ' \n')