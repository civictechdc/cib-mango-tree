from cibmangotree.analyzer_interface import (
    AnalyzerInput,
    AnalyzerInterface,
    AnalyzerOutput,
    AnalyzerParam,
    ChoiceOption,
    ChoiceParam,
    InputColumn,
    OutputColumn,
)
from cibmangotree.analyzer_interface.params import IntegerParam

COL_USER_ID = "user_id"
COL_MESSAGE_TEXT = "message_text"
COL_TIMESTAMP = "timestamp"
COL_REL_TIMESTAMP = "rel_timestamp"

COL_USER_A = "user_a"
COL_USER_B = "user_b"
COL_WEIGHT = "weight"
COL_NORM_WEIGHT = "norm_weight"

OUTPUT_POSTS = "posts"
OUTPUT_EDGES = "edges"

PARAM_METHOD = "method"
PARAM_WIN_SIZE = "win_size"
PARAM_T_STEP = "t_step"
PARAM_MIN_POSTS = "min_posts"

METHOD_SLIDING = "sliding_window"
METHOD_ADO = "ado_window"
METHOD_TIME_OVERLAP = "time_overlap"

METHOD_OPTIONS = [
    ChoiceOption(value=METHOD_SLIDING, label="Sliding Window"),
    ChoiceOption(value=METHOD_ADO, label="Action Driven Overlapping Window"),
    ChoiceOption(value=METHOD_TIME_OVERLAP, label="Time Overlap"),
]

interface = AnalyzerInterface(
    id="time_coordination",
    version="0.1.0",
    name="Time Coordination",
    short_description="User networks from posting-time overlap",
    long_description="""
Time coordination builds a network of users whose posting times overlap. That can
suggest coordinated activity without looking at message text.

**Methods** (choose one on the parameters step):

- **Sliding Window** — fixed windows that slide across the timeline
- **Action Driven Overlapping Window (ADO)** — windows anchored on each post
- **Time Overlap** *(default)* — compares binned activity patterns; usually best on larger datasets

Window length is window size × time step (in seconds). For Time Overlap,
accounts below the minimum post count are left out of the graph.
""",
    input=AnalyzerInput(
        columns=[
            InputColumn(
                name=COL_USER_ID,
                human_readable_name="Unique User ID",
                data_type="identifier",
                description="Account / author identifier",
                name_hints=[
                    "author",
                    "user",
                    "username",
                    "screen name",
                    "handle",
                    "account",
                ],
            ),
            InputColumn(
                name=COL_TIMESTAMP,
                human_readable_name="Timestamp",
                data_type="datetime",
                description="When the message was posted",
                name_hints=["time", "timestamp", "date", "created", "createdAt"],
            ),
            InputColumn(
                name=COL_MESSAGE_TEXT,
                human_readable_name="Post Content",
                data_type="text",
                description="Text content of the message",
                name_hints=[
                    "message",
                    "text",
                    "content",
                    "body",
                    "tweet",
                    "post",
                ],
            ),
        ]
    ),
    outputs=[
        AnalyzerOutput(
            id=OUTPUT_POSTS,
            name="Posts",
            internal=True,
            description="Normalized posts used for graph build and Compare users",
            columns=[
                OutputColumn(name=COL_USER_ID, data_type="identifier"),
                OutputColumn(name=COL_TIMESTAMP, data_type="datetime"),
                OutputColumn(name=COL_MESSAGE_TEXT, data_type="text"),
                OutputColumn(name=COL_REL_TIMESTAMP, data_type="float"),
            ],
        ),
        AnalyzerOutput(
            id=OUTPUT_EDGES,
            name="User links",
            description="Weighted edges between users with overlapping posting times",
            columns=[
                OutputColumn(name=COL_USER_A, data_type="identifier"),
                OutputColumn(name=COL_USER_B, data_type="identifier"),
                OutputColumn(name=COL_WEIGHT, data_type="float"),
                OutputColumn(name=COL_NORM_WEIGHT, data_type="float"),
            ],
        ),
    ],
    params=[
        AnalyzerParam(
            id=PARAM_METHOD,
            human_readable_name="Method",
            description="How posting-time overlap between accounts is scored",
            type=ChoiceParam(options=METHOD_OPTIONS),
            # Time Overlap scales better on long/large datasets than Sliding Window.
            default=METHOD_TIME_OVERLAP,
        ),
        AnalyzerParam(
            id=PARAM_WIN_SIZE,
            human_readable_name="Window size (steps)",
            description="Number of time steps in each analysis window",
            type=IntegerParam(min=1, max=100),
            default=2,
        ),
        AnalyzerParam(
            id=PARAM_T_STEP,
            human_readable_name="Time step (seconds)",
            description=(
                "Seconds per time step; window length is win_size × t_step. "
                "Smaller steps are much slower on long timelines."
            ),
            type=IntegerParam(min=1, max=86400),
            default=300,
        ),
        AnalyzerParam(
            id=PARAM_MIN_POSTS,
            human_readable_name="Min posts (Time Overlap)",
            description="Minimum posts for an account to be a node (Time Overlap only)",
            type=IntegerParam(min=1, max=10_000),
            default=20,
        ),
    ],
)
