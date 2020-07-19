import sys
import json
import enum
import numpy as np
from os import listdir
from os.path import isfile, join, exists
from PIL import Image
sys.path.append(r'E:\GameProjects\pyro-tools')
from pyro_tools import spr_open
from pyro_tools import act_open


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


data_dir = r'E:\GameProjects\RO_data\sprites'

# enemies
# names = ['poring', 'lunatic', 'wolf', 'mantis', 'majoruros', 'marduk', 'owl_duke', 'randgris']
# required_actions = [Action.Move.value, Action.Damage.value, Action.Dead.value]
# out_dir = r'E:\GameProjects\wx_td2\assets\resources\sprites'

# towers
names = ['goblin_archer', 'orc_archer', 'raydric_archer', 'faceworm', 'boitata', 'detale']
required_actions = [Action.Idle.value, Action.Attack.value]
out_dir = r'E:\GameProjects\wx_td2\assets\resources\sprites'

# all sprites in the directory
# names = list(set(['.'.join(f.split('.')[:-1]) for f in listdir(data_dir) if isfile(join(data_dir, f))]))
# required_actions = np.arange(0, 10).tolist()
# out_dir = r'E:\GameProjects\RO_data'

# test
# names = ['poring']
# required_actions = np.arange(0, 10).tolist()
# out_dir = r'E:\GameProjects\sprite_test'


spr_file = join(data_dir, '{name}.spr')
act_file = join(data_dir, '{name}.act')
png_path = join(out_dir, '{name}.png')
json_path = join(out_dir, '{name}.json')


def auto_split(n):
    test = int(np.sqrt(n))
    if np.square(test) >= n:
        return test, test
    elif (test + 1)*test >= n:
        return test + 1, test
    else:
        return test + 1, test + 1


def extract_spr(sprin, actin, sprout, actout, actions):
    # load input files
    frames = spr_open(sprin)
    actor = act_open(actin)

    # ==== process animation information ====
    anims = []
    for i, animation in enumerate(actor.animations):
        if i % 4 > 0:
            continue
        attr = {
            'image_n': [], 'rotation': [], 'direction': [], 'offset_x': [],
            'offset_y': [], 'scale_x': [], 'scale_y': [],
        }
        for subframes in animation.frames:
            for key, vals in attr.items():
                # vals += [f.__getattribute__(key) for f in subframes]
                vals.append([f.__getattribute__(key) for f in subframes])
        attr['speed'] = animation.speed
        attr['opacity'] = [[f.__getattribute__('color')[3] for f in subframes] for subframes in animation.frames]
        anims.append(attr)

    # used animations
    anims = np.array(anims).reshape((len(anims)//2, 2))
    valid_acts = [act for act in actions if act < len(anims)]
    anims = anims[valid_acts]
    used_frames = np.unique([f for anim in anims.flat for fs in anim['image_n'] for f in fs]).tolist()

    # mapping the frames, use compressed indices
    fdict = {f: list.index(used_frames, f) for f in used_frames}

    # translate image_n to the new indices
    for anim in anims.flat:
        anim['image_n'] = [[fdict[f] for f in fs] for fs in anim['image_n']]

    # ==== merge all used frames ====
    uframes = np.array(frames)[used_frames]
    ncols, nrows = auto_split(len(uframes))
    width, height = np.max([f.width for f in uframes]) + 1, np.max([f.height for f in uframes]) + 1

    full_img = Image.new('RGBA', (width*ncols, height*nrows))
    frame_rects = []

    for i, frame in enumerate(uframes):
        frames.fill_rgba(frame)
        im = Image.frombytes('RGBA', (frame.width, frame.height), b''.join(frame.data))
        u, v = (i % ncols), (i // ncols)
        full_img.paste(im, (u*width, v*height))
        frame_rects.append([int(u*width), int(v*height), int(frame.width), int(frame.height)])

    # ==== save texture ====
    full_img.save(sprout)

    json_attrs = {
        'max_frames': len(uframes),
        'frame_rects': frame_rects,
        'sounds': actor.sounds,
        'animations': {valid_acts[i]: anims[i].tolist() for i in np.arange(len(valid_acts))}
    }

    # dump all the information to json
    with open(actout, 'w') as f:
         json.dump(json_attrs, f)


for name in names:
    if not (exists(spr_file.format(name=name)) and exists(act_file.format(name=name))):
        continue
    # extract_spr(spr_file.format(name=name), act_file.format(name=name),
    #             png_path.format(name=name), json_path.format(name=name), required_actions)
    try:
        extract_spr(spr_file.format(name=name), act_file.format(name=name),
                    png_path.format(name=name), json_path.format(name=name), required_actions)
    except:
        print("Unexpected error for {}: {}".format(name, sys.exc_info()[0]))
