from factory import DictFactory
from factory.fuzzy import FuzzyChoice
from factory.fuzzy import FuzzyInteger
from factory.fuzzy import FuzzyText

from issue_tracker_bot.repository import commons


class ReporterFactory(DictFactory):
    id = FuzzyText()
    name = FuzzyText()
    role = commons.Roles.reporter.value


class DeviceFactory(DictFactory):
    id = FuzzyText()
    name = FuzzyText()
    group = FuzzyText()


class ProblemRecordFactory(DictFactory):
    reporter_id = FuzzyText()
    device_id = FuzzyText()
    text = FuzzyText()
    kind = commons.ReportKinds.problem.value


class SolutionRecordFactory(DictFactory):
    reporter_id = FuzzyText()
    device_id = FuzzyText()
    text = FuzzyText()
    kind = commons.ReportKinds.solution.value


class PredefinedMessageFactory(DictFactory):
    id = FuzzyText()
    text = FuzzyText()
    kind = FuzzyChoice(
        [commons.ReportKinds.problem.value, commons.ReportKinds.solution.value]
    )
