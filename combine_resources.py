import sys
import os
import enum
import json
import numpy as np
from PIL import Image
from PyQt5.QtWidgets import QApplication

sys.path.append(r'E:\GameProjects\sprites_tools\pyro_tools')
from qtgui import AnimationViewer


# enum defined in code
class Action(enum.Enum):
    Idle = 0
    Move = 1
    Attack = 2
    Damage = 3
    Dead = 4
    Action1 = 5
    Action2 = 6
    Action3 = 7
    Action4 = 8
    Action5 = 9


def auto_split(n):
    test = int(np.sqrt(n))
    if np.square(test) >= n:
        return test, test
    elif (test + 1)*test >= n:
        return test + 1, test
    else:
        return test + 1, test + 1


data_path = r'E:\GameProjects\sprite_test\data\{name}.png'
png_path = r'E:\GameProjects\sprite_test\{name}.png'
json_path = r'E:\GameProjects\sprite_test\{name}.json'

sprite_name = 'my_wolf'


# define actions, each set of actions have two elements (front, back)
# REQUIRED: images, actions[image_n, speed]
# OPTIONAL: rotation, direction, offset_x, offset_y, scale_x, scale_y in actions
optional = {'rotation': [0], 'direction': [0], 'offset_x': [0], 'offset_y': [0],
            'scale_x': [1], 'scale_y': [1], 'opacity': [255]}
my_sprite = {
    "images": ['wolf-1', 'wolf-2', 'wolf-3', 'wolf-35', 'wolf-37'],
    "actions": {
        Action.Move.value: [
            # front
            dict(speed=3.0, image_n=[[0], [1], [2]]),
            # back
            dict(speed=3.0, image_n=[[0], [1], [2]]),
        ],
        Action.Damage.value: [
            dict(speed=4.0, image_n=[[3], [3], [3], [3], [3]], rotation=[[-280], [-300], [-320], [-340], [-360]]),
            dict(speed=4.0, image_n=[[3], [3], [3], [3], [3]], rotation=[[-280], [-300], [-320], [-340], [-360]]),
        ],
        Action.Dead.value: [
            dict(speed=4.0, image_n=[[3], [3], [3], [3], [4], [4], [4]],
                 rotation=[[-300], [-320], [-340], [-360], [0], [0], [0]]),
            dict(speed=4.0, image_n=[[3], [3], [3], [3], [4], [4], [4]],
                 rotation=[[-300], [-320], [-340], [-360], [0], [0], [0]]),
        ]
    },
}

# merge images
images = [Image.open(data_path.format(name=imfile)) for imfile in my_sprite['images']]
ncols, nrows = auto_split(len(images))
width, height = np.max([f.width for f in images]) + 1, np.max([f.height for f in images]) + 1

full_img = Image.new('RGBA', (width*ncols, height*nrows))
frame_rects = []

for i, im in enumerate(images):
    u, v = (i % ncols), (i // ncols)
    full_img.paste(im, (u*width, v*height))
    frame_rects.append([int(u*width), int(v*height), int(im.width), int(im.height)])

full_img.save(png_path.format(name=sprite_name), 'PNG')

# animation actions
# fill missing items
anims = my_sprite['actions']
for key, item in anims.items():
    for anim in anims[key]:
        length = [len(imn) for imn in anim['image_n']]
        fill = {key: [item * sublen for sublen in length] for key, item in optional.items() if key not in anim}
        anim.update(fill)

json_attrs = {
    'max_frames': len(images),
    'frame_rects': frame_rects,
    'animations': anims
}

# dump all the information to json

with open(json_path.format(name=sprite_name), 'w') as f:
    json.dump(json_attrs, f, indent=2)


# ==== you can also show existing animations ====
data_dir = r'E:\GameProjects\wx_td2\assets\resources\sprites'
name = 'poring'
f = open(os.path.join(data_dir, '{}.json'.format(name)))
# full_img = Image.open(os.path.join(data_dir, '{}.png'.format(name))).convert("RGBA")
# json_attrs = json.load(f)

# ==== show the built animations ====
app = QApplication(sys.argv)
w = AnimationViewer(full_img, json_attrs, (200, 200))
w.play()
w.show()
sys.exit(app.exec_())
