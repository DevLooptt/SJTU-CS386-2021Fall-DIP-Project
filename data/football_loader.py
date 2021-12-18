from __future__ import division
import json
import numpy as np
import scipy.misc
import imageio
from PIL import Image
from path import Path
from tqdm import tqdm


class football_loader(object):
    def __init__(self,
                 dataset_dir,
                 split='train',
                 crop_bottom=False,  # We don't need to get rid of the car logo
                 img_height=171,
                 img_width=416):
        self.dataset_dir = Path(dataset_dir)
        self.split = split
        # Crop out the bottom 25% of the image to remove the car logo
        self.crop_bottom = crop_bottom
        self.img_height = img_height
        self.img_width = img_width
        self.min_speed = 2
        self.scenes = (self.dataset_dir/split).dirs() # split='train',scenes是数据差别较大文件夹(比如不同足球比赛?)
        print('Total scenes collected: {}'.format(len(self.scenes)))

    def collect_scenes(self, city):
        img_files = sorted(city.files('*.png')) #按照图片名称排序
        scenes = {}
        connex_scenes = {}
        connex_scene_data_list = []
        for f in img_files:
            scene_id,frame_id = f.basename().split('_')[1:3] #f.basename的格式为city_sceneid_frameid_.png
            if scene_id not in scenes.keys():
                scenes[scene_id] = []
            scenes[scene_id].append(frame_id)

        # 我们不需要分割成连续的帧，只要将数据命名为连续的帧即可
        # divide scenes into connex sequences 分割成连续的帧
        for scene_id in scenes.keys():
            previous = None
            connex_scenes[scene_id] = []
            for id in scenes[scene_id]:
                if previous is None or int(id) - int(previous) > 1:
                    current_list = []
                    connex_scenes[scene_id].append(current_list)
                current_list.append(id)
                previous = id

        # create scene data dicts, and subsample scene every two frames 分割成奇数帧和偶数帧
        for scene_id in connex_scenes.keys():
            intrinsics = self.load_intrinsics(city, scene_id)
            for subscene in connex_scenes[scene_id]:
                # frame_speeds = [self.load_speed(city, scene_id, frame_id) for frame_id in subscene]
                connex_scene_data_list.append({'city':city,
                                               'scene_id': scene_id,
                                               'rel_path': city.basename()+'_'+scene_id+'_'+subscene[0]+'_0', # 数据要dump到的目标地址
                                               'intrinsics': intrinsics,
                                               'frame_ids':subscene[0::2] # 从0开始间隔2取样
                                               #'speeds':frame_speeds[0::2]
                                               })
                connex_scene_data_list.append({'city':city,
                                               'scene_id': scene_id,
                                               'rel_path': city.basename()+'_'+scene_id+'_'+subscene[0]+'_1',
                                               'intrinsics': intrinsics,
                                               'frame_ids': subscene[1::2] # 从1开始间隔2取样
                                               #'speeds': frame_speeds[1::2]
                                               })
        return connex_scene_data_list

#足球比赛数据集无法获得摄像机移动的json数据，因此以下函数返回0矩阵
    def load_intrinsics(self, city, scene_id):
        # city_name = city.basename()
        # camera_folder = self.dataset_dir/'camera'/self.split/city_name
        # camera_file = camera_folder.files('{}_{}_*_camera.json'.format(city_name, scene_id))[0]
        # frame_id = camera_file.split('_')[2]
        # frame_path = city/'{}_{}_{}_leftImg8bit.png'.format(city_name, scene_id, frame_id)

        # with open(camera_file, 'r') as f:
        #     camera = json.load(f)
        # fx = camera['intrinsic']['fx']
        # fy = camera['intrinsic']['fy']
        # u0 = camera['intrinsic']['u0']
        # v0 = camera['intrinsic']['v0']
        # intrinsics = np.array([[fx, 0, u0],
        #                        [0, fy, v0],
        #                        [0,  0,  1]])

        # img = imageio.imread(frame_path)
        # #版本问题被弃用 img = scipy.misc.imread(frame_path) 
        # h,w,_ = img.shape
        # zoom_y = self.img_height/h
        # zoom_x = self.img_width/w

        # intrinsics[0] *= zoom_x
        # intrinsics[1] *= zoom_y

        intrinsics = np.array([[0, 0, 0],
                               [0, 0, 0],
                               [0, 0, 1]])
        return intrinsics

    # def load_speed(self, city, scene_id, frame_id):
    #     city_name = city.basename()
    #     vehicle_folder = self.dataset_dir/'vehicle_sequence'/self.split/city_name
    #     vehicle_file = vehicle_folder/'{}_{}_{}_vehicle.json'.format(city_name, scene_id, frame_id)
    #     with open(vehicle_file, 'r') as f:
    #         vehicle = json.load(f)
    #     return vehicle['speed']

    def get_scene_imgs(self, scene_data):
        cum_speed = np.zeros(3)
        print(scene_data['city'].basename(), scene_data['scene_id'], scene_data['frame_ids'][0])
        for i,frame_id in enumerate(scene_data['frame_ids']):
            # cum_speed += scene_data['speeds'][i]
            speed_mag = np.linalg.norm(cum_speed) # 求范数(=0)
            #if speed_mag > self.min_speed: #TODO 这里将min_speed改为0，可能会出现bug
            yield self.load_image(scene_data['city'], scene_data['scene_id'], frame_id), frame_id
            cum_speed *= 0

    def load_image(self, city, scene_id, frame_id):
        img_file = city/'{}_{}_{}_.png'.format(city.basename(),
                                                          scene_id,
                                                          frame_id)
        if not img_file.isfile():
            return None

        # 版本问题被弃用
        # img = scipy.misc.imread(img_file)
        img = imageio.imread(imgfile)
        # img = scipy.misc.imresize(img, (self.img_height, self.img_width))[:int(self.img_height*0.75)]
        img = np.array(Image.fromarray(img).resize((self.img_height,self.img_width)))[:int(self.img_height*0.75)]
        return img
