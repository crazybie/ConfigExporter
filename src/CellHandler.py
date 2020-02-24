class CellHandler:
    def __init__(self):
        pass


# example
class accessory(CellHandler):
    def __init__(self):
        CellHandler.__init__(self)
        self['mergeAccessory'] = self.mergeAccessory

    def mergeAccessory(self):
        return '%s~%s' % (self['accessoryType'].value, self['accessoryLevel'].value)
