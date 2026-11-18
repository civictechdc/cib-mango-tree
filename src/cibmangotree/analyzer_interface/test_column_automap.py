"""Unit tests for analyzer input column auto-mapping."""

from cibmangotree.analyzer_interface.column_automap import (
    UserInputColumn,
    check_name_hint,
    column_automap,
)
from cibmangotree.analyzer_interface.interface import InputColumn


def test_check_name_hint_requires_every_word() -> None:
    assert check_name_hint("Twitter screenname", "twitter screen")
    assert check_name_hint("MESSAGE_TEXT", "message text")
    assert not check_name_hint("author", "user name")


def test_column_automap_prefers_name_hint_matches() -> None:
    user_columns = [
        UserInputColumn(name="author_id", data_type="identifier"),
        UserInputColumn(name="message_text", data_type="text"),
        UserInputColumn(name="created_at", data_type="datetime"),
    ]
    schema = [
        InputColumn(
            name="user_id",
            data_type="identifier",
            name_hints=["author id", "user id"],
        ),
        InputColumn(
            name="text",
            data_type="text",
            name_hints=["message text", "tweet"],
        ),
        InputColumn(
            name="timestamp",
            data_type="datetime",
            name_hints=["created"],
        ),
    ]

    assert column_automap(user_columns, schema) == {
        "user_id": "author_id",
        "text": "message_text",
        "timestamp": "created_at",
    }


def test_column_automap_skips_incompatible_types() -> None:
    user_columns = [
        UserInputColumn(name="message_text", data_type="text"),
        UserInputColumn(name="retweet_count", data_type="integer"),
    ]
    schema = [
        InputColumn(
            name="text",
            data_type="text",
            name_hints=["message"],
        ),
        InputColumn(
            name="timestamp",
            data_type="datetime",
            name_hints=["message"],
        ),
    ]

    assert column_automap(user_columns, schema) == {"text": "message_text"}


def test_column_automap_falls_back_to_best_compatible_type() -> None:
    user_columns = [
        UserInputColumn(name="col_a", data_type="text"),
        UserInputColumn(name="col_b", data_type="integer"),
    ]
    schema = [
        InputColumn(name="count", data_type="integer", name_hints=[]),
    ]

    assert column_automap(user_columns, schema) == {"count": "col_b"}
