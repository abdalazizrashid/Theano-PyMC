import numpy as np
import pytest

import aesara
import aesara.tensor as tt
from aesara import config, gof, printing
from aesara.gof.opt import check_stack_trace
from aesara.tensor import lvector, matrix, scalar, vector
from aesara.tensor.nnet import (
    CrossentropyCategorical1Hot,
    CrossentropyCategorical1HotGrad,
    CrossentropySoftmax1HotWithBiasDx,
    CrossentropySoftmaxArgmax1HotWithBias,
    Prepend_scalar_constant_to_each_row,
    Prepend_scalar_to_each_row,
    Softmax,
    SoftmaxGrad,
    SoftmaxWithBias,
    binary_crossentropy,
    categorical_crossentropy,
    confusion_matrix,
    crossentropy_categorical_1hot,
    crossentropy_softmax_1hot,
    crossentropy_softmax_1hot_with_bias,
    crossentropy_softmax_1hot_with_bias_dx,
    crossentropy_softmax_argmax_1hot_with_bias,
    elu,
    h_softmax,
    logsoftmax,
    logsoftmax_op,
    relu,
    selu,
    sigmoid,
    sigmoid_binary_crossentropy,
    softmax,
    softmax_grad,
    softmax_graph,
    softmax_op,
    softmax_with_bias,
    softplus,
)
from aesara.tensor.nnet.nnet import LogSoftmax, softsign
from tests import unittest_tools as utt
from tests.tensor.utils import (
    _good_broadcast_unary_normal_float_no_complex,
    check_floatX,
    makeBroadcastTester,
    upcast_int8_nfunc,
)


class TestSigmoid:
    def setup_method(self):
        utt.seed_rng()

    def test_elemwise(self):
        utt.verify_grad(sigmoid, [np.random.rand(3, 4)])


class TestSoftplus:
    def setup_method(self):
        utt.seed_rng()

    def test_elemwise(self):
        utt.verify_grad(softplus, [np.random.rand(3, 4)])


class TestSoftmax(utt.InferShapeTester):
    def test_basic(self):
        def f(a):
            return softmax_op(a)[:, 0]

        utt.verify_grad(f, [np.random.rand(3, 4)])

        def f(a):
            return softmax_op(a)[:, 1]

        utt.verify_grad(f, [np.random.rand(3, 4)])

        def f(a):
            return softmax_op(a)[:, 2]

        utt.verify_grad(f, [np.random.rand(3, 4)])

        def f(a):
            return softmax_op(a)[:, 3]

        utt.verify_grad(f, [np.random.rand(3, 4)])

    def test_infer_shape(self):
        admat = matrix()
        admat_val = np.random.rand(3, 4).astype(config.floatX)
        self._compile_and_check([admat], [Softmax()(admat)], [admat_val], Softmax)

    def test_vector(self):
        x = tt.vector()
        f = aesara.function([x], softmax_op(x))

        xv = np.random.randn(6).astype(config.floatX)
        assert np.allclose(f(xv), np.exp(xv) / np.exp(xv).sum())

    def test_vector_grad(self):
        def f(a):
            return softmax_op(a)

        utt.verify_grad(f, [np.random.rand(4)])


class TestSoftmaxWithBias(utt.InferShapeTester):
    def test_basic(self):
        def f(a, b):
            return softmax_with_bias(a, b)[:, 0]

        utt.verify_grad(f, [np.random.rand(3, 4), np.random.rand(4)])

        def f(a, b):
            return softmax_with_bias(a, b)[:, 1]

        utt.verify_grad(f, [np.random.rand(3, 4), np.random.rand(4)])

        def f(a, b):
            return softmax_with_bias(a, b)[:, 2]

        utt.verify_grad(f, [np.random.rand(3, 4), np.random.rand(4)])

        def f(a, b):
            return softmax_with_bias(a, b)[:, 3]

        utt.verify_grad(f, [np.random.rand(3, 4), np.random.rand(4)])

    def test_broadcast(self):
        # test that we don't raise an error during optimization for no good
        # reason as softmax_with_bias don't support correctly some/all
        # broadcasted inputs pattern
        initial_W = np.asarray(
            [[0.1, 0.1, 0.1], [0.1, 0.1, 0.1], [0.1, 0.1, 0.1]],
            dtype=aesara.config.floatX,
        )
        W = aesara.shared(value=initial_W, name="W")
        vbias = aesara.shared(value=0.1, name="vbias")  # 0.01
        hid = tt.vector("hid")
        f = aesara.function([hid], softmax_op(tt.dot(hid, W.T) + vbias))
        ops = [node.op for node in f.maker.fgraph.toposort()]
        assert softmax_with_bias not in ops
        assert softmax_op in ops

        f([0, 1, 0])
        # print f.maker.fgraph.toposort()

    def test_softmax_with_bias_trace(self):
        a = aesara.shared(np.random.randn(3).astype(config.floatX))
        b = aesara.shared(np.float32(np.random.randn()))
        sm = softmax(a + b)
        f = aesara.function([], sm)
        assert check_stack_trace(f, ops_to_check="last")

    def test_infer_shape(self):
        admat = matrix()
        advec = vector()
        admat_val = np.random.rand(3, 4).astype(config.floatX)
        advec_val = np.random.rand(4).astype(config.floatX)
        self._compile_and_check(
            [admat, advec],
            [SoftmaxWithBias()(admat, advec)],
            [admat_val, advec_val],
            SoftmaxWithBias,
        )


