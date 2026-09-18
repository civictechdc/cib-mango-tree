from .csv import CSVImporter
from .excel import ExcelImporter
from .huggingface import HuggingFaceImporter
from .importer import Importer, ImporterSession

# Core importers - no terminal dependencies
importers: list[Importer[ImporterSession]] = [
    CSVImporter(),
    ExcelImporter(),
]

# Importers that fetch data from a remote source rather than a local file/upload
web_importers: list[Importer[ImporterSession]] = [
    HuggingFaceImporter(),
]
