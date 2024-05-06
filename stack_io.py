from PIL import Image
from PIL.TiffTags import TAGS

import numpy as np
import operator
from functools import reduce
from math import ceil, sqrt, cos, pi, floor
from itertools import product
from scipy.ndimage import sobel,gaussian_filter

import os
import re


def save_stack(arr, name="test.tif", metadata=None,typ=np.int32):
    imlist = []
    arr = arr.astype(typ)
    print(arr.dtype)
    for i in range(arr.shape[-1]):
        imlist.append(Image.fromarray(arr[:, :, i], mode="I"))
    if metadata != None:
        imlist[0].save(
            name,
            compression=None,
            save_all=True,
            append_images=imlist[1:],
            tiffinfo=metadata,
        )
    else:
        imlist[0].save(name, compression=None, save_all=True, append_images=imlist[1:])
    print(f"saving {name} finished")


def show_image(array, height=None, a=None, b=None):
    get_image(array, height, a, b).show()


def get_image(array, height=None, a=None, b=None,color=(0,)):
    if a == None:
        a = array.shape[0]
    if b == None:
        b = array.shape[1]
    arr = np.zeros((a, b, 3))
    for i in color:
        if height != None:
            arr[:, :, i] = array[:a, :b, height] / (np.amax(array) / 255)
        else:
            arr[:, :, i] = array[:a, :b] / (np.amax(array) / 255)
    return Image.fromarray(arr.astype(np.uint8))

def get_image_rgb(array):
    arr = array/max(-np.amin(array),np.amax(array))
    arr=arr*255
    return Image.fromarray(arr.astype(np.uint8))

def show_image_rgb(array):
    get_image_rgb(array).show()



def load_image(file_name):
    # E:\Users\Fingal\Anaconda3
    img = Image.open(file_name)
    # Map PIL mode to numpy dtype (note this may need to be extended)
    return image_to_array(img)


def image_to_array(img: Image) -> np.array:
    dtype = np.uint16
    w, h = img.size
    array = np.zeros((h, w, img.n_frames), dtype=dtype)
    for i in range(img.n_frames):
        img.seek(i)
        array[:, :, i] = np.array(img)
    return array


def get_dimentions(img: Image) -> (float, float, float):
    meta_dict = {TAGS[key]: img.tag.get(key) for key in img.tag.keys()}
    x = meta_dict["XResolution"][0]
    x = x[1] / x[0]

    y = meta_dict["YResolution"][0]
    y = y[1] / y[0]

    z = float(re.findall("spacing=[0-9.]*", meta_dict["ImageDescription"][0])[0][8:])

    return x, y, z


def draw_line(result, starting_point, v, size=5, offset=0):
    for j in np.linspace(0, 1, num=(1 + 2 * ceil(max(np.amax(v), -np.amin(v))))):
        point = v * j + starting_point
        # print(point)
        size = 5
        result[
            ceil(point[0]) - size : ceil(point[0]) + size,
            ceil(point[1]) - size : ceil(point[1]) + size,
            ceil(point[2]) - size : ceil(point[2]) + size,
        ].fill(5000 + offset)


def array_range(array, step_size=1):
    return product(
        range(0, array.shape[0], step_size),
        range(0, array.shape[1], step_size),
        range(0, array.shape[2], step_size),
    )


def to_image(array, dir):
    if not os.path.exists(dir):
        os.makedirs(dir)
    array = array.astype(np.uint16)
    for i in range(array.shape[-1]):
        im = Image.fromarray(
            (array[:, :, i] / (np.amax(array) / 300)).astype(int)
        ).convert("RGB")
        im.save(f"{dir}\\out{i}.jpg")


# def get_heightmap(array: np.array) -> np.array:
#     result = np.zeros(array.shape[:2])
#     edges = np.abs(sobel(array))
#     over8000 = (zip(*map(reversed,np.where(edges>8000))))
#     for x,y,z in over8000:
#         if result[x,y]>z:
#             continue
#         result[x,y]=z
#     over7000 = (zip(*map(reversed,np.where(np.logical_and(edges<8000, edges>7000)))))
#     for x,y,z in over7000:
#         if result[x,y]>z:
#             continue
#         result[x,y]=z
#     for x,y in zip(*np.where(result==0)):
#         value = 0
#         for z in reversed(range(edges.shape[2])):
#             if edges[x,y,z]>value:
#                 value=edges[x,y,z]
#                 result[x,y]=z
#     return result