class TestLogSoftmax(utt.InferShapeTester):
    def test_basic(self):
        def f(a):
            return logsoftmax_op(a)[:, 0]

        utt.verify_grad(f, [np.random.rand(3, 4)])

        def f(a):
            return logsoftmax_op(a)[:, 1]

        utt.verify_grad(f, [np.random.rand(3, 4)])

        def f(a):
            return logsoftmax_op(a)[:, 2]

        utt.verify_grad(f, [np.random.rand(3, 4)])

        def f(a):
            return logsoftmax_op(a)[:, 3]

        utt.verify_grad(f, [np.random.rand(3, 4)])

    def test_matrix(self):
        def f(a):
            return logsoftmax_op(a)

        utt.verify_grad(f, [np.random.rand(3, 4)])

    def test_vector(self):
        x = tt.vector()
        f = aesara.function([x], logsoftmax_op(x))

        xv = np.random.randn(6).astype(config.floatX)
        assert np.allclose(f(xv), np.log(np.exp(xv) / np.exp(xv).sum()))

    def test_vector_grad(self):
        def f(a):
            return logsoftmax_op(a)

        utt.verify_grad(f, [np.random.rand(4)])

    def test_allclose(self):
        m = aesara.config.mode
        m = aesara.compile.get_mode(m)
        m.check_isfinite = False
        x, y = tt.matrices("xy")
        # regular softmax and crossentropy
        sm = softmax(x)
        cm = categorical_crossentropy(sm, y)

        # numerically stable log-softmax with crossentropy
        logsm = logsoftmax(x)
        sm2 = tt.exp(logsm)  # just used to show equivalence with sm
        cm2 = -tt.sum(y * logsm, axis=1)
        grad = tt.grad(cm2.mean(), x)

        # create some inputs into a softmax that are large and labels
        a = np.exp(10 * np.random.rand(5, 10).astype(aesara.config.floatX))
        # create some one-hot coded labels
        b = np.eye(5, 10).astype(aesara.config.floatX)

        # show equivalence of softmax and exponentiated numerically stable
        # log-softmax
        f1 = aesara.function([x], [sm, sm2])
        sm_, sm2_ = f1(a)
        utt.assert_allclose(sm_, sm2_)

        # now show that the two versions result in the same crossentropy cost
        # this indicates that the forward function does provide some numerical
        # stability
        f2 = aesara.function([x, y], [cm, cm2], mode=m)
        cm_, cm2_ = f2(a, b)
        utt.assert_allclose(cm_, cm2_)

        # now, show that in the standard softmax case the gradients blow up
        # while in the log-softmax case they don't
        f3 = aesara.function([x, y], [grad])
        grad_ = f3(a, b)
        assert not np.any(np.isnan(grad_))

    def test_isclose(self):
        def f(a):
            return logsoftmax_op(a)

    def test_local_softmax_optimization(self):
        # Test the Logsoftmax substitution
        #
        # Check that Log(Softmax(x)) is substituted with Logsoftmax(x). Note that
        # only the forward pass is checked (i.e., doesn't check the gradient)

        x, y = tt.matrices("xy")
        sm = softmax(x)
        logsm = tt.log(sm)
        f = aesara.function([x], logsm)
        assert isinstance(f.maker.fgraph.outputs[0].owner.op, LogSoftmax)
        assert check_stack_trace(f, ops_to_check=LogSoftmax)

    def test_local_softmax_grad_optimization_and_big_input(self):
        # Test the Logsoftmax's grad substitution.
        #
        # Check that Log(Softmax(x))'s grad is substituted with Logsoftmax(x)'s
        # grad and that the new operation does not explode for big inputs.
        # Note that only the grad is checked.

        m = aesara.config.mode
        m = aesara.compile.get_mode(m)
        m.check_isfinite = False
        # some inputs that are large to make the gradient explode in the non
        # optimized case
        a = np.exp(10 * np.random.rand(5, 10).astype(aesara.config.floatX))

        def myfunc(x):
            sm = softmax(x)
            logsm = tt.log(sm)
            return logsm

        # We set step to 0.1 because for big values we need a big epsilon
        utt.verify_grad(myfunc, [a], eps=0.1, mode=m)
        sa = aesara.shared(a)
        f = aesara.function([], myfunc(sa))
        assert check_stack_trace(f, ops_to_check="all")

    def test_logsoftmax_grad_true_div_elemwise(self):
        # Checks that the gradient of an expression similar to a log(softmax)
        # but with a different elemwise operation than true_div is not
        # optimized.

        x = tt.matrix("x")
        y = tt.log(softmax(x))
        g = tt.grad(y.sum(), x)

        softmax_grad_node = g.owner
        assert softmax_grad_node.op == softmax_grad
        true_div_node = softmax_grad_node.inputs[0].owner
        assert true_div_node.op == tt.true_div

        # We replace the elemwise true_div op by an elemwise add.
        new_g = softmax_grad(tt.add(*true_div_node.inputs), softmax_grad_node.inputs[1])

        fgraph = gof.FunctionGraph([x], [new_g])
        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )

        assert softmax_grad in [n.op for n in fgraph.toposort()]


class TestSoftmaxGrad(utt.InferShapeTester):
    def test_infer_shape(self):
        admat = matrix()
        bdmat = matrix()
        admat_val = np.random.rand(3, 4).astype(config.floatX)
        bdmat_val = np.random.rand(3, 4).astype(config.floatX)
        self._compile_and_check(
            [admat, bdmat],
            [SoftmaxGrad()(admat, bdmat)],
            [admat_val, bdmat_val],
            SoftmaxGrad,
        )


class TestCrossentropySoftmax1Hot:
    def setup_method(self):
        utt.seed_rng()

    def test_basic(self):
        y_idx = [0, 1, 3]

        def f(a, b):
            return crossentropy_softmax_1hot_with_bias(a, b, y_idx)[0]

        utt.verify_grad(f, [np.random.rand(3, 4), np.random.rand(4)])

        y_idx = [0, 1, 3]

        def f(a):
            return crossentropy_softmax_1hot(a, y_idx)[0]

        utt.verify_grad(f, [np.random.rand(3, 4)])

    def test_vector(self):
        y_idx = [3]

        def f(a):
            return crossentropy_softmax_1hot(tt.shape_padleft(a), y_idx)[0]

        utt.verify_grad(f, [np.random.rand(4)])

    def test_vectors(self):
        y_idx = [3]

        def f(a, b):
            return crossentropy_softmax_1hot(tt.shape_padleft(a) + b, y_idx)[0]

        utt.verify_grad(f, [np.random.rand(4), np.random.rand(4)])


class TestCrossentropySoftmax1HotWithBiasDx(utt.InferShapeTester):
    def test_basic(self):
        def ff(class_dtype):
            def f(sm):
                # Class indices
                y = np.random.randint(low=0, high=5, size=10).astype(class_dtype)
                return crossentropy_softmax_1hot_with_bias_dx(
                    np.random.rand(10), sm, y  # Gradient w.r.t. NLL.  # Softmax output.
                )

            return f

        # Build a random softmax output whose rows sum to 1.
        softmax_output = np.random.rand(10, 5)
        softmax_output /= softmax_output.sum(axis=1).reshape(10, 1)
        for dtype in ["uint8", "int8", "uint64", "int64"]:
            utt.verify_grad(ff(dtype), [softmax_output])

    def test_basic_2(self):
        rng = np.random.RandomState(utt.fetch_seed())
        softmax_output = rng.rand(10, 5)
        softmax_output /= softmax_output.sum(axis=1).reshape(10, 1)

        def f(dy):
            return crossentropy_softmax_1hot_with_bias_dx(
                dy, softmax_output, rng.randint(low=0, high=5, size=10)
            )

        utt.verify_grad(f, [rng.rand(10)])

    def test_infer_shape(self):
        admat = matrix()
        advec = vector()
        alvec = lvector()
        rng = np.random.RandomState(utt.fetch_seed())
        admat_val = rng.rand(10, 5).astype(config.floatX)
        admat_val /= admat_val.sum(axis=1).reshape(10, 1)
        advec_val = rng.rand(10).astype(config.floatX)
        alvec_val = rng.randint(low=0, high=5, size=10)
        self._compile_and_check(
            [advec, admat, alvec],
            [CrossentropySoftmax1HotWithBiasDx()(advec, admat, alvec)],
            [advec_val, admat_val, alvec_val],
            CrossentropySoftmax1HotWithBiasDx,
        )

    def test_neg_idx(self):
        admat = matrix()
        advec = vector()
        alvec = lvector()
        rng = np.random.RandomState(utt.fetch_seed())
        admat_val = rng.rand(10, 5).astype(config.floatX)
        admat_val /= admat_val.sum(axis=1).reshape(10, 1)
        advec_val = rng.rand(10).astype(config.floatX)
        alvec_val = rng.randint(low=0, high=5, size=10)
        alvec_val[1] = -1
        out = CrossentropySoftmax1HotWithBiasDx()(advec, admat, alvec)
        f = aesara.function([advec, admat, alvec], out)
        with pytest.raises(ValueError):
            f(advec_val, admat_val, alvec_val)


