from .csv import CSVImporter
from .excel import ExcelImporter
from .importer import Importer, ImporterSession

# Core importers - no terminal dependencies
importers: list[Importer[ImporterSession]] = [
    CSVImporter(),
    ExcelImporter(),
]
