from PIL import ImageGrab
from pytesseract import pytesseract, image_to_string
from re import sub
from tkinter import *
from pathlib import Path
from threading import Thread
from random import random, randint, choice
from time import sleep
from string import ascii_letters
from pynput.keyboard import Key, Controller

pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'

class PromptGrabber:
    def __init__(self,
        bbox_1=(770, 690, 850, 710),
        bbox_2=(770, 375, 850, 415)
    ):
        self.bbox_1 = bbox_1
        self.bbox_2 = bbox_2
    
    def grab(self):
        grab_from_bbox = lambda bbox: image_to_string(ImageGrab.grab(bbox=bbox)
            .convert("L").point(lambda x: 0 if x < 32 else 255), config="--psm 6 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        result = sub(r"\W+", "", grab_from_bbox(self.bbox_1) +\
            grab_from_bbox(self.bbox_2)).upper()
        return result.replace("1", "I") if len(result) > 1 else None

class PromptSearcher:
    def __init__(self,
        words=Path("dictionary.txt")
            .read_text()
            .splitlines()
    ):
        words.sort(key=len, reverse=True)
        self.words = words
    
    def matches(self, prompt):
        return [*filter(lambda word: prompt in word, self.words)]

class Typer:
    def __init__(self):
        self.ctrl = Controller()

    def event_speed(self):
        return [("c", max(0.06, random()/5))]
    
    def event_stoppage(self):
        return [("p", max(0.2, random()/5))]

    def event_mistake(self):
        rand = randint(1, 3)
        return [("t", choice(ascii_letters)) for _ in range(rand)]+\
            [("t", Key.backspace)]*rand + self.event_stoppage()
    
    def do_typing(self, word):
        coms = [("t", c) for c in word]
        coms[0:0] = self.event_speed()

        speed = 0.02

        for i,_ in enumerate(word):
            if random()<0.2:
                coms[i:i] = \
                    getattr(self, choice([*filter(lambda x: "event" in x, Typer.__dict__)]))() 
        
        for com, val in coms:
            match com, val:
                case ("t", val):
                    self.ctrl.press(val)
                    self.ctrl.release(val)
                case ("c", val):
                    speed = val
                case ("p", val):
                    sleep(val)
            sleep(speed+(random()-0.5)*speed)
        sleep(0.1)
        self.ctrl.press(Key.enter)


class Wobinator:
    def __init__(self,
        pg=PromptGrabber(),
        ps=PromptSearcher(),
        ty=Typer()
    ):
        self.pg = pg
        self.ps = ps
        self.ty = ty
        self.previous_prompt = None
    
    def exec(self):
        prompt = self.pg.grab() or "//"
        if prompt != self.previous_prompt:
            matches = self.ps.matches(prompt)
            self.previous_prompt = prompt
            return (prompt, matches)
    
    def word_selected(self, word):
        self.ty.do_typing(word)

class GuiWrapper(Tk, Wobinator):
    N_OF_WORDS = 10

    def __init__(self):
        Tk.__init__(self)
        Wobinator.__init__(self)

        self.attributes("-topmost", True)

        self.prompt_var = StringVar()
        Label(self, text="Prompt: ").grid(column=0, row=0)
        Label(self, textvariable=self.prompt_var)\
            .grid(column=0, row=1)
        
        self.word_vars = [StringVar() for _ in range(self.N_OF_WORDS)]
        for i, var in enumerate(self.word_vars):
            Button(self, textvariable=var, width=25, command=self.button_com(var))\
                .grid(column=2, row=i)

    def button_com(self, var):
        return lambda: (sleep(1), self.ty.do_typing(var.get()))

    def do_work(self):
        res = self.exec()
        if res:
            prompt, matches = res
            self.prompt_var.set(prompt)
            for var, word in zip(self.word_vars, matches):
                var.set(word)
    
    def mainloop(self):
        def f():
            while True: self.do_work()
        Thread(target=f).start()
        return super().mainloop()

app = GuiWrapper()

app.mainloop()