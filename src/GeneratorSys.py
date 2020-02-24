from src.Generators.Generator import *


# TODO: move lua & js type generation info from typeHandler to here.

class GeneratorSys:
    inst = None  # type: GeneratorSys

    def __init__(self):
        GeneratorSys.inst = self
        self.logger = L.getLogger(self.__class__.__name__)
        for i in walk(os.path.join(appCfg['cwd'], 'src/Generators'), '*.py'):
            if os.path.basename(i) in ['__init__.py', 'Generator.py']:
                continue
            execfile(i)

    def genAll(self, tables):
        startingTime = datetime.datetime.now()
        for i in Generator.subclasses:
            i().generate(tables)
        self.logger.info('all generating done, took %s', datetime.datetime.now() - startingTime)

    def genLoc(self, tables):
        LocGen = [i for i in Generator.subclasses if i.__name__ == 'LocGen'][0]
        LocGen().genLoc(tables)