def get_heightmap(array: np.array) -> np.array:
    result = np.zeros(array.shape[:2])
    edges = np.abs(sobel(array))
    over8000 = zip(*map(reversed, np.where(edges > 8000)))
    for x, y, z in over8000:
        if result[x, y] > z:
            continue
        result[x, y] = z
    for x, y in zip(*np.where(result == 0)):
        value = 0
        for z in reversed(range(edges.shape[2])):
            if edges[x, y, z] > value:
                value = edges[x, y, z]
                result[x, y] = z
    return result


def normalize(x):
    if np.linalg.norm(x)<0.00001:
        return x
    return x/np.linalg.norm(x)

def calculate_normals(heightmap: np.array, r=3) -> np.array:
    result = np.zeros((*heightmap.shape,3))
    #heightmap=gaussian_filter(heightmap,2)
    N,M=heightmap.shape
    for a,b in product(range(-r+1,r),range(-r+1,r)): 
        if a==0 and b==0:
            continue
        if a!=0:
            result[r:-r,r:-r,0]+=(heightmap[r:-r,r:-r]-heightmap[r+a:-r+a,r+a:-r+a])*a/((a**2+b**2)**0.5)
        if b!=0:
            result[r:-r,r:-r,2]+=(heightmap[r:-r,r:-r]-heightmap[r+b:-r+b,r+b:-r+b])*b/((a**2+b**2)**0.5)

        result[r:-r,r:-r,1]=result[r:-r,r:-r,1]+1

    norms = np.zeros((*heightmap.shape,1))
    norms[:,:,0]=(result[:,:,0]**2+result[:,:,1]**2+result[:,:,2]**2)**0.5
    norms[norms<0.00001]=1
    result = result/norms
    return result
    # for i in range(r,N-r):
    #     for j in range(r,M-r):
    #         base_height=heightmap[i,j]
    #         normal=np.array([0,0,0])
    #         for a,b in product(range(-r,r+1),range(-r,r+1)):
    #             if a ==0 and b==0:
    #                 continue
    #             this_height=heightmap[i+a,j+b]
    #             normal=normal+normalize(np.array([0,1,0])+np.array([a,0,b])*(base_height-this_height))
    #         normal=normal/np.linalg.norm(normal)
    #         result[i,j,:]=normal

def range_calculate_normals(heightmap: np.array, r=2) -> np.array:
    result = np.zeros((*heightmap.shape,3))
    N,M=heightmap.shape
    for i in range(N):
        for j in range(M):
            base_height=heightmap[i,j]
            for a in range(-r,r+1):
                for b in range(-r,r+1):
                    if a-i<0 or b-j<0 or a+i>=heightmap.shape[0] or b+j>=heightmap.shape[1]:
                        print('out of bounds')
                        continue
                    if a ==0 and b==0:
                        print('zero')
                        continue
                    normal = np.array([0,1,0])
                    dir = np.array([a,0,b])
                    this_height=heightmap[i+a,b+j]
                    d=np.array([0,0,0])
                    print('h div',base_height-this_height)
                    if (base_height-this_height)!=0:
                        d=(dir*(base_height-this_height))
                        d=d/(np.linalg.norm(d)**2)
                    if d[0]==np.nan:
                        d=np.array([0,0,0])
                        

                    print(np.linalg.norm(normal+d))
                    print(normal+d)
                    result[i,j,:]=result[i,j,:]+(normal+d)/np.linalg.norm(normal+d)
                    
            if (np.linalg.norm(result[i,j,:])>0):
                result[i,j,:]=result[i,j,:]/np.linalg.norm(result[i,j,:])
            else:
                result[i,j,:]=np.array([0,1,0])
    
    return result

