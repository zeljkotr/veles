# -*- coding: utf-8 -*-

import re


REPLACEMENTS = {
    "CPU": "ce pe u",
    "GPU": "dzi pe u",
    "RAM": "ram memorija",
    "SSD": "es es de",
    "HDD": "ha de de",
    "USB": "ju es bi",
    "WiFi": "vaj faj",
    "Docker": "Doker",
    "GitHub": "Git hab",
    "Linux": "Linuks",
    "Windows": "Vindous",
    "GHz": "gigaherca",
    "MHz": "megaherca",
    "GB": "gigabajta",
    "TB": "terabajta",
}


def preprocess(text):

    for old, new in REPLACEMENTS.items():
        text = text.replace(old, new)

    text = re.sub(
        r"(\d+)\s*GB",
        r"\1 gigabajta",
        text
    )

    text = re.sub(
        r"(\d+)\s*%",
        r"\1 posto",
        text
    )

    text = re.sub(
        r"(\d+)\.(\d+)",
        r"\1 zarez \2",
        text
    )

    text = text.replace(".", ". ")

    return text