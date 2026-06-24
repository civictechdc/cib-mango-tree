# Column type mapping and timestamp detection

## Symptom

A user maps columns for an analysis, opens the dropdown for a timestamp input,
and finds it empty or missing the column that holds the timestamp (#330, with
#249, #227, and #223 reporting variants). The CLI surfaced the same situation as
a re-promptable text error. The GUI shows a dropdown with nothing in it and no
way forward.

## Two causes

### Inference: non-ISO datetime strings are not parsed

Column semantics are inferred in
`src/cibmangotree/preprocessing/series_semantic.py`. The string-datetime path,
`parse_datetime_with_tz` (lines 57-115), strips timezone markers and then calls
`s.str.strptime(pl.Datetime(), strict=False)` with no format. `date_string`
(line 154) does the same with `pl.Date`. Polars infers only ISO-like layouts, so
a common input such as `MM/DD/YYYY HH:MM AM/PM` parses to null and the column is
classified as text.

`parse_time_military` (lines 40-54), directly above, already handles this: it
tries a list of explicit formats and keeps the first that parses. Give the
datetime and date paths the same treatment, with a short list of common formats
before the inference fallback. Inference also runs on a 100-row sample at a 0.8
threshold (`SeriesSemantic.check`), so a column whose parseable rows are sparse in
the sample can be missed.

### Compatibility: a datetime input accepts only an exact datetime match

`src/cibmangotree/analyzer_interface/data_type_compatibility.py:8` defines
`"datetime": [["datetime"]]`. A datetime input therefore offers only columns
inferred as exactly `datetime`. When inference misses, as above, nothing is
offered and the dropdown is empty.

The same function carries a latent failure. `get_data_type_compatibility_score`
(lines 20-37) indexes `data_type_mapping_preference[expected_data_type]`
directly, so an analyzer that declares an `expected_data_type` absent from the
dictionary raises `KeyError`. As analyzers are added, this breaks the mapping
screen rather than degrading to "not compatible".

## Changes

1. Guard the dictionary access with
   `data_type_mapping_preference.get(expected_data_type, [])`, returning `None`
   for an unknown type instead of raising. Add a regression test. Small and
   independent; do this first.
2. Add explicit format lists to `parse_datetime_with_tz` and the date path,
   matching `parse_time_military`. Extend `test_series_semantic.py` with the
   formats users actually submit.
3. Give the mapping screen a fallback: when no column is compatible with a
   required input, present the user's columns with a warning rather than an empty
   control, so a timestamp can be assigned by hand. This covers the cases
   inference will always miss.
4. Later: sample across the file rather than only the first rows, so detection
   does not change between files of the same shape.

## Verify against the worker path

Changes 2 and 3 alter which data reaches the analyzers. Check the analyzer output
against the snapshot tests once the comparer tolerance from
`worker-process-boundary.md` is in, so a real regression is not hidden by
exact-match noise.

## References

#330, #249, #227, #223; `series_semantic.py`, `data_type_compatibility.py`.
