#! /usr/bin/env python3

import json
import logging
import os
import tkinter as tk
from datetime import datetime
from threading import Thread
from tkinter import ttk

import cv2

logging.basicConfig(level=logging.INFO)
path = os.path.dirname(__file__) + os.sep


class Recorder:
    """ Class for viewing and recording video from network camera. """

    def __init__(self, params):
        self.root = tk.Tk()
        self.root.title("Video Recorder GUI")
        self.root.protocol("WM_DELETE_WINDOW", self.exit)

        self.array = {}

        for param in params:
            name = param["NAME"]
            url = param["URL"]

            frame = ttk.LabelFrame(self.root, text=name, labelanchor="n")
            frame.pack(side="left", fill="both", expand=True)

            btn_show = ttk.Button(frame, text="Show Video")
            btn_show.config(command=lambda button=btn_show: self.show(button))
            btn_show.pack(side="top", fill="x", pady=2, padx=2)

            btn_rec = ttk.Button(frame, text="Start Record", state="disabled")
            btn_rec.config(command=lambda button=btn_rec: self.record(button))
            btn_rec.pack(side="top", fill="x", pady=2, padx=2)

            self.array[btn_show] = {"NAME": name, "EXIT": False, "PID": None, "RECORD": False, "TOGGLE": False, "URL": url, "DEPEND": btn_rec}
            self.array[btn_rec]  = {"NAME": name, "EXIT": False, "PID": None, "RECORD": False, "TOGGLE": False, "URL": url, "DEPEND": btn_show}

        self.root.mainloop()

    def show(self, button):
        """ Show or hide video frame. """

        name = self.array[button]["NAME"]

        if self.array[button]["TOGGLE"]:
            logging.info("%s-> Hide video", name)

            button.config(text="Show Video")

            self.array[button]["DEPEND"].config(state="disabled")
            self.array[button]["TOGGLE"] = False
            self.array[button]["EXIT"] = True
            self.array[button]["PID"].join()
            self.array[button]["PID"] = None
        else:
            logging.info("%s-> Show video", name)

            button.config(text="Hide Video")

            self.array[button]["DEPEND"].config(state="normal")
            self.array[button]["TOGGLE"] = True
            self.array[button]["EXIT"] = False
            self.array[button]["PID"] = Thread(target=self.play, args=(button,))
            self.array[button]["PID"].daemon = True
            self.array[button]["PID"].start()

    def record(self, button):
        """ Start or stop recording. """

        name = self.array[button]["NAME"]

        if self.array[button]["RECORD"]:
            logging.info("%s-> Stop recording", name)

            button.config(text="Start Record")

            self.array[button]["DEPEND"].config(state="normal")
            self.array[button]["RECORD"] = False
            tmp = self.array[button]["DEPEND"]
            self.array[tmp]["RECORD"] = False
        else:
            logging.info("%s-> Start recording", name)

            button.config(text="Stop Record")

            self.array[button]["DEPEND"].config(state="disabled")
            self.array[button]["RECORD"] = True
            tmp = self.array[button]["DEPEND"]
            self.array[tmp]["RECORD"] = True

    def play(self, button):
        """ Play video frame. """

        name = self.array[button]["NAME"]

        capture = cv2.VideoCapture(self.array[button]["URL"])

        if capture.isOpened():
            logging.info("%s-> Capture opened successfully", name)

            height = capture.get(cv2.CAP_PROP_FRAME_HEIGHT)
            width = capture.get(cv2.CAP_PROP_FRAME_WIDTH)
            fps = capture.get(cv2.CAP_PROP_FPS)
            fourcc = cv2.VideoWriter_fourcc("M", "J", "P", "G")
            logging.info("%s-> Height=%i Width=%i FPS=%.1f", name, height, width, fps)

            new_file = True

            while capture.isOpened():
                ret, frame = capture.read()
                if ret:
                    cv2.imshow(name, frame)

                    if self.array[button]["RECORD"]:
                        if new_file:
                            filename = datetime.now().strftime(name + " %Y-%m-%d %H-%M-%S" + ".avi")
                            out = cv2.VideoWriter(filename, fourcc, 25, (int(width), int(height)))
                            if out.isOpened():
                                logging.info("%s-> Writer opened successfully", name)
                                new_file = False
                            else:
                                logging.error("%s-> Writer not opened", name)
                        else:
                            out.write(frame)
                    else:
                        new_file = True
                else:
                    logging.error("%s-> Frame not grabbed", name)

                cv2.waitKey(1)

                if self.array[button]["EXIT"]:
                    break
        else:
            logging.error("%s-> Capture not opened", name)

        logging.info("%s-> Release video", name)
        capture.release()
        cv2.destroyWindow(name)

    def exit(self):
        """ Exit GUI. """

        [self.show(key) for key in self.array if self.array[key]["TOGGLE"]]
        self.root.quit()


if __name__ == "__main__":
    with open(f"{path}video-recorder.json", encoding="utf-8") as hfile:
        rec_params = json.load(hfile)
        Recorder(rec_params)
