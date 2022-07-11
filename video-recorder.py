#! /usr/bin/env python
# -*- coding: utf-8 -*-

import logging
import threading
import cv2
import json
import datetime

try:
    import tkinter as Tkinter       # for Python3
    from tkinter import ttk
except:
    import Tkinter                  # for Python2
    import ttk


logging.basicConfig(level=logging.INFO)


class Recoder(object):
    def __init__(self, params):
        self.root = Tkinter.Tk()
        self.root.title("Video Recoder GUI")
        self.root.protocol('WM_DELETE_WINDOW', self.exit)

        self.array = {}

        for param in params:
            name = param["NAME"]
            url = param["URL"]

            frame = ttk.LabelFrame(self.root, text=name, labelanchor='n')
            frame.pack(side="left", fill="both", expand=True)

            buttonShow = ttk.Button(frame, text="Show Video")
            buttonShow.pack(side="top", fill="x", pady=2, padx=2)

            buttonRec = ttk.Button(frame, text="Start Record", state="disabled")
            buttonRec.pack(side="top", fill="x", pady=2, padx=2)

            self.array[buttonShow] = {'NAME': name, 'EXIT': False, 'PID': None, 'RECORD': False, 'TOGGLE': False, 'URL': url, 'DEPEND': buttonRec}
            self.array[buttonRec]  = {'NAME': name, 'EXIT': False, 'PID': None, 'RECORD': False, 'TOGGLE': False, 'URL': url, 'DEPEND': buttonShow}

            buttonShow.config(command=lambda button=buttonShow: self.show(button))
            buttonRec.config(command=lambda button=buttonRec: self.record(button))

        self.root.mainloop()

    def show(self, button):
        if self.array[button]['TOGGLE']:
            logging.info(self.array[button]['NAME'] + "-> Hide video")

            button.config(text="Show Video")

            self.array[button]['DEPEND'].config(state="disabled")
            self.array[button]['TOGGLE'] = False
            self.array[button]['EXIT'] = True
            self.array[button]['PID'].join()
            self.array[button]['PID'] = None
        else:
            logging.info(self.array[button]['NAME'] + "-> Show video")

            button.config(text="Hide Video")

            self.array[button]['DEPEND'].config(state="normal")
            self.array[button]['TOGGLE'] = True
            self.array[button]['EXIT'] = False
            self.array[button]['PID'] = threading.Thread(target=self.play, args=(button,))
            self.array[button]['PID'].daemon = True
            self.array[button]['PID'].start()

    def record(self, button):
        if self.array[button]['RECORD']:
            logging.info(self.array[button]['NAME'] + "-> Stop recording")

            button.config(text="Start Record")

            self.array[button]['DEPEND'].config(state="normal")
            self.array[button]['RECORD'] = False
            tmp = self.array[button]['DEPEND']
            self.array[tmp]['RECORD'] = False
        else:
            logging.info(self.array[button]['NAME'] + "-> Start recording")

            button.config(text="Stop Record")

            self.array[button]['DEPEND'].config(state="disabled")
            self.array[button]['RECORD'] = True
            tmp = self.array[button]['DEPEND']
            self.array[tmp]['RECORD'] = True

    def play(self, button):
        name = self.array[button]['NAME']

        capture = cv2.VideoCapture(self.array[button]['URL'])

        if capture.isOpened():
            logging.info("%s-> Capture opened successfully" % (name))

            if int(cv2.__version__[0]) > 2:
                height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
                width  = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
                fps    = capture.get(cv2.CAP_PROP_FPS)
                fourcc = cv2.VideoWriter_fourcc('M','J','P','G')
            else:
                height = capture.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
                width  = capture.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
                fps    = capture.get(cv2.cv.CV_CAP_PROP_FPS)
                fourcc = cv2.cv.CV_FOURCC('M','J','P','G')
            logging.info("%s-> Height=%i Width=%i FPS=%.1f" % (name, height, width, fps))

            new_file = True

            while(capture.isOpened()):
                ret, frame = capture.read()
                if ret:
                    cv2.imshow(name, frame)

                    if self.array[button]['RECORD']:
                        if new_file:
                            filename = datetime.datetime.strftime(datetime.datetime.now(), name + " %Y-%m-%d %H-%M-%S") + ".avi"
                            out = cv2.VideoWriter(filename, fourcc, 25, (int(width), int(height)))
                            if out.isOpened():
                                logging.info(name + "-> Writer opened successfully")
                                new_file = False
                            else:
                                logging.error(name + "-> Writer not opened")
                        else:
                            out.write(frame)
                    else:
                        new_file = True
                else:
                    logging.error(name + "-> Frame not grabbed")

                cv2.waitKey(1)

                if self.array[button]['EXIT']:
                    break
        else:
            logging.error(name + "-> Capture not opened")

        logging.info(name + "-> Release video")
        capture.release()
        cv2.destroyWindow(name)

    def exit(self):
        [self.show(key) for key in self.array.keys() if self.array[key]['TOGGLE']]
        self.root.quit()


if __name__ == '__main__':
    rec_params = json.load(open('video-recorder.json'))
    Recoder(rec_params)
