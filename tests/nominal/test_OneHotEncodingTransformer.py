import numpy as np
import pandas as pd
import pytest
import sklearn
import test_aide as ta

import tests.test_data as d
import tubular
from tubular.nominal import OneHotEncodingTransformer


class TestInit:
    """Tests for OneHotEncodingTransformer.init()."""

    def test_super_init_called(self, mocker):
        """Test that init calls BaseTransformer.init.

        Note, not using ta.functions.assert_function_call for this as it does not handle self being passed to BaseTransformer.init.
        """
        expected_keyword_args = {"columns": None, "verbose": True, "copy": None}

        mocker.patch("tubular.base.BaseTransformer.__init__")

        x = OneHotEncodingTransformer(columns=None, verbose=True)

        assert (
            tubular.base.BaseTransformer.__init__.call_count == 1
        ), f"Not enough calls to BaseTransformer.__init__ -\n  Expected: 1\n  Actual: {tubular.base.BaseTransformer.__init__.call_count}"

        call_args = tubular.base.BaseTransformer.__init__.call_args_list[0]
        call_pos_args = call_args[0]
        call_kwargs = call_args[1]

        ta.equality.assert_equal_dispatch(
            expected=expected_keyword_args,
            actual=call_kwargs,
            msg="kwargs for BaseTransformer.__init__ in OneHotEncodingTransformer.init",
        )

        assert (
            len(call_pos_args) == 1
        ), f"Unepxected number of positional args in BaseTransformer.__init__ call -\n  Expected: 1\n  Actual: {len(call_pos_args)}"

        assert (
            call_pos_args[0] is x
        ), f"Unexpected positional arg (self) in BaseTransformer.__init__ call -\n  Expected: self\n  Actual: {call_pos_args[0]}"


class TestFit:
    """Tests for OneHotEncodingTransformer.fit()."""

    def test_base_transformer_fit_called(self, mocker):
        """Test that fit calls BaseTransformer.fit."""
        expected_keyword_args = {"X": d.create_df_1(), "y": None}

        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        mocker.patch("tubular.base.BaseTransformer.fit")

        x.fit(df)

        assert (
            tubular.base.BaseTransformer.fit.call_count == 1
        ), f"Not enough calls to BaseTransformer.fit -\n  Expected: 1\n  Actual: {tubular.base.BaseTransformer.fit.call_count}"

        call_args = tubular.base.BaseTransformer.fit.call_args_list[0]
        call_pos_args = call_args[0]
        call_kwargs = call_args[1]

        ta.equality.assert_equal_dispatch(
            expected=expected_keyword_args,
            actual=call_kwargs,
            msg="kwargs for BaseTransformer.fit in OneHotEncodingTransformer.init",
        )

        assert (
            len(call_pos_args) == 1
        ), f"Unepxected number of positional args in BaseTransformer.fit call -\n  Expected: 1\n  Actual: {len(call_pos_args)}"

        assert (
            call_pos_args[0] is x
        ), f"Unexpected positional arg (self) in BaseTransformer.fit call -\n  Expected: self\n  Actual: {call_pos_args[0]}"

    def test_one_hot_encoder_fit_called(self, mocker):
        """Test that fit calls OneHotEncoder.fit."""
        expected_keyword_args = {"X": d.create_df_1()[["b"]], "y": None}

        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        mocker.patch("sklearn.preprocessing.OneHotEncoder.fit")

        x.fit(df)

        assert (
            sklearn.preprocessing.OneHotEncoder.fit.call_count == 1
        ), f"Not enough calls to OneHotEncoder.fit -\n  Expected: 1\n  Actual: {sklearn.preprocessing.OneHotEncoder.fit.call_count}"

        call_args = sklearn.preprocessing.OneHotEncoder.fit.call_args_list[0]
        call_pos_args = call_args[0]
        call_kwargs = call_args[1]

        ta.equality.assert_equal_dispatch(
            expected=expected_keyword_args,
            actual=call_kwargs,
            msg="kwargs for OneHotEncoder.fit in OneHotEncodingTransformer.init",
        )

        assert (
            len(call_pos_args) == 1
        ), f"Unepxected number of positional args in OneHotEncoder.fit call -\n  Expected: 1\n  Actual: {len(call_pos_args)}"

        assert (
            call_pos_args[0] is x
        ), f"Unexpected positional arg (self) in OneHotEncoder.fit call -\n  Expected: self\n  Actual: {call_pos_args[0]}"

    def test_nulls_in_X_error(self):
        """Test that an exception is raised if X has nulls in column to be fit on."""
        df = d.create_df_2()

        x = OneHotEncodingTransformer(columns=["b", "c"])

        with pytest.raises(
            ValueError,
            match="OneHotEncodingTransformer: column b has nulls - replace before proceeding",
        ):
            x.fit(df)

    def test_fields_with_over_100_levels_error(self):
        """Test that OneHotEncodingTransformer.fit on fields with more than 100 levels raises error."""
        df = pd.DataFrame({"b": list(range(101))})
        df["a"] = 1

        x = OneHotEncodingTransformer(columns=["a", "b"])

        with pytest.raises(
            ValueError,
            match="OneHotEncodingTransformer: column b has over 100 unique values - consider another type of encoding",
        ):
            x.fit(df)

    def test_fit_returns_self(self):
        """Test fit returns self?."""
        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        x_fitted = x.fit(df)

        assert (
            x_fitted is x
        ), "Returned value from OneHotEncodingTransformer.fit not as expected."

    def test_fit_not_changing_data(self):
        """Test fit does not change X."""
        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        x.fit(df)

        ta.equality.assert_equal_dispatch(
            expected=d.create_df_1(),
            actual=df,
            msg="Check X not changing during fit",
        )


