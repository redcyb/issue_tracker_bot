from collections import defaultdict


class AppContext:
    devices = None

    def __init__(self):
        self.init_devices()

    def init_devices(self):
        a = [i for i in range(1, 32)]
        b = [i for i in range(1, 36)]

        step = 8
        self.devices = defaultdict(list)

        def handle_part(_name, _part):
            while _part:
                row, _part = _part[:step], _part[step:]
                self.devices[_name].append(row)

        handle_part("A", a)
        handle_part("B", b)
