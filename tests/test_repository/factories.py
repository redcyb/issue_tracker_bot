from factory import DictFactory
from factory.fuzzy import FuzzyInteger
from factory.fuzzy import FuzzyText

from issue_tracker_bot.repository import commons


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
