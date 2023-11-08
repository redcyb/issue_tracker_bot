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
