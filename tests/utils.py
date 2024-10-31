import pandas as pd
import polars as pl
from narwhals.typing import FrameT
from pandas.testing import assert_frame_equal as assert_pandas_frame_equal
from polars.testing import assert_frame_equal as assert_polars_frame_equal


def align_pandas_and_polars_dtypes(
    pandas_df: pd.DataFrame,
    polars_df: pl.DataFrame,
) -> pl.DataFrame:
    """helper to ensure that dtypes are aligned between polars/pandas dfs used in tests. Avoids e.g.
    [0, None] being inferred as float in pandas and int in polars and complicating tests

    Parameters
    ----------
    pandas_df : pd.DataFrame
        pandas df to extract types from

    polars_df : pl.DataFrame
        polars df to apply types to

    Returns
    ----------

    pl.DataFrame: polars df with types converted to align with pandas_df

    """

    PANDAS_TO_POLARS_TYPES = {
        "int64": pl.Int64,
        "int32": pl.Int32,
        "int16": pl.Int16,
        "int8": pl.Int8,
        "float64": pl.Float64,
        "float32": pl.Float32,
        "object": pl.Utf8,
        "str": pl.String,
        "bool": pl.Boolean,
        "datetime64[ns]": pl.Datetime,
    }

    for col in pandas_df:
        pandas_col_type = str(pandas_df[col].dtype)
        polars_col_type = PANDAS_TO_POLARS_TYPES[pandas_col_type]
        polars_df = polars_df.with_columns(polars_df[col].cast(polars_col_type))

    return polars_df


def assert_frame_equal_dispatch(df1: FrameT, df2: FrameT) -> None:
    """fixture to return correct pandas/polars assert_frame_equal method

    Parameters
    ----------
    df1 : pd.DataFrame
        first df for comparison

    df1 : pd.DataFrame
        second df for comparison

    """

    if isinstance(df1, pd.DataFrame) and isinstance(df2, pd.DataFrame):
        return assert_pandas_frame_equal(df1, df2)

    if isinstance(df1, pl.DataFrame) and isinstance(df2, pl.DataFrame):
        return assert_polars_frame_equal(df1, df2)

    invalid_request_error = "tubular is setup to handle only pandas or polars inputs, and dfs input to this function should be from same library"
    raise ValueError(invalid_request_error)


def dataframe_init_dispatch(
    dataframe_dict: dict,
    library: str,
) -> FrameT:
    """
    Initialize a DataFrame using either Pandas or Polars library based on the specified library name.

    Parameters:
    dataframe_dict (dict): A dictionary where keys are column names and values are lists of column data.
    library (str): The name of the library to use for DataFrame creation. Should be either "pandas" or "polars".

    Returns:
    pl.DataFrame | pd.DataFrame: A DataFrame object from the specified library.

    Raises:
    ValueError: If the `library` parameter is not "pandas" or "polars".
    """

    pandas_df = pd.DataFrame(dataframe_dict)

    if library == "pandas":
        return pandas_df

    if library == "polars":
        polars_df = pl.DataFrame(dataframe_dict)

        return align_pandas_and_polars_dtypes(pandas_df, polars_df)

    library_error_message = (
        "The library parameter should be either 'pandas' or 'polars'."
    )
    raise ValueError(library_error_message)