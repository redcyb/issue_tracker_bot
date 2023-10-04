class AppContext:
    _instance = None
    devices = None
    problems_kinds = None
    solutions_kinds = None
    open_problems: dict = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def set_devices(self, devices):
        self.devices = devices

    def set_problems_kinds(self, problems_kinds):
        self.problems_kinds = problems_kinds or []

    def set_solutions_kinds(self, solutions_kinds):
        self.solutions_kinds = solutions_kinds or []

    def set_open_problems(self, open_problems):
        self.open_problems = open_problems or {}

    # def init_devices(self):
    #     a = [i for i in range(1, 32)]
    #     b = [i for i in range(1, 36)]
    #
    #     step = 8
    #     self.devices = defaultdict(list)
    #
    #     def handle_part(_name, _part):
    #         while _part:
    #             row, _part = _part[:step], _part[step:]
    #             self.devices[_name].append(row)
    #
    #     handle_part("A", a)
    #     handle_part("B", b)
