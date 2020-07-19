import os
import sys
import json
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *

__all__ = ['combine_subframes', 'AnimationViewer']

action_names = {
    0: "闲置",
    1: "移动",
    2: "攻击",
    3: "受伤",
    4: "死亡",
    5: "动作1",
    6: "动作2",
    7: "动作3",
    8: "动作4",
    9: "动作5",
}

dir_names = ["左下", "右下", "左上", "右上"]


# tools help to combine subframes
def get_subimage(texture, rect):
    img = texture.crop((rect[0], rect[1], rect[0] + rect[2], rect[1] + rect[3]))
    width, height = img.size
    pixdata = img.load()
    trans_pixel = pixdata[0, 0]

    for y in range(height):
        for x in range(width):
            if pixdata[x, y] == trans_pixel:
                pixdata[x, y] = (255, 255, 255, 0)
    return img


def alpha_scale(img, alpha):
    new_img = img.copy()
    data = list(img.getdata())
    for x in range(len(data)):
        data[x] = (*data[x][:3], int(data[x][3]*alpha))
    new_img.putdata(data)
    return new_img


def combine_subframes(image, acts, scale=1.0):
    raw_frames = [get_subimage(image, rect) for rect in acts['frame_rects']]
    combined = {}
    # loop over actions
    for actval, anims in acts['animations'].items():
        action = []
        # loop over directions (face, back)
        for anim in anims:
            frames = []
            keys = ['image_n', 'offset_x', 'offset_y', 'rotation', 'scale_x', 'scale_y', 'opacity', 'direction']
            for i in range(len(anim['image_n'])):
                vals = np.array([anim[key][i] for key in keys]).T
                # # loop over subframes and find a proper pic size
                # max_x, max_y = 0, 0
                # for (idx, offx, offy, rot, scx, scy, op, mir) in vals:
                #     ifr = int(idx)
                #     size = np.array([raw_frames[ifr].width, raw_frames[ifr].height])
                #     offset = np.abs([offx, offy])*2.0
                #     max_x = max(max_x, (size + offset)[0]*scx)
                #     max_y = max(max_y, (size + offset)[1]*scy)
                # pic_size = (np.array([max_x, max_y])*scale + np.array([1, 1])).astype(int)
                pic_size = (1000, 1000)
                frame = Image.new('RGBA', tuple(pic_size), (255, 255, 255, 0))
                center = np.array(pic_size)/2
                # loop over subframes and stack them
                for (idx, offx, offy, rot, scx, scy, op, mir) in vals:
                    ifr = int(idx)
                    size = np.array([scx*raw_frames[ifr].width, scy*raw_frames[ifr].height])*scale
                    offset = np.array([offx*scx, offy*scy])*scale
                    subf = raw_frames[ifr].resize(size=tuple(size.astype(int)))
                    if mir:
                        subf = subf.transpose(Image.FLIP_LEFT_RIGHT)
                        rot = -rot
                    pos = center - offset - size/2.
                    frame.alpha_composite(alpha_scale(subf, op/255).rotate(rot), tuple(pos.astype(int)))
                # finish one frame
                frames.append(frame)
            # finish one direction for one action
            action.append({'frames': frames, 'speed': anim['speed']})
        # finish one action
        combined[actval] = action
    return combined


# animated Qlabel
class AnimeLabel(QLabel):
    # interval is in ms
    def __init__(self, frames, speed, flip=False, size=(200, 200), interval=10):
        super(AnimeLabel, self).__init__()

        # basic attributes
        self.flip = flip
        self.speed = speed
        self.frameSize = np.asarray(size)
        self.frames = frames
        self.iframe = 0

        # define timer to refresh
        self.qTimer = QTimer()
        self.qTimer.setInterval(interval)
        # connect timeout signal to signal handler
        self.qTimer.timeout.connect(self.update_frame)
        # start timer
        self.timer = 0
        # initial image
        self.set_frame(0)

    def update_frame(self):
        self.timer += self.qTimer.interval()
        # speed unit is 40 ms
        if self.timer >= self.speed*40:
            self.timer = 0
            self.iframe = (self.iframe + 1) % len(self.frames)
            self.set_frame(self.iframe)

    def set_frame(self, i):
        frame = self.frames[i]
        # crop it
        center = np.array([frame.width, frame.height])/2.
        crop_rect = tuple(np.concatenate([center - self.frameSize/2., center + self.frameSize/2.]).astype(int))
        frame_img = frame.crop(crop_rect)
        if self.flip:
            frame_img = frame_img.transpose(Image.FLIP_LEFT_RIGHT)
        self.setPixmap(QPixmap.fromImage(ImageQt(frame_img)))

    def play(self):
        self.qTimer.start()

    def stop(self):
        self.qTimer.stop()


class AnimationViewer(QWidget):
    def __init__(self, texture, action_json, label_size=(200, 200), scale=1.0):
        super(AnimationViewer, self).__init__()
        animations = combine_subframes(texture, action_json, scale)
        self.labels = []
        hbox = QHBoxLayout()
        vbox = QVBoxLayout()
        # direction name labels
        for dir_name in dir_names:
            # text label
            label = QLabel(self)
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            label.setText(dir_name)
            label.setFont(QFont('Times', 24))
            label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
            vbox.addWidget(label)
        awidget = QWidget(self)
        awidget.setLayout(vbox)
        hbox.addWidget(awidget)

        for key, actions in animations.items():
            vbox = QVBoxLayout()
            # text label for action name
            label = QLabel(self)
            label.setFrameStyle(QFrame.Panel | QFrame.Sunken)
            label.setText(action_names[int(key)])
            label.setFont(QFont('Times', 24))
            label.setAlignment(Qt.AlignCenter | Qt.AlignCenter)
            vbox.addWidget(label)
            # four direction animations
            dir1 = AnimeLabel(actions[0]['frames'], actions[0]['speed'], False, label_size)
            dir2 = AnimeLabel(actions[0]['frames'], actions[0]['speed'], True, label_size)
            dir3 = AnimeLabel(actions[1]['frames'], actions[1]['speed'], True, label_size)
            dir4 = AnimeLabel(actions[1]['frames'], actions[1]['speed'], False, label_size)
            for dir in [dir1, dir2, dir3, dir4]:
                self.labels.append(dir)
                vbox.addWidget(dir)
            awidget = QWidget(self)
            awidget.setLayout(vbox)
            hbox.addWidget(awidget)
        self.setLayout(hbox)

    def play(self):
        for label in self.labels:
            label.play()

    def stop(self):
        for label in self.labels:
            label.stop()


if __name__ == '__main__':
    data_dir = r'E:\GameProjects\wx_td2\assets\resources\sprites'
    name = 'poring'
    image = Image.open(os.path.join(data_dir, '{}.png'.format(name))).convert("RGBA")
    f = open(os.path.join(data_dir, '{}.json'.format(name)))
    acts = json.load(f)

    app = QApplication(sys.argv)
    w = AnimationViewer(image, acts, (200, 200), 2.0)
    w.play()
    w.show()
    sys.exit(app.exec_())
