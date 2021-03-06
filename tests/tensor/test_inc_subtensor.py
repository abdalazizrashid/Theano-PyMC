import numpy as np
import pytest

import aesara
import aesara.tensor as tt
from tests import unittest_tools as utt


class TestIncSubtensor:
    """
    Partial testing.

    What could be tested:
    - increment vs set
    - thing incremented: scalar, vector, matrix,
    - increment/set: constant, scalar, vector, matrix
    - indices: scalar vs slice, constant vs variable, out of bound, ...
    - inplace

    NOTE: these are the same tests as test_incsubtensor.py, but using
    the new (read: not deprecated) inc_subtensor, set_subtensor
    functions.
    """

    def setup_method(self):
        utt.seed_rng()

    def test_simple_2d(self):
        # Increments or sets part of a tensor by a scalar using full slice and
        # a partial slice depending on a scalar.

        a = tt.dmatrix()
        increment = tt.dscalar()
        sl1 = slice(None)
        sl2_end = tt.lscalar()
        sl2 = slice(sl2_end)

        for do_set in [False, True]:

            if do_set:
                resut = tt.set_subtensor(a[sl1, sl2], increment)
            else:
                resut = tt.inc_subtensor(a[sl1, sl2], increment)

            f = aesara.function([a, increment, sl2_end], resut)

            val_a = np.ones((5, 5))
            val_inc = 2.3
            val_sl2_end = 2

            result = f(val_a, val_inc, val_sl2_end)

            expected_result = np.copy(val_a)
            if do_set:
                expected_result[:, :val_sl2_end] = val_inc
            else:
                expected_result[:, :val_sl2_end] += val_inc

            utt.assert_allclose(result, expected_result)

    def test_wrong_dims(self):
        a = tt.matrix()
        increment = tt.matrix()
        index = 0

        with pytest.raises(TypeError):
            tt.set_subtensor(a[index], increment)
        with pytest.raises(TypeError):
            tt.inc_subtensor(a[index], increment)

    def test_wrong_broadcast(self):
        a = tt.col()
        increment = tt.vector()

        # These symbolic graphs legitimate, as long as increment has exactly
        # one element. So it should fail at runtime, not at compile time.
        rng = np.random.RandomState(utt.fetch_seed())

        def rng_randX(*shape):
            return rng.rand(*shape).astype(aesara.config.floatX)

        for op in (tt.set_subtensor, tt.inc_subtensor):
            for base in (a[:], a[0]):
                out = op(base, increment)
                f = aesara.function([a, increment], out)
                # This one should work
                f(rng_randX(3, 1), rng_randX(1))
                # These ones should not
                with pytest.raises(ValueError):
                    f(rng_randX(3, 1), rng_randX(2))
                with pytest.raises(ValueError):
                    f(rng_randX(3, 1), rng_randX(3))
                with pytest.raises(ValueError):
                    f(rng_randX(3, 1), rng_randX(0))

    def test_simple_3d(self):
        # Increments or sets part of a tensor by a scalar using full slice and
        # a partial slice depending on a scalar.

        a = tt.dtensor3()
        increment = tt.dscalar()
        sl1 = slice(None)
        sl2_end = tt.lscalar()
        sl2 = slice(sl2_end)
        sl3 = 2

        val_a = np.ones((5, 3, 4))
        val_inc = 2.3
        val_sl2_end = 2

        for method in [tt.set_subtensor, tt.inc_subtensor]:
            print("MethodSet", method)

            resut = method(a[sl1, sl3, sl2], increment)

            f = aesara.function([a, increment, sl2_end], resut)

            expected_result = np.copy(val_a)
            result = f(val_a, val_inc, val_sl2_end)

            if method is tt.set_subtensor:
                expected_result[:, sl3, :val_sl2_end] = val_inc
            else:
                expected_result[:, sl3, :val_sl2_end] += val_inc

            utt.assert_allclose(result, expected_result)

            # Test when we broadcast the result
            resut = method(a[sl1, sl2], increment)

            f = aesara.function([a, increment, sl2_end], resut)

            expected_result = np.copy(val_a)
            result = f(val_a, val_inc, val_sl2_end)

            if method is tt.set_subtensor:
                expected_result[:, :val_sl2_end] = val_inc
            else:
                expected_result[:, :val_sl2_end] += val_inc

            utt.assert_allclose(result, expected_result)

    def test_grad_inc_set(self):
        def inc_slice(*s):
            def just_numeric_args(a, b):
                return tt.inc_subtensor(a[s], b)

            return just_numeric_args

        def set_slice(*s):
            def just_numeric_args(a, b):
                return tt.set_subtensor(a[s], b)

            return just_numeric_args

        for f_slice in [inc_slice, set_slice]:
            # vector
            utt.verify_grad(
                f_slice(slice(2, 4, None)),
                (
                    np.asarray([0, 1, 2, 3, 4, 5.0]),
                    np.asarray([9, 9.0]),
                ),
            )

            # matrix
            utt.verify_grad(
                f_slice(slice(1, 2, None), slice(None, None, None)),
                (
                    np.asarray([[0, 1], [2, 3], [4, 5.0]]),
                    np.asarray([[9, 9.0]]),
                ),
            )

            # single element
            utt.verify_grad(
                f_slice(2, 1),
                (
                    np.asarray([[0, 1], [2, 3], [4, 5.0]]),
                    np.asarray(9.0),
                ),
            )

            # broadcast
            utt.verify_grad(
                f_slice(2),
                (
                    np.asarray([[0, 1], [2, 3], [4, 5.0]]),
                    np.asarray(9.0),
                ),
            )
