from typing import get_args

from cibmangotree.analyzer_interface.data_type_compatibility import (
    data_type_mapping_preference,
)
from cibmangotree.analyzer_interface.interface import DataType


def test_mapping_preference_covers_every_data_type() -> None:
    assert set(data_type_mapping_preference) == set(get_args(DataType))
