import os
import webbrowser
from datetime import datetime


def open_notepad():
    os.system("notepad")


def open_calculator():
    os.system("calc")


def open_paint():
    os.system("mspaint")


def open_cmd():
    os.system("start cmd")


def open_youtube():
    webbrowser.open("https://youtube.com")


def open_google():
    webbrowser.open("https://google.com")


def get_time():
    return datetime.now().strftime("%I:%M:%S %p")


def get_date():
    return datetime.now().strftime("%d-%m-%Y")