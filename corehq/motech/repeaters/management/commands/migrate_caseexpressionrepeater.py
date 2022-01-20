from corehq.motech.repeaters.utils import RepeaterMigrationHelper
from corehq.motech.repeaters.expression.repeaters import (
    SQLCaseExpressionRepeater,
)


class Command(RepeaterMigrationHelper):

    @classmethod
    def couch_doc_type(cls):
        return 'CaseExpressionRepeater'

    @classmethod
    def sql_class(cls):
        return SQLCaseExpressionRepeater

    def get_sql_options_obj(self, doc):
        return {
            "options": {
                "configured_fliter": doc.get("configured_filter"),
                "configured_expression": doc.get("configured_expression"),
                "format": doc.get("format"),
            }
        }
