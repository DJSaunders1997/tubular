"""This module contains transformers that deal with imputation of missing values."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

import narwhals as nw
import numpy as np
import pandas as pd

from tubular.base import BaseTransformer
from tubular.mixins import WeightColumnMixin

if TYPE_CHECKING:
    import pandas as pd
    from narwhals.typing import FrameT


class BaseImputer(BaseTransformer):
    """Base imputer class containing standard transform method that will use pd.Series.fillna with the
    values in the impute_values_ attribute.

    Other imputers in this module should inherit from this class.

    Attributes
    ----------

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    """

    polars_compatible = True

    FITS = False

    @nw.narwhalify
    def transform(self, X: FrameT) -> FrameT:
        """Impute missing values with median values calculated from fit method.

        Parameters
        ----------
        X : FrameT
            Data to impute.

        Returns
        -------
        X : FrameT
            Transformed input X with nulls imputed with the median value for the specified columns.

        """
        self.check_is_fitted(["impute_values_"])

        X = nw.from_native(super().transform(X))

        new_col_expressions = [
            nw.col(c).fill_null(self.impute_values_[c]) for c in self.columns
        ]

        return X.with_columns(
            new_col_expressions,
        )


class ArbitraryImputer(BaseImputer):
    """Transformer to impute null values with an arbitrary pre-defined value.

    Parameters
    ----------
    impute_value : int or float or str
        Value to impute nulls with.
    columns : None or str or list, default = None
        Columns to impute, if the default of None is supplied all columns in X are used
        when the transform method is called.
    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------
    impute_value : int or float or str
        Value to impute nulls with.

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework
    """

    polars_compatible = False

    FITS = False

    def __init__(
        self,
        impute_value: float | str,
        columns: str | list[str],
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

        if (
            not isinstance(impute_value, int)
            and not isinstance(impute_value, float)
            and not isinstance(impute_value, str)
        ):
            msg = f"{self.classname()}: impute_value should be a single value (int, float or str)"
            raise ValueError(msg)

        self.impute_values_ = {}
        self.impute_value = impute_value

        for c in self.columns:
            self.impute_values_[c] = self.impute_value

    def transform(self, X: pd.DataFrame) -> pd.DataFrame:
        """Impute missing values with the supplied impute_value.
        If columns is None all columns in X will be imputed.

        Parameters
        ----------
        X : pd.DataFrame
            Data containing columns to impute.

        Returns
        -------
        X : pd.DataFrame
            Transformed input X with nulls imputed with the specified impute_value, for the specified columns.

        Additions
        ---------
        * Preserving the datatypes of columns
        * Finding the target column dtype and cast imputer values as same dtype
        """
        self.check_is_fitted(["impute_value"])
        self.columns_check(X)
        for c in self.columns:
            if (
                "category" in X[c].dtype.name
                and self.impute_value not in X[c].cat.categories
            ):
                X[c] = X[c].cat.add_categories(
                    self.impute_value,
                )  # add new category

        # Calling the BaseImputer's transform method to impute the values
        X_transformed = super().transform(X)

        # casting imputer value as same dtype as original column
        for c in self.columns:
            dtype = X[c].dtype  # get the dtype of original column
            X_transformed[c] = X_transformed[c].astype(dtype)

        return X_transformed


class MedianImputer(BaseImputer, WeightColumnMixin):
    """Transformer to impute missing values with the median of the supplied columns.

    Parameters
    ----------
    columns : None or str or list, default = None
        Columns to impute, if the default of None is supplied all columns in X are used
        when the transform method is called.

    weights_column: None or str, default=None
        Column containing weights

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------
    impute_values_ : dict
        Created during fit method. Dictionary of float / int (median) values of columns
        in the columns attribute. Keys of impute_values_ give the column names.

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    """

    polars_compatible = False

    FITS = True

    def __init__(
        self,
        columns: str | list[str],
        weights_column: str | None = None,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

        WeightColumnMixin.check_and_set_weight(self, weights_column)

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        """Calculate median values to impute with from X.

        Parameters
        ----------
        X : pd.DataFrame
            Data to "learn" the median values from.

        y : None or pd.DataFrame or pd.Series, default = None
            Not required.

        """
        super().fit(X, y)

        self.impute_values_ = {}

        if self.weights_column is not None:
            WeightColumnMixin.check_weights_column(self, X, self.weights_column)

            for c in self.columns:
                # filter out null rows so their weight doesn't influence calc
                filtered = X[X[c].notna()]

                # below algorithm only works for >1 non null values
                if len(filtered) <= 0:
                    median = np.nan

                else:
                    # first sort df by column to be imputed (order of weight column shouldn't matter for median)
                    filtered = filtered.sort_values(c)

                    # next calculate cumulative weight sums
                    cumsum = filtered[self.weights_column].cumsum()

                    # find midpoint
                    cutoff = filtered[self.weights_column].sum() / 2.0

                    # find first value >= this point
                    median = filtered[c][cumsum >= cutoff].iloc[0]

                self.impute_values_[c] = median

        else:
            for c in self.columns:
                self.impute_values_[c] = X[c].median()

        return self


class MeanImputer(WeightColumnMixin, BaseImputer):
    """Transformer to impute missing values with the mean of the supplied columns.

    Parameters
    ----------
    columns : None or str or list, default = None
        Columns to impute, if the default of None is supplied all columns in X are used
        when the transform method is called.

    weights_column : None or str, default = None
        Column containing weights.

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------
    impute_values_ : dict
        Created during fit method. Dictionary of float / int (mean) values of columns
        in the columns attribute. Keys of impute_values_ give the column names.

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    """

    polars_compatible = False

    FITS = True

    def __init__(
        self,
        columns: str | list[str] | None = None,
        weights_column: str | None = None,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

        WeightColumnMixin.check_and_set_weight(self, weights_column)

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        """Calculate mean values to impute with from X.

        Parameters
        ----------
        X : pd.DataFrame
            Data to "learn" the mean values from.

        y : None or pd.DataFrame or pd.Series, default = None
            Not required.

        """
        super().fit(X, y)

        self.impute_values_ = {}

        if self.weights_column is not None:
            WeightColumnMixin.check_weights_column(self, X, self.weights_column)

            for c in self.columns:
                # filter out null rows so they don't count towards total weight
                filtered = X[X[c].notna()]

                # calculate total weight and total of weighted col
                total_weight = filtered[self.weights_column].sum()
                total_weighted_col = (
                    filtered[c].mul(filtered[self.weights_column]).sum()
                )

                # find weighted mean and add to dict
                weighted_mean = total_weighted_col / total_weight

                self.impute_values_[c] = weighted_mean

        else:
            for c in self.columns:
                self.impute_values_[c] = X[c].mean()

        return self


class ModeImputer(BaseImputer, WeightColumnMixin):
    """Transformer to impute missing values with the mode of the supplied columns.

    If mode is NaN, a warning will be raised.

    Parameters
    ----------
    columns : None or str or list, default = None
        Columns to impute, if the default of None is supplied all columns in X are used
        when the transform method is called.

    weights_column : str
        Name of weights columns to use if mode should be in terms of sum of weights
        not count of rows.

    **kwargs
        Arbitrary keyword arguments passed onto BaseTransformer.init method.

    Attributes
    ----------
    impute_values_ : dict
        Created during fit method. Dictionary of float / int (mode) values of columns
        in the columns attribute. Keys of impute_values_ give the column names.

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    """

    polars_compatible = False

    FITS = True

    def __init__(
        self,
        columns: str | list[str] | None = None,
        weights_column: str | None = None,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

        WeightColumnMixin.check_and_set_weight(self, weights_column)

    def fit(self, X: pd.DataFrame, y: pd.Series | None = None) -> pd.DataFrame:
        """Calculate mode values to impute with from X.

        Parameters
        ----------
        X : pd.DataFrame
            Data to "learn" the mode values from.

        y : None or pd.DataFrame or pd.Series, default = None
            Not required.

        """
        super().fit(X, y)

        self.impute_values_ = {}

        if self.weights_column is None:
            for c in self.columns:
                mode_value = X[c].mode(dropna=True)

                if len(mode_value) == 0:
                    self.impute_values_[c] = np.nan

                    warnings.warn(
                        f"ModeImputer: The Mode of column {c} is NaN.",
                        stacklevel=2,
                    )

                else:
                    self.impute_values_[c] = mode_value[0]

        else:
            WeightColumnMixin.check_weights_column(self, X, self.weights_column)

            for c in self.columns:
                grouped = X.groupby(c)[self.weights_column].sum()

                if grouped.isna().all():
                    warnings.warn(
                        f"ModeImputer: The Mode of column {c} is NaN.",
                        stacklevel=2,
                    )

                    self.impute_values_[c] = np.nan

                else:
                    self.impute_values_[c] = grouped.idxmax()

        return self


class NearestMeanResponseImputer(BaseImputer):
    """Class to impute missing values with; the value for which the average response is closest
    to the average response for the unknown levels.

    Parameters
    ----------
    columns : None or str or list, default = None
        Columns to impute, if the default of None is supplied all columns in X are used
        when the transform method is called.

    Attributes
    ----------

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    """

    polars_compatible = True

    FITS = True

    def __init__(
        self,
        columns: str | list[str] | None = None,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

    @nw.narwhalify
    def fit(self, X: FrameT, y: nw.Series) -> FrameT:
        """Calculate mean values to impute with.

        Parameters
        ----------
        X : FrameT
            Data to fit the transformer on.

        y : nw.Series
            Response column used to determine the value to impute with. The average response for
            each level of every column is calculated. The level which has the closest average response
            to the average response of the unknown levels is selected as the imputation value.

        """

        super().fit(X, y)

        n_nulls = y.is_null().sum()

        if n_nulls > 0:
            msg = f"{self.classname()}: y has {n_nulls} null values"
            raise ValueError(msg)

        self.impute_values_ = {}

        X_y = nw.from_native(self._combine_X_y(X, y))
        response_column = "_temporary_response"

        for c in self.columns:
            c_nulls = X.select(nw.col(c).is_null())[c]

            if c_nulls.sum() == 0:
                msg = f"{self.classname()}: Column {c} has no missing values, cannot use this transformer."
                raise ValueError(msg)

            mean_response_by_levels = (
                X_y.filter(~c_nulls).group_by(c).agg(nw.col(response_column).mean())
            )

            mean_response_nulls = X_y.filter(c_nulls)[response_column].mean()

            mean_response_by_levels = mean_response_by_levels.with_columns(
                (nw.col(response_column) - mean_response_nulls)
                .abs()
                .alias("abs_diff_response"),
            )

            # take first value having the minimum difference in terms of average response
            self.impute_values_[c] = mean_response_by_levels.filter(
                mean_response_by_levels["abs_diff_response"]
                == mean_response_by_levels["abs_diff_response"].min(),
            )[c].item(index=0)

        return self


class NullIndicator(BaseTransformer):
    """Class to create a binary indicator column for null values.

    Parameters
    ----------
    columns : None or str or list, default = None
        Columns to produce indicator columns for, if the default of None is supplied all columns in X are used
        when the transform method is called.

    Attributes
    ----------

    polars_compatible : bool
        class attribute, indicates whether transformer has been converted to polars/pandas agnostic narwhals framework

    """

    polars_compatible = True

    def __init__(
        self,
        columns: str | list[str] | None = None,
        **kwargs: dict[str, bool],
    ) -> None:
        super().__init__(columns=columns, **kwargs)

    @nw.narwhalify
    def transform(self, X: FrameT) -> FrameT:
        """Create new columns indicating the position of null values for each variable in self.columns.

        Parameters
        ----------
        X : FrameT
            Data to add indicators to.

        """
        X = nw.from_native(super().transform(X))

        for c in self.columns:
            X = X.with_columns(
                (nw.col(c).is_null()).cast(nw.Boolean).alias(f"{c}_nulls"),
            )

        return X
