from enum import Enum


class Roles(Enum):
    admin = "admin"
    manager = "manager"
    reporter = "reporter"


class ReportKinds(Enum):
    problem = "problem"
    solution = "solution"