class TestCrossentropySoftmaxArgmax1HotWithBias(utt.InferShapeTester):
    def setup_method(self):
        self.op = crossentropy_softmax_argmax_1hot_with_bias
        super().setup_method()

    def test_grads(self):
        n_classes = 5
        n_samples = 3

        # First test gradient when getting a gradient on the NLL output.
        def grad_on_nll_dtype(dtype):
            def grad_on_nll(x, b):
                y_idx = np.random.randint(low=0, high=n_classes, size=n_samples).astype(
                    dtype
                )
                return self.op(x, b, y_idx=y_idx)[0]

            return grad_on_nll

        for dtype in ["uint8", "int8", "uint64", "int64"]:
            utt.verify_grad(
                grad_on_nll_dtype(dtype),
                [np.random.rand(n_samples, n_classes), np.random.rand(n_classes)],
            )

        # Then test gradient when getting a gradient on the softmax output.
        def grad_on_softmax(x, b):
            return self.op(
                x, b, y_idx=np.random.randint(low=0, high=n_classes, size=n_samples)
            )[1]

        utt.verify_grad(
            grad_on_softmax,
            [np.random.rand(n_samples, n_classes), np.random.rand(n_classes)],
        )

    def test_infer_shape(self):
        admat = matrix()
        advec = vector()
        alvec = lvector()
        rng = np.random.RandomState(utt.fetch_seed())
        admat_val = rng.rand(3, 5).astype(config.floatX)
        advec_val = rng.rand(5).astype(config.floatX)
        alvec_val = rng.randint(low=0, high=5, size=3)
        self._compile_and_check(
            [admat, advec, alvec],
            CrossentropySoftmaxArgmax1HotWithBias()(admat, advec, alvec),
            [admat_val, advec_val, alvec_val],
            CrossentropySoftmaxArgmax1HotWithBias,
        )

    def test_neg_idx(self):
        admat = matrix()
        advec = vector()
        alvec = lvector()
        rng = np.random.RandomState(utt.fetch_seed())
        admat_val = rng.rand(3, 5).astype(config.floatX)
        advec_val = rng.rand(5).astype(config.floatX)
        alvec_val = rng.randint(low=0, high=5, size=3)
        alvec_val[1] = -1
        out = CrossentropySoftmaxArgmax1HotWithBias()(admat, advec, alvec)
        f = aesara.function([admat, advec, alvec], out)
        with pytest.raises(ValueError):
            f(admat_val, advec_val, alvec_val)


class TestPrepend(utt.InferShapeTester):
    def test_prepend_constant(self):
        x = tt.matrix("x")
        y = Prepend_scalar_constant_to_each_row(4.0)(x)
        f = aesara.function([x], y)
        m = np.random.rand(3, 5).astype(config.floatX)
        my = f(m)
        assert my.shape == (3, 6)
        assert np.all(my[:, 0] == 4.0)

    def test_prepend_basic(self):
        """Test basic functionality."""
        x = tt.matrix("x")
        y = Prepend_scalar_to_each_row()(5.0, x)
        f = aesara.function([x], y)
        m = np.ones((3, 5), dtype="float32")
        my = f(m)
        assert my.shape == (3, 6)
        assert np.all(my[:, 0] == 5.0)

    def test_infer_shape(self):
        admat = matrix()
        adscal = scalar()
        rng = np.random.RandomState(utt.fetch_seed())
        admat_val = rng.rand(3, 5).astype(config.floatX)
        adscal_val = np.asarray(rng.rand(), dtype=config.floatX).item()
        self._compile_and_check(
            [admat],
            [Prepend_scalar_constant_to_each_row(adscal_val)(admat)],
            [admat_val],
            Prepend_scalar_constant_to_each_row,
        )

        self._compile_and_check(
            [adscal, admat],
            [Prepend_scalar_to_each_row()(adscal, admat)],
            [adscal_val, admat_val],
            Prepend_scalar_to_each_row,
        )


class TestCrossentropyCategorical1HotGrad(utt.InferShapeTester):
    def test_infer_shape(self):
        advec = vector()
        admat = matrix()
        alvec = lvector()
        rng = np.random.RandomState(utt.fetch_seed())
        advec_val = rng.rand(3).astype(config.floatX)
        admat_val = rng.rand(3, 2).astype(config.floatX)
        alvec_val = [0, 1, 0]
        self._compile_and_check(
            [advec, admat, alvec],
            [CrossentropyCategorical1HotGrad()(advec, admat, alvec)],
            [advec_val, admat_val, alvec_val],
            CrossentropyCategorical1HotGrad,
        )


