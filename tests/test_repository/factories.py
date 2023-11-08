from factory import DictFactory
from factory.fuzzy import FuzzyInteger
from factory.fuzzy import FuzzyText

from issue_tracker_bot.repository import commons


class ReporterFactory(DictFactory):
    id = FuzzyInteger(1, 1000000000)
    name = FuzzyText()
    role = commons.Roles.reporter.value


class DeviceFactory(DictFactory):
    name = FuzzyText()
    group = FuzzyText()


class ProblemRecordFactory(DictFactory):
    reporter_id = FuzzyInteger(1, 1000)
    device_id = FuzzyInteger(1, 1000)
    text = FuzzyText()
    kind = commons.ReportKinds.problem.value


class SolutionRecordFactory(DictFactory):
    reporter_id = FuzzyInteger(1, 1000)
    device_id = FuzzyInteger(1, 1000)
    text = FuzzyText()
    kind = commons.ReportKinds.solution.value