class TestTransform:
    """Tests for OneHotEncodingTransformer.transform()."""

    def expected_df_1():
        """Expected output for test_expected_output."""
        df = pd.DataFrame(
            {
                "a": [4, 2, 2, 1, 3],
                "b": ["x", "z", "y", "x", "x"],
                "c": ["c", "a", "a", "c", "b"],
            },
        )

        df["c"] = df["c"].astype("category")

        df["b_x"] = [1.0, 0.0, 0.0, 1.0, 1.0]
        df["b_y"] = [0.0, 0.0, 1.0, 0.0, 0.0]
        df["b_z"] = [0.0, 1.0, 0.0, 0.0, 0.0]

        return df

    def expected_df_2():
        """Expected output for test_unseen_categories_encoded_as_all_zeroes."""
        df = pd.DataFrame(
            {
                "a": [1, 5, 2, 3, 3],
                "b": ["w", "w", "z", "y", "x"],
                "c": ["a", "a", "c", "b", "a"],
            },
            index=[10, 15, 200, 251, 59],
        )

        df["c"] = df["c"].astype("category")

        df["a_1"] = [1.0, 0.0, 0.0, 0.0, 0.0]
        df["a_2"] = [0.0, 0.0, 1.0, 0.0, 0.0]
        df["a_3"] = [0.0, 0.0, 0.0, 1.0, 1.0]
        df["a_4"] = [0.0, 0.0, 0.0, 0.0, 0.0]
        df["b_x"] = [0.0, 0.0, 0.0, 0.0, 1.0]
        df["b_y"] = [0.0, 0.0, 0.0, 1.0, 0.0]
        df["b_z"] = [0.0, 0.0, 1.0, 0.0, 0.0]
        df["c_a"] = [1.0, 1.0, 0.0, 0.0, 1.0]
        df["c_b"] = [0.0, 0.0, 0.0, 1.0, 0.0]
        df["c_c"] = [0.0, 0.0, 1.0, 0.0, 0.0]

        return df

    def test_columns_check_call(self, mocker):
        """Test the first call to BaseTransformer columns_check."""
        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        x.fit(df)

        expected_call_args = {0: {"args": (d.create_df_1(),), "kwargs": {}}}

        with ta.functions.assert_function_call(
            mocker,
            tubular.base.BaseTransformer,
            "columns_check",
            expected_call_args,
        ):
            x.transform(df)

    def test_non_numeric_column_error_1(self):
        """Test that transform will raise an error if a column to transform has nulls."""
        df_train = d.create_df_1()
        df_test = d.create_df_2()

        x = OneHotEncodingTransformer(columns=["b"])

        x.fit(df_train)

        with pytest.raises(
            ValueError,
            match="OneHotEncodingTransformer: column b has nulls - replace before proceeding",
        ):
            x.transform(df_test)

    def test_base_transformer_transform_called(self, mocker):
        """Test that BaseTransformer.transform called."""
        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        x.fit(df)

        mocker.patch(
            "tubular.base.BaseTransformer.transform",
            return_value=d.create_df_1(),
        )

        x.transform(df)

        assert (
            tubular.base.BaseTransformer.transform.call_count == 1
        ), f"Not enough calls to BaseTransformer.transform -\n  Expected: 1\n  Actual: {tubular.base.BaseTransformer.transform.call_count}"

        call_args = tubular.base.BaseTransformer.transform.call_args_list[0]
        call_pos_args = call_args[0]
        call_kwargs = call_args[1]

        ta.equality.assert_equal_dispatch(
            expected={},
            actual=call_kwargs,
            msg="kwargs for BaseTransformer.transform in OneHotEncodingTransformer.init",
        )

        expected_pos_args = (x, d.create_df_1())

        assert (
            len(call_pos_args) == 2
        ), f"Unepxected number of positional args in BaseTransformer.transform call -\n  Expected: 2\n  Actual: {len(call_pos_args)}"

        ta.equality.assert_frame_equal_msg(
            expected=expected_pos_args[1],
            actual=call_pos_args[1],
            msg_tag="X positional arg in BaseTransformer.transform call",
        )

        assert (
            expected_pos_args[0] == call_pos_args[0]
        ), "self positional arg in BaseTransformer.transform call"

    def test_one_hot_encoder_transform_called(self, mocker):
        """Test that OneHotEncoder.transform called."""
        df = d.create_df_1()

        x = OneHotEncodingTransformer(columns="b")

        x.fit(df)

        mocker.patch("sklearn.preprocessing.OneHotEncoder.transform")

        x.transform(df)

        assert (
            sklearn.preprocessing.OneHotEncoder.transform.call_count == 1
        ), f"Not enough calls to OneHotEncoder.transform -\n  Expected: 1\n  Actual: {sklearn.preprocessing.OneHotEncoder.transform.call_count}"

        call_args = sklearn.preprocessing.OneHotEncoder.transform.call_args_list[0]
        call_pos_args = call_args[0]
        call_kwargs = call_args[1]

        ta.equality.assert_equal_dispatch(
            expected={},
            actual=call_kwargs,
            msg="kwargs for OneHotEncodingTransformer.transform in BaseTransformer.init",
        )

        assert (
            len(call_pos_args) == 2
        ), f"Unepxected number of positional args in OneHotEncodingTransformer.transform call -\n  Expected: 2\n  Actual: {len(call_pos_args)}"

        assert (
            call_pos_args[0] is x
        ), f"Unexpected positional arg (self, index 1) in OneHotEncodingTransformer.transform call -\n  Expected: self\n  Actual: {call_pos_args[0]}"

        ta.equality.assert_frame_equal_msg(
            expected=d.create_df_1()[["b"]],
            actual=call_pos_args[1],
            msg_tag="X positional arg in OneHotEncodingTransformer.transform call",
        )

    @pytest.mark.parametrize(
        ("df_test", "expected"),
        ta.pandas.adjusted_dataframe_params(d.create_df_7(), expected_df_1()),
    )
    def test_expected_output(self, df_test, expected):
        """Test that OneHotEncodingTransformer.transform encodes the feature correctly.

        Also tests that OneHotEncodingTransformer.transform does not modify unrelated columns.
        """
        # transformer is fit on the whole dataset separately from the input df to work with the decorators
        columns = ["b"]
        df_train = d.create_df_7()
        x = OneHotEncodingTransformer(columns=columns)
        x.fit(df_train)

        df_transformed = x.transform(df_test)

        for col in [
            column + f"_{value}"
            for column in columns
            for value in df_train[column].unique().tolist()
        ]:
            expected[col] = expected[col].astype(np.int8)

        ta.equality.assert_frame_equal_msg(
            expected=expected,
            actual=df_transformed,
            msg_tag="Unspecified columns changed in transform",
        )

    def test_categories_not_modified(self):
        """Test that the categories from fit are not changed in transform."""
        df_train = d.create_df_1()
        df_test = d.create_df_7()

        x = OneHotEncodingTransformer(columns=["a", "b"], verbose=False)
        x2 = OneHotEncodingTransformer(columns=["a", "b"], verbose=False)

        x.fit(df_train)
        x2.fit(df_train)

        x.transform(df_test)

        ta.equality.assert_equal_dispatch(
            expected=list(x2.categories_[0]),
            actual=list(x.categories_[0]),
            msg="categories_ (index 0) modified during transform",
        )

        ta.equality.assert_equal_dispatch(
            expected=list(x2.categories_[1]),
            actual=list(x.categories_[1]),
            msg="categories_ (index 1) modified during transform",
        )

    def test_renaming_feature_works_as_expected(self):
        """Test OneHotEncodingTransformer.transform() is renaming features correctly."""
        df = d.create_df_7()
        df = df[["b", "c"]]

        x = OneHotEncodingTransformer(
            columns=["b", "c"],
            separator="|",
            drop_original=True,
        )

        x.fit(df)

        df_transformed = x.transform(df)

        ta.equality.assert_equal_dispatch(
            expected=["b|x", "b|y", "b|z", "c|a", "c|b", "c|c"],
            actual=list(df_transformed.columns.values),
            msg="renaming columns feature in OneHotEncodingTransformer.transform",
        )

    def test_warning_generated_by_unseen_categories(self):
        """Test OneHotEncodingTransformer.transform triggers a warning for unseen categories."""
        df_train = d.create_df_7()
        df_test = d.create_df_8()

        x = OneHotEncodingTransformer(columns=["a", "b", "c"], verbose=True)

        x.fit(df_train)

        with pytest.warns(Warning):
            x.transform(df_test)

    @pytest.mark.parametrize(
        ("df_test", "expected"),
        ta.pandas.adjusted_dataframe_params(d.create_df_8(), expected_df_2()),
    )
    def test_unseen_categories_encoded_as_all_zeroes(self, df_test, expected):
        """Test OneHotEncodingTransformer.transform encodes unseen categories correctly (all 0s)."""
        # transformer is fit on the whole dataset separately from the input df to work with the decorators
        df_train = d.create_df_7()
        columns = ["a", "b", "c"]
        x = OneHotEncodingTransformer(columns=columns, verbose=False)
        x.fit(df_train)

        df_transformed = x.transform(df_test)

        for col in [
            column + f"_{value}"
            for column in columns
            for value in df_train[column].unique().tolist()
        ]:
            expected[col] = expected[col].astype(np.int8)

        ta.equality.assert_equal_dispatch(
            expected=expected,
            actual=df_transformed,
            msg="unseen category rows not encoded as 0s",
        )

    def test_original_columns_dropped_when_specified(self):
        """Test OneHotEncodingTransformer.transform drops original columns get when specified."""
        df = d.create_df_7()

        x = OneHotEncodingTransformer(columns=["a", "b", "c"], drop_original=True)

        x.fit(df)

        df_transformed = x.transform(df)

        ta.equality.assert_equal_dispatch(
            expected=["a", "b", "c"],
            actual=[
                x
                for x in df.columns.to_numpy()
                if x not in df_transformed.columns.to_numpy()
            ],
            msg="original columns not dropped",
        )

    def test_original_columns_kept_when_specified(self):
        """Test OneHotEncodingTransformer.transform keeps original columns when specified."""
        df = d.create_df_7()

        x = OneHotEncodingTransformer(columns=["a", "b", "c"], drop_original=False)

        x.fit(df)

        df_transformed = x.transform(df)

        ta.equality.assert_equal_dispatch(
            expected=list(set()),
            actual=list({"a", "b", "c"} - set(df_transformed.columns)),
            msg="original columns not kept",
        )