class TestCrossentropyCategorical1Hot(utt.InferShapeTester):
    def test_grad(self):
        x = tt.matrix("x")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        xe = op(x, one_of_n)
        f = aesara.function([x, one_of_n], xe)
        x_val = np.asarray([[0.4, 0.6, 0.0], [0.1, 0.8, 0.1]], dtype=config.floatX)
        xe_val = f(x_val, [0, 1])
        assert np.allclose(xe_val, -np.log([0.4, 0.8]))

        def oplike(x):
            return op(x, [0, 1])

        tt.verify_grad(oplike, [x_val], rng=np.random)

    def test_infer_shape(self):
        admat = matrix()
        alvec = lvector()
        rng = np.random.RandomState(utt.fetch_seed())
        admat_val = rng.rand(3, 2).astype(config.floatX)
        alvec_val = [0, 1, 0]
        self._compile_and_check(
            [admat, alvec],
            [CrossentropyCategorical1Hot()(admat, alvec)],
            [admat_val, alvec_val],
            CrossentropyCategorical1Hot,
        )

    def test_softmax_optimizations(self):
        x = tt.matrix("x")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        # xe = op(x, one_of_n)

        fgraph = gof.FunctionGraph([x, one_of_n], [op(softmax_op(x), one_of_n)])
        assert fgraph.outputs[0].owner.op == op

        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )
        assert fgraph.outputs[0].owner.op == crossentropy_softmax_argmax_1hot_with_bias

    def test_softmax_optimizations_vector(self):
        x = tt.vector("x")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        fgraph = gof.FunctionGraph([x, one_of_n], [op(softmax_op(x), one_of_n)])
        assert fgraph.outputs[0].owner.op == op

        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )
        assert fgraph.outputs[0].owner.op == crossentropy_softmax_argmax_1hot_with_bias

    def test_softmax_optimizations_w_bias(self):
        x = tt.matrix("x")
        b = tt.vector("b")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        # xe = op(x, one_of_n)

        fgraph = gof.FunctionGraph([x, b, one_of_n], [op(softmax_op(x + b), one_of_n)])
        assert fgraph.outputs[0].owner.op == op

        # print 'BEFORE'
        # for node in fgraph.toposort():
        #    print node.op
        # print printing.pprint(node.outputs[0])
        # print '----'

        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )

        # print 'AFTER'
        # for node in fgraph.toposort():
        #    print node.op
        # print printing.pprint(node.outputs[0])
        # print '===='
        assert len(fgraph.toposort()) == 1
        assert fgraph.outputs[0].owner.op == crossentropy_softmax_argmax_1hot_with_bias

    def test_softmax_optimizations_w_bias2(self):
        x = tt.matrix("x")
        b = tt.vector("b")
        c = tt.vector("c")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot

        fgraph = gof.FunctionGraph(
            [x, b, c, one_of_n], [op(softmax_op(tt.add(x, b, c)), one_of_n)]
        )
        assert fgraph.outputs[0].owner.op == op

        # print 'BEFORE'
        # for node in fgraph.toposort():
        #    print node.op
        # print '----'

        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )

        # print 'AFTER'
        # for node in fgraph.toposort():
        #    print node.op
        # print '===='
        assert len(fgraph.toposort()) == 2
        assert fgraph.outputs[0].owner.op == crossentropy_softmax_argmax_1hot_with_bias

    def test_softmax_optimizations_w_bias_vector(self):
        x = tt.vector("x")
        b = tt.vector("b")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        fgraph = gof.FunctionGraph([x, b, one_of_n], [op(softmax_op(x + b), one_of_n)])
        assert fgraph.outputs[0].owner.op == op
        # print 'BEFORE'
        # for node in fgraph.toposort():
        #    print node.op
        # print printing.pprint(node.outputs[0])
        # print '----'

        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )
        # print 'AFTER'
        # for node in fgraph.toposort():
        #    print node.op
        # print '===='
        assert len(fgraph.toposort()) == 2
        assert fgraph.outputs[0].owner.op == crossentropy_softmax_argmax_1hot_with_bias

    def test_softmax_grad_optimizations(self):
        x = tt.matrix("x")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        xe = op(softmax_op(x), one_of_n)
        sum_xe = tt.sum(xe)
        g_x = tt.grad(sum_xe, x)
        fgraph = gof.FunctionGraph([x, one_of_n], [g_x])
        assert check_stack_trace(
            fgraph, ops_to_check=[crossentropy_softmax_1hot_with_bias_dx, softmax_op]
        )

        # print 'BEFORE'
        # for node in fgraph.toposort():
        #    print node.op, node.inputs
        # print '----'
        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )

        # print 'AFTER'
        # for node in fgraph.toposort():
        #    print node.op, node.inputs

        has_cx1hot = False
        has_cx1hotdx = False
        has_softmax = False
        has_softmaxdx = False
        for node in fgraph.toposort():
            if node.op == crossentropy_softmax_argmax_1hot_with_bias:
                has_cx1hot = True
            if node.op == crossentropy_softmax_1hot_with_bias_dx:
                has_cx1hotdx = True
            if node.op == softmax_op:
                has_softmax = True
            if node.op == softmax_grad:
                has_softmaxdx = True
        assert not has_cx1hot
        assert has_cx1hotdx
        assert has_softmax
        assert not has_softmaxdx

    def test_softmax_grad_optimizations_vector(self):
        x = tt.vector("x")
        one_of_n = tt.lvector("one_of_n")
        op = crossentropy_categorical_1hot
        xe = op(softmax_op(x), one_of_n)
        sum_xe = tt.sum(xe)
        g_x = tt.grad(sum_xe, x)
        fgraph = gof.FunctionGraph([x, one_of_n], [g_x])

        # print 'BEFORE'
        # for node in fgraph.toposort():
        #    print node.op, node.inputs
        # print '----'
        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )

        # print 'AFTER'
        # for node in fgraph.toposort():
        #    print node.op, node.inputs

        has_cx1hot = False
        has_cx1hotdx = False
        has_softmax = False
        has_softmaxdx = False
        for node in fgraph.toposort():
            if node.op == crossentropy_softmax_argmax_1hot_with_bias:
                has_cx1hot = True
            if node.op == crossentropy_softmax_1hot_with_bias_dx:
                has_cx1hotdx = True
            if node.op == softmax_op:
                has_softmax = True
            if node.op == softmax_grad:
                has_softmaxdx = True
        assert not has_cx1hot
        assert has_cx1hotdx
        assert has_softmax
        assert not has_softmaxdx

    def test_get_rid_of_advanced_indexing_version_of_xent(self):
        verbose = 0
        # TODO: add the optimization in FAST_COMPILE?
        # In the mean time, run it as 'FAST_RUN' instead
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(3, 5).astype(config.floatX)
        b_val = rng.randn(5).astype(config.floatX)
        y_val = np.asarray([2, 4, 1])
        x = tt.matrix("x")
        b = tt.vector("b")
        y = tt.lvector("y")

        # Basic case
        expressions = [
            tt.sum(-tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            tt.sum(-tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
        ]
        for expr in expressions:
            # Verify the optimizer worked on the expressions
            f = aesara.function([x, y], expr, mode=mode)
            # todo: only the first output of the op has a stack trace
            # assert check_stack_trace(
            #     f, ops_to_check=crossentropy_softmax_argmax_1hot_with_bias)
            if verbose:
                aesara.printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                assert len(ops) == 4
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            # Also verify the gradient wrt x
            g = aesara.function([x, y], tt.grad(expr, x), mode=mode)
            assert check_stack_trace(
                g, ops_to_check=[crossentropy_softmax_1hot_with_bias_dx, softmax_op]
            )
            if verbose:
                aesara.printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) == 2
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_op in ops
                assert softmax_grad not in ops
                g(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

        # Test that a biased softmax is optimized correctly
        bias_expressions = [
            tt.sum(-tt.log(softmax(x + b)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(b + x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x + b))[tt.arange(y.shape[0]), y]),
            tt.sum(-tt.log(softmax(b + x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in bias_expressions:
            f = aesara.function([x, b, y], expr, mode=mode)
            # todo: only the first output of the op has a stack trace
            # assert check_stack_trace(
            #     f, ops_to_check=crossentropy_softmax_argmax_1hot_with_bias)
            if verbose:
                aesara.printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                assert len(ops) == 2  # [big_op, sum]
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                f(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise
            g = aesara.function([x, b, y], tt.grad(expr, x), mode=mode)
            assert check_stack_trace(
                g,
                ops_to_check=[
                    crossentropy_softmax_1hot_with_bias_dx,
                    softmax_with_bias,
                ],
            )
            if verbose:
                aesara.printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) == 2
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_with_bias in ops
                assert softmax_grad not in ops
                g(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

        # Test that using "mean" instead of sum works, too
        mean_expressions = [
            tt.mean(-tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -tt.mean(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -tt.mean(tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            tt.mean(-tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in mean_expressions:
            f = aesara.function([x, y], expr, mode=mode)
            # todo: only the first output of the op has a stack trace
            # assert check_stack_trace(
            #     f, ops_to_check=[crossentropy_softmax_argmax_1hot_with_bias])
            if verbose:
                aesara.printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                assert len(ops) == 6
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            g = aesara.function([x, y], tt.grad(expr, x), mode=mode)
            assert check_stack_trace(
                g, ops_to_check=[crossentropy_softmax_1hot_with_bias_dx, softmax_op]
            )
            if verbose:
                aesara.printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) == 5
                # there's an extra dimshuffle in there
                # but I can't think of a good rule to get rid of it
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_op in ops
                assert softmax_grad not in ops
                g(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

        mean_bias_expressions = [
            tt.mean(-tt.log(softmax(x + b)[tt.arange(y.shape[0]), y])),
            -tt.mean(tt.log(softmax(b + x)[tt.arange(y.shape[0]), y])),
            -tt.mean(tt.log(softmax(x + b))[tt.arange(y.shape[0]), y]),
            tt.mean(-tt.log(softmax(b + x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in mean_bias_expressions:
            f = aesara.function([x, b, y], expr, mode=mode)
            # todo: only the first output of the op has a stack trace
            # assert check_stack_trace(
            #     f, ops_to_check=crossentropy_softmax_argmax_1hot_with_bias)
            if verbose:
                aesara.printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                assert len(ops) == 4
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
            except Exception:
                aesara.printing.debugprint(f)
                raise
            g = aesara.function([x, b, y], tt.grad(expr, x), mode=mode)
            assert check_stack_trace(
                g,
                ops_to_check=[
                    crossentropy_softmax_1hot_with_bias_dx,
                    softmax_with_bias,
                ],
            )
            if verbose:
                aesara.printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) == 5
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_with_bias in ops
                assert softmax_grad not in ops
                g(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

    def test_xent_thing_int32(self):
        verbose = 0
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(3, 5).astype(config.floatX)
        y_val = np.asarray([2, 4, 1], dtype="int64")
        x = tt.matrix("x")
        y = tt.lvector("y")
        yi = tt.cast(y, "int32")
        expressions = [
            tt.sum(-tt.log(softmax(x)[tt.arange(yi.shape[0]), yi])),
            -tt.sum(tt.log(softmax(x)[tt.arange(yi.shape[0]), yi])),
            -tt.sum(tt.log(softmax(x))[tt.arange(yi.shape[0]), yi]),
            tt.sum(-tt.log(softmax(x))[tt.arange(yi.shape[0]), yi]),
        ]

        for expr in expressions:
            # Verify the optimizer worked on the expressions
            f = aesara.function([x, y], expr, mode=mode)
            if verbose:
                aesara.printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                assert len(ops) == 5
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            # Also verify the gradient wrt x
            g = aesara.function([x, y], tt.grad(expr, x), mode=mode)
            if verbose:
                aesara.printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) == 3
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_op in ops
                assert softmax_grad not in ops
                g(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

    def test_optimize_xent_vector(self):
        verbose = 0
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(5).astype(config.floatX)
        y_val = np.asarray([2])

        x = tt.vector("x")
        y = tt.lvector("y")

        # Test that a biased softmax is optimized correctly
        bias_expressions = [
            tt.sum(-tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
        ]

        for expr in bias_expressions:
            f = aesara.function([x, y], expr, mode=mode)
            if verbose:
                printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                assert len(ops) == 5
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise
            g = aesara.function([x, y], tt.grad(expr, x), mode=mode)
            if verbose:
                printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) == 4
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_op in ops
                assert softmax_grad not in ops
                g(x_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

    def test_optimize_xent_vector2(self):
        verbose = 0
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(5).astype(config.floatX)
        b_val = rng.randn(5).astype(config.floatX)
        y_val = np.asarray([2])

        x = tt.vector("x")
        b = tt.vector("b")
        y = tt.lvector("y")

        # Test that a biased softmax is optimized correctly
        bias_expressions = [
            tt.sum(-tt.log(softmax(x + b)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(b + x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x + b))[tt.arange(y.shape[0]), y]),
            tt.sum(-tt.log(softmax(b + x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in bias_expressions:
            f = aesara.function([x, b, y], expr, mode=mode)
            if verbose:
                printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                # [big_op, sum, dim_shuffle]
                assert len(ops) == 3
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            backup = config.warn.sum_div_dimshuffle_bug
            config.warn.sum_div_dimshuffle_bug = False
            try:
                g = aesara.function([x, b, y], tt.grad(expr, x), mode=mode)
            finally:
                config.warn.sum_div_dimshuffle_bug = backup

            if verbose:
                printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) <= 6
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_with_bias in ops
                assert softmax_grad not in ops
                g(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

    def test_optimize_xent_vector3(self):
        # Same as test_optimize_xent_vector2, but y is the result of
        # a "flatten", and it used to make the constant-folding
        # of arange(y.shape[0]) happen before the xent optimization
        verbose = 0
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(5).astype(config.floatX)
        b_val = rng.randn(5).astype(config.floatX)
        y_val = np.asarray([2])

        x = tt.vector("x")
        b = tt.vector("b")
        y_ = tt.lvector("y_")
        y = y_.flatten()

        # Test that a biased softmax is optimized correctly
        bias_expressions = [
            tt.sum(-tt.log(softmax(x + b)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(b + x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x + b))[tt.arange(y.shape[0]), y]),
            tt.sum(-tt.log(softmax(b + x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in bias_expressions:
            f = aesara.function([x, b, y_], expr, mode=mode)
            if verbose:
                printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                # [big_op, sum, dim_shuffle, flatten]
                assert len(ops) <= 4
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            backup = config.warn.sum_div_dimshuffle_bug
            config.warn.sum_div_dimshuffle_bug = False
            try:
                g = aesara.function([x, b, y], tt.grad(expr, x), mode=mode)
            finally:
                config.warn.sum_div_dimshuffle_bug = backup

            if verbose:
                printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) <= 6
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_with_bias in ops
                assert softmax_grad not in ops
                g(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

    def test_optimize_xent_vector4(self):
        # Same as test_optimize_xent_vector2, but y is the result of
        # a "specify_shape" that indicates its length is 1, so the
        # constant-folding of arange(y.shape[0]) happen before the xent
        # optimization
        verbose = 0
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(5).astype(config.floatX)
        b_val = rng.randn(5).astype(config.floatX)
        y_val = np.asarray([2])

        x = tt.vector("x")
        b = tt.vector("b")
        y_ = tt.lvector("y_")
        y = tt.specify_shape(y_, (1,))

        # Test that a biased softmax is optimized correctly
        bias_expressions = [
            tt.sum(-tt.log(softmax(x + b)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(b + x)[tt.arange(y.shape[0]), y])),
            -tt.sum(tt.log(softmax(x + b))[tt.arange(y.shape[0]), y]),
            tt.sum(-tt.log(softmax(b + x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in bias_expressions:
            f = aesara.function([x, b, y_], expr, mode=mode)
            if verbose:
                printing.debugprint(f)
            try:
                ops = [node.op for node in f.maker.fgraph.toposort()]
                # [big_op, sum, dim_shuffle, specify_shape]
                assert len(ops) <= 4
                assert crossentropy_softmax_argmax_1hot_with_bias in ops
                assert not [1 for o in ops if isinstance(o, tt.AdvancedSubtensor)]
                f(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            backup = config.warn.sum_div_dimshuffle_bug
            config.warn.sum_div_dimshuffle_bug = False
            try:
                g = aesara.function([x, b, y], tt.grad(expr, x), mode=mode)
            finally:
                config.warn.sum_div_dimshuffle_bug = backup

            if verbose:
                printing.debugprint(g)
            try:
                ops = [node.op for node in g.maker.fgraph.toposort()]
                assert len(ops) <= 6
                assert crossentropy_softmax_1hot_with_bias_dx in ops
                assert softmax_with_bias in ops
                assert softmax_grad not in ops
                g(x_val, b_val, y_val)
            except Exception:
                aesara.printing.debugprint(g)
                raise

    def test_crossentropy_softmax_1hot_with_bias_dxcale_cost(self):
        # TODO: add the optimization in FAST_COMPILE?
        # In the mean time, run it as 'FAST_RUN' instead
        mode = aesara.compile.mode.get_default_mode()
        if mode == aesara.compile.mode.get_mode("FAST_COMPILE"):
            mode = "FAST_RUN"
        rng = np.random.RandomState(utt.fetch_seed())
        x_val = rng.randn(3, 5).astype(config.floatX)
        y_val = np.asarray([2, 4, 1])
        x = tt.matrix("x")
        y = tt.lvector("y")
        a = tt.scalar("a")

        def validate_fn_graph(func):
            # The graph of the function should not have softmax anymore
            has_cx1hot = False
            has_softmax = False
            for node in func.maker.fgraph.toposort():
                if node.op == crossentropy_softmax_argmax_1hot_with_bias:
                    has_cx1hot = True
                if node.op == softmax_op:
                    has_softmax = True

            assert has_cx1hot
            assert not has_softmax

        def validate_grad_graph(func):
            # The graph of the gradient should not have softmaxgrad anymore
            has_cx1hotdx = False
            has_softmax = False
            has_softmaxdx = False
            for node in func.maker.fgraph.toposort():
                if node.op == crossentropy_softmax_1hot_with_bias_dx:
                    has_cx1hotdx = True
                if node.op == softmax_op:
                    has_softmax = True
                if node.op == softmax_grad:
                    has_softmaxdx = True

            assert has_cx1hotdx
            assert has_softmax
            assert not has_softmaxdx

        # Cases to test
        expressions = [
            a * tt.sum(-tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -a * tt.sum(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            a * (-tt.sum(tt.log(softmax(x)[tt.arange(y.shape[0]), y]))),
            a * tt.sum(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            a * tt.sum(-tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            -a * tt.sum(tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            a * (-tt.sum(tt.log(softmax(x))[tt.arange(y.shape[0]), y])),
            a * tt.sum(tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            a * tt.mean(-tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            -a * tt.mean(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            a * (-tt.mean(tt.log(softmax(x)[tt.arange(y.shape[0]), y]))),
            a * tt.mean(tt.log(softmax(x)[tt.arange(y.shape[0]), y])),
            a * tt.mean(-tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            -a * tt.mean(tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
            a * (-tt.mean(tt.log(softmax(x))[tt.arange(y.shape[0]), y])),
            a * tt.mean(tt.log(softmax(x))[tt.arange(y.shape[0]), y]),
        ]

        for expr in expressions:
            # Verify the optimizer worked on the expressions
            f = aesara.function([x, y, a], expr, mode=mode)
            try:
                assert 5 <= len(f.maker.fgraph.toposort()) <= 10
                validate_fn_graph(f)
                f(x_val, y_val, 0.1)
            except Exception:
                aesara.printing.debugprint(f)
                raise

            # Verify the gradient wrt x
            g = aesara.function([x, y, a], tt.grad(expr, x), mode=mode)
            try:
                assert 3 <= len(g.maker.fgraph.toposort()) <= 6
                validate_grad_graph(g)
                g(x_val, y_val, 0.1)
            except Exception:
                aesara.printing.debugprint(g)
                raise

            # Verify the gradient when providing output gradient
            h = aesara.function(
                [x, y, a], tt.grad(expr, x, known_grads={expr: a * x.sum()}), mode=mode
            )
            try:
                assert 6 <= len(h.maker.fgraph.toposort()) <= 8
                validate_grad_graph(h)
                h(x_val, y_val, 0.1)
            except Exception:
                aesara.printing.debugprint(h)
                raise


def test_argmax_pushdown():
    x = tt.matrix()
    for sm in [softmax_graph, softmax_op]:
        # test that the max_and_argmax is pushed down if the max is not used
        out = tt.max_and_argmax(sm(tt.exp(tt.tanh(sigmoid(x)))), axis=-1)[1]
        fgraph = gof.FunctionGraph([x], [out])
        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )

        # print 'AFTER'
        # for node in fgraph.toposort():
        # print node.op
        assert len(fgraph.toposort()) == 1
        assert isinstance(fgraph.toposort()[0].op, tt.Argmax)
        assert check_stack_trace(fgraph, ops_to_check=tt.Argmax)
        x = tt.matrix()
        # test that the max_and_argmax is not pushed down if the max is used
        out = tt.max_and_argmax(sm(tt.exp(tt.tanh(sigmoid(x)))), axis=-1)[0]
        fgraph = gof.FunctionGraph([x], [out])

        assert hasattr(fgraph.outputs[0].tag, "trace")
        backup = config.warn.argmax_pushdown_bug
        config.warn.argmax_pushdown_bug = False
        try:
            aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
                fgraph
            )
        finally:
            config.warn.argmax_pushdown_bug = backup

        # print 'AFTER'
        # for node in fgraph.toposort():
        # print node.op
        assert len(fgraph.toposort()) == 3
        assert isinstance(fgraph.toposort()[0].op, tt.Elemwise)
        assert isinstance(fgraph.toposort()[1].op, Softmax)
        assert isinstance(fgraph.toposort()[2].op, tt.CAReduce)
        assert isinstance(fgraph.toposort()[2].op.scalar_op, aesara.scalar.Maximum)


def test_argmax_pushdown_bias():
    x = tt.matrix()
    b = tt.vector()

    out = tt.argmax(softmax_with_bias(x, b), axis=-1)
    fgraph = gof.FunctionGraph([x, b], [out])

    aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(fgraph)

    # print 'AFTER'
    # for node in fgraph.toposort():
    #    print node.op
    types_to_check = (tt.DimShuffle, tt.Elemwise, tt.Argmax)
    assert len(fgraph.toposort()) == 3

    for i, type in enumerate(types_to_check):
        assert isinstance(fgraph.toposort()[i].op, type)
    assert check_stack_trace(fgraph, ops_to_check=types_to_check)

    x = tt.matrix()
    b = tt.vector()
    out = tt.max_and_argmax(softmax_with_bias(x, b), axis=-1)[0]
    fgraph = gof.FunctionGraph([x, b], [out])

    backup = config.warn.argmax_pushdown_bug
    config.warn.argmax_pushdown_bug = False
    try:
        aesara.compile.mode.optdb.query(aesara.compile.mode.OPT_FAST_RUN).optimize(
            fgraph
        )
    finally:
        config.warn.argmax_pushdown_bug = backup

    # print 'AFTER'
    # for node in fgraph.toposort():
    #    print node.op
    assert len(fgraph.toposort()) == 2
    assert isinstance(fgraph.toposort()[0].op, SoftmaxWithBias)
    assert isinstance(fgraph.toposort()[1].op, tt.CAReduce)
    assert isinstance(fgraph.toposort()[1].op.scalar_op, aesara.scalar.Maximum)
    assert check_stack_trace(fgraph, ops_to_check=(SoftmaxWithBias, tt.CAReduce))


def test_asymptotic_32():
    # This test makes sure that our functions behave sensibly when
    # huge values are present

    # TODO: consider adding the optimization of crossentropy into the current
    # mode for the purpose of running this test

    for dtype in "float32", "float64":
        if dtype == "float32":
            x = tt.fmatrix()
            x2 = tt.fvector()
        else:
            x = tt.dmatrix()
            x2 = tt.dvector()
        y = tt.lvector()

        c = categorical_crossentropy(softmax(x + x2), y)
        f = aesara.function([x, y, x2], [c.sum(), tt.grad(c.sum(), x)], mode="FAST_RUN")

        xval = np.zeros((5, 5), dtype=dtype).astype(dtype)
        x2val = np.zeros(5, dtype=xval.dtype).astype(dtype)
        for i in range(100):
            cval, gxval = f(xval, np.arange(5), x2val)
            xval -= 100.3 * gxval
            # print cval, gxval
        assert cval == 0  # no problem going to zero error

        # what about when x gets really big?

        xval = np.zeros((5, 5), dtype=dtype)
        x2val = np.zeros(5, dtype=xval.dtype)
        for i in range(100):

            cval, gxval = f(xval, np.arange(5), x2val)
            xval += 100000.3 * gxval
            # print cval, gxval

        assert cval > 61750000
        assert gxval[0, 0] == -1.0
        assert gxval[0, 1] == 0.25


class TestSoftmaxOpt:
    # Test that expressions of softmax in terms of exponentiated things
    # divided by row sums are replaced by softmax expressions.
    #
    # Softmax_grad isn't that interesting as an Op, but it has the signature
    # we look for when trying to insert CrossEntropySoftmax... grad.  So, for
    # now, we add softmax_grad to graphs. In the future, we may modify the
    # CrossEntropySoftmax...grad to look for the more basic pattern.
    #

    def setup_method(self):
        utt.seed_rng()
        self.rng = np.random.RandomState(utt.fetch_seed())
        self.mode = aesara.compile.mode.get_default_mode()
        self.mode = self.mode.including("canonicalize")

    def test_basic(self):
        c = tt.matrix()
        p_y = tt.exp(c) / tt.exp(c).sum(axis=1).dimshuffle(0, "x")

        # test that function contains softmax and no div.
        f = aesara.function([c], p_y, mode=self.mode)

        assert check_stack_trace(f, ops_to_check=softmax_op)

        f_ops = [n.op for n in f.maker.fgraph.toposort()]
        # print '--- f ='
        # printing.debugprint(f)
        # print '==='
        assert len(f_ops) == 1
        assert softmax_op in f_ops
        f(self.rng.rand(3, 4).astype(config.floatX))

    def test_basic_keepdims(self):
        c = tt.matrix()
        p_y = tt.exp(c) / tt.exp(c).sum(axis=1, keepdims=True)

        # test that function contains softmax and no div.
        f = aesara.function([c], p_y, mode=self.mode)

        assert check_stack_trace(f, ops_to_check=softmax_op)

        f_ops = [n.op for n in f.maker.fgraph.toposort()]
        # print '--- f ='
        # printing.debugprint(f)
        # print '==='
        assert len(f_ops) == 1
        assert softmax_op in f_ops
        f(self.rng.rand(3, 4).astype(config.floatX))

    @pytest.mark.skip(reason="Optimization not enabled for the moment")
    def test_grad(self):
        c = tt.matrix()
        p_y = tt.exp(c) / tt.exp(c).sum(axis=1).dimshuffle(0, "x")

        # test that function contains softmax and softmaxgrad
        w = tt.matrix()
        backup = config.warn.sum_div_dimshuffle_bug
        config.warn.sum_div_dimshuffle_bug = False
        try:
            g = aesara.function([c, w], tt.grad((p_y * w).sum(), c))
        finally:
            config.warn.sum_div_dimshuffle_bug = backup
        g_ops = [n.op for n in g.maker.fgraph.toposort()]
        # print '--- g ='
        # printing.debugprint(g)
        # print '==='

        assert len(g_ops) == 2
        assert softmax_op in g_ops
        assert softmax_grad in g_ops
        g(self.rng.rand(3, 4), self.rng.uniform(0.5, 1, (3, 4)))

    @pytest.mark.skip(reason="Optimization not enabled for the moment")
    def test_transpose_basic(self):
        # this should be a transposed softmax
        c = tt.matrix()
        p_y = tt.exp(c) / tt.exp(c).sum(axis=0)

        # test that function contains softmax and no div.
        aesara.function([c], p_y)
        # printing.debugprint(f)

        # test that function contains softmax and no div.
        backup = config.warn.sum_div_dimshuffle_bug
        config.warn.sum_div_dimshuffle_bug = False
        try:
            aesara.function([c], tt.grad(p_y.sum(), c))
        finally:
            config.warn.sum_div_dimshuffle_bug = backup
        # printing.debugprint(g)

    @pytest.mark.skip(reason="Optimization not enabled for the moment")
    def test_1d_basic(self):
        # this should be a softmax, but of a one-row matrix
        c = tt.vector()
        p_y = tt.exp(c) / tt.exp(c).sum()

        # test that function contains softmax and no div.
        aesara.function([c], p_y)
        # printing.debugprint(f)

        # test that function contains softmax and no div.
        backup = config.warn.sum_div_dimshuffle_bug
        config.warn.sum_div_dimshuffle_bug = False
        try:
            aesara.function([c], tt.grad(p_y.sum(), c))
        finally:
            config.warn.sum_div_dimshuffle_bug = backup
        # printing.debugprint(g)

    # REPEAT 3 CASES in presence of log(softmax) with the advanced indexing
    # etc.


def test_softmax_graph():
    rng = np.random.RandomState(utt.fetch_seed())
    x = aesara.shared(rng.normal(size=(3, 4)))

    def f(inputs):
        y = softmax_graph(x)
        return aesara.grad(None, x, known_grads={y: inputs})

    utt.verify_grad(f, [rng.rand(3, 4)])


def test_grad_softmax_grad():
    rng = np.random.RandomState(utt.fetch_seed())
    x = aesara.shared(rng.normal(size=(3, 4)))

    def f(inputs):
        y = softmax_op(x)
        return aesara.grad(None, x, known_grads={y: inputs})

    utt.verify_grad(f, [rng.rand(3, 4)])


def test_stabilize_log_softmax():
    mode = aesara.compile.mode.get_default_mode()
    mode = mode.including("local_log_softmax", "specialize")

    x = matrix()
    y = softmax(x)
    z = tt.log(y)

    f = aesara.function([x], z, mode=mode)
    assert check_stack_trace(f, ops_to_check="all")

    # check that the softmax has been optimized out
    for node in f.maker.fgraph.toposort():
        assert not isinstance(node.op, y.owner.op.__class__)

    # call the function so debug mode can verify the optimized
    # version matches the unoptimized version
    rng = np.random.RandomState([2012, 8, 22])
    f(np.cast[config.floatX](rng.randn(2, 3)))


def test_relu():
    x = matrix("x")
    seed = utt.fetch_seed()
    rng = np.random.RandomState(seed)
    X = rng.randn(20, 30).astype(config.floatX)

    # test the base case, without custom alpha value
    y = relu(x).eval({x: X})
    assert np.allclose(y, np.maximum(X, 0))

    # test for different constant alpha values (also outside of [0, 1])
    for alpha in 0, 0.3, 1, 2, -0.3, -1, -2:
        y = relu(x, alpha).eval({x: X})
        assert np.allclose(y, np.where(X > 0, X, alpha * X))

    # test for variable alpha (scalar, vector and matrix)
    for alpha in scalar(), vector(), matrix():
        # create value for alpha (correct ndim and broadcastable against X)
        A = np.array(rng.randn(*X.shape[::-1][: alpha.ndim][::-1]), dtype=config.floatX)
        y = relu(x, alpha).eval({x: X, alpha: A})
        assert np.allclose(y, np.where(X > 0, X, A * X), rtol=3e-5)
        # test that for alpha of ndarray don't cause upcast.
        x = matrix("x", dtype="float32")
        rng = np.random.RandomState(seed)
        X = rng.randn(20, 30).astype("float32")
        alpha = np.asarray(0.123, dtype="float32")
        y = relu(x, alpha).eval({x: X})
        assert np.allclose(y, np.where(X > 0, X, alpha * X))
        assert y.dtype == "float32"


def test_h_softmax():
    # Tests the output dimensions of the h_softmax when a target is provided or
    # not.

    #############
    # Config
    #############

    input_size = 4
    batch_size = 2
    h_softmax_level1_size = 5
    h_softmax_level2_size = 3
    output_size = h_softmax_level1_size * h_softmax_level2_size

    #############
    # Initialize shared variables
    #############

    floatX = aesara.config.floatX
    shared = aesara.shared

    # First level of h_softmax
    W1 = np.asarray(
        np.random.normal(size=(input_size, h_softmax_level1_size)), dtype=floatX
    )
    W1 = shared(W1)
    b1 = shared(np.asarray(np.zeros((h_softmax_level1_size,)), dtype=floatX))

    # Second level of h_softmax
    W2 = np.asarray(
        np.random.normal(
            size=(h_softmax_level1_size, input_size, h_softmax_level2_size)
        ),
        dtype=floatX,
    )
    W2 = shared(W2)
    b2 = shared(
        np.asarray(
            np.zeros((h_softmax_level1_size, h_softmax_level2_size)), dtype=floatX
        )
    )

    #############
    # Build graph
    #############
    x = tt.matrix("x")
    y = tt.ivector("y")

    # This only computes the output corresponding to the target
    y_hat_tg = h_softmax(
        x,
        batch_size,
        output_size,
        h_softmax_level1_size,
        h_softmax_level2_size,
        W1,
        b1,
        W2,
        b2,
        y,
    )

    # This computes all the outputs
    y_hat_all = h_softmax(
        x,
        batch_size,
        output_size,
        h_softmax_level1_size,
        h_softmax_level2_size,
        W1,
        b1,
        W2,
        b2,
    )

    #############
    # Compile functions
    #############
    fun_output_tg = aesara.function([x, y], y_hat_tg)
    fun_output = aesara.function([x], y_hat_all)

    #############
    # Test
    #############
    x_mat = np.random.normal(size=(batch_size, input_size)).astype(floatX)
    y_mat = np.random.randint(0, output_size, batch_size).astype("int32")
    tg_output = fun_output_tg(x_mat, y_mat)
    all_outputs = fun_output(x_mat)

    assert tg_output.shape == (batch_size,)
    assert all_outputs.shape == (batch_size, output_size)

    # Verifies that the outputs computed by fun_output_tg are the same as those
    # computed by fun_output.
    utt.assert_allclose(all_outputs[np.arange(0, batch_size), y_mat], tg_output)


def test_elu():
    x = matrix("x")
    seed = utt.fetch_seed()
    rng = np.random.RandomState(seed)
    X = rng.randn(20, 30).astype(config.floatX)

    # test the base case, without custom alpha value
    y = elu(x).eval({x: X})
    utt.assert_allclose(y, np.where(X > 0, X, np.exp(X) - 1))

    # test for different constant alpha values
    for alpha in 1.5, 2, -1, -1.5, -2:
        y = elu(x, alpha).eval({x: X})
        utt.assert_allclose(y, np.where(X > 0, X, alpha * (np.exp(X) - 1)))


def test_selu():
    alpha = 1.6732632423543772848170429916717
    scale = 1.0507009873554804934193349852946

    x = matrix("x")
    seed = utt.fetch_seed()
    rng = np.random.RandomState(seed)
    X = rng.randn(20, 30).astype(config.floatX)

    y = selu(x).eval({x: X})
    utt.assert_allclose(y, np.where(X > 0, scale * X, scale * alpha * (np.exp(X) - 1)))


def test_binary_crossentropy_reshape():
    # Reported as https://github.com/Aesara/Aesara/issues/4086
    a = tt.tensor4("a")
    for c in (
        binary_crossentropy(sigmoid(a.reshape((-1, 1))), 1).sum(),
        binary_crossentropy(sigmoid(a).reshape((-1, 1)), 1).sum(),
    ):

        ga = aesara.grad(c, a)
        # This only works when "specialize" options are included
        mode = aesara.compile.get_default_mode().including("fast_run")
        fga = aesara.function([a], ga, mode=mode)
        utt.assert_allclose(
            fga(np.array([[[[30.0]]]], dtype=config.floatX)),
            np.zeros((1, 1, 1, 1), dtype=config.floatX),
        )


TestSoftsign = makeBroadcastTester(
    op=softsign,
    expected=upcast_int8_nfunc(
        lambda inputs: check_floatX(inputs, inputs / (1.0 + np.fabs(inputs)))
    ),
    good=_good_broadcast_unary_normal_float_no_complex,
    name="SoftsignTester",
)


class TestSigmoidBinaryCrossentropy:
    def setup_method(self):
        utt.seed_rng()

    def _get_test_inputs(self, n=50):
        pred, target = np.random.randn(2, n).astype(config.floatX)
        # apply sigmoid to target, but not pred
        return [pred, 1 / (1 + np.exp(-target))]

    def test_matches_binary_crossentropy(self):
        # Test sigmoid_binary_crossentropy(p, t) ==
        #      binary_crossentropy(sigmoid(p), t).

        pred, target = inputs = tt.vectors("pt")

        reference_val = binary_crossentropy(sigmoid(pred), target)
        f_reference = aesara.function(inputs, reference_val)

        test_val = sigmoid_binary_crossentropy(pred, target)
        f_test = aesara.function(inputs, test_val)

        test_inputs = self._get_test_inputs()
        utt.assert_allclose(f_reference(*test_inputs), f_test(*test_inputs))

    def test_grad(self):
        utt.verify_grad(sigmoid_binary_crossentropy, self._get_test_inputs())


def test_confusion_matrix():
    # Defining numpy implementation of confusion matrix
    def numpy_conf_mat(actual, pred):
        order = np.union1d(actual, pred)
        colA = np.matrix(actual).T
        colP = np.matrix(pred).T
        oneHotA = colA.__eq__(order).astype("int64")
        oneHotP = colP.__eq__(order).astype("int64")
        conf_mat = np.dot(oneHotA.T, oneHotP)
        conf_mat = np.asarray(conf_mat)
        return [conf_mat, order]

    x = tt.vector()
    y = tt.vector()
    f = aesara.function([x, y], confusion_matrix(x, y))
    list_inputs = [
        [[0, 1, 2, 1, 0], [0, 0, 2, 1, 2]],
        [[2, 0, 2, 2, 0, 1], [0, 0, 2, 2, 0, 2]],
    ]

    for case in list_inputs:
        a = np.asarray(case[0])
        b = np.asarray(case[1])
        out_exp = numpy_conf_mat(a, b)
        outs = f(case[0], case[1])
        for exp, out in zip(out_exp, outs):
            utt.assert_allclose(exp, out)
