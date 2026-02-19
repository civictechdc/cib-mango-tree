from analyzer_interface import SecondaryAnalyzerDeclaration

from .interface import interface
from .main import main

copypasta_detection = SecondaryAnalyzerDeclaration(interface=interface, main=main)
