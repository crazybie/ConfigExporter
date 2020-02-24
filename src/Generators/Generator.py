# encoding=utf8
from src.TypeHandler import *


class Generator(object):
    subclasses = []

    def __init__(self):
        self.logger = L.getLogger(self.__class__.__name__)

    def generate(self, tables):
        self.logger.debug('bypass')


def gen(c):
    Generator.subclasses.append(c)
    return c
