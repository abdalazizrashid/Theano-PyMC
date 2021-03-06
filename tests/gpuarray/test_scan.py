import numpy as np

import aesara
import aesara.sandbox.rng_mrg
from aesara.gpuarray.basic_ops import GpuFromHost, HostFromGpu
from aesara.gpuarray.elemwise import GpuElemwise
from tests import unittest_tools as utt
from tests.gpuarray.config import mode_with_gpu, test_ctx_name


class TestScan:
    def setup_method(self):
        utt.seed_rng()

    def test_one_sequence_one_output_weights_gpu1(self):
        def f_rnn(u_t, x_tm1, W_in, W):
            return u_t * W_in + x_tm1 * W

        u = aesara.tensor.fvector("u")
        x0 = aesara.tensor.fscalar("x0")
        W_in = aesara.tensor.fscalar("win")
        W = aesara.tensor.fscalar("w")

        mode = mode_with_gpu.excluding("InputToGpuOptimizer")
        output, updates = aesara.scan(
            f_rnn,
            u,
            x0,
            [W_in, W],
            n_steps=None,
            truncate_gradient=-1,
            go_backwards=False,
            mode=mode,
        )

        output = GpuFromHost(test_ctx_name)(output)
        f2 = aesara.function(
            [u, x0, W_in, W],
            output,
            updates=updates,
            allow_input_downcast=True,
            mode=mode,
        )

        rng = np.random.RandomState(utt.fetch_seed())
        v_u = rng.uniform(size=(4,), low=-5.0, high=5.0)
        v_x0 = rng.uniform()
        W = rng.uniform()
        W_in = rng.uniform()

        v_u = np.asarray(v_u, dtype="float32")
        v_x0 = np.asarray(v_x0, dtype="float32")
        W = np.asarray(W, dtype="float32")
        W_in = np.asarray(W_in, dtype="float32")

        # compute the output in numpy
        v_out = np.zeros((4,))
        v_out[0] = v_u[0] * W_in + v_x0 * W
        for step in range(1, 4):
            v_out[step] = v_u[step] * W_in + v_out[step - 1] * W

        aesara_values = f2(v_u, v_x0, W_in, W)
        utt.assert_allclose(aesara_values, v_out)

        # TO DEL
        topo = f2.maker.fgraph.toposort()
        scan_node = [
            node
            for node in topo
            if isinstance(node.op, aesara.scan_module.scan_op.Scan)
        ]
        assert len(scan_node) == 1
        scan_node = scan_node[0]

        topo = f2.maker.fgraph.toposort()
        assert sum([isinstance(node.op, HostFromGpu) for node in topo]) == 0
        assert sum([isinstance(node.op, GpuFromHost) for node in topo]) == 4

        scan_node = [
            node
            for node in topo
            if isinstance(node.op, aesara.scan_module.scan_op.Scan)
        ]
        assert len(scan_node) == 1
        scan_node = scan_node[0]
        scan_node_topo = scan_node.op.fn.maker.fgraph.toposort()

        # check that there is no gpu transfer in the inner loop.
        assert any([isinstance(node.op, GpuElemwise) for node in scan_node_topo])
        assert not any([isinstance(node.op, HostFromGpu) for node in scan_node_topo])
        assert not any([isinstance(node.op, GpuFromHost) for node in scan_node_topo])

    # This second version test the second case in the optimizer to the gpu.
    def test_one_sequence_one_output_weights_gpu2(self):
        def f_rnn(u_t, x_tm1, W_in, W):
            return u_t * W_in + x_tm1 * W

        u = aesara.tensor.fvector("u")
        x0 = aesara.tensor.fscalar("x0")
        W_in = aesara.tensor.fscalar("win")
        W = aesara.tensor.fscalar("w")
        output, updates = aesara.scan(
            f_rnn,
            u,
            x0,
            [W_in, W],
            n_steps=None,
            truncate_gradient=-1,
            go_backwards=False,
            mode=mode_with_gpu,
        )

        f2 = aesara.function(
            [u, x0, W_in, W],
            output,
            updates=updates,
            allow_input_downcast=True,
            mode=mode_with_gpu,
        )

        # get random initial values
        rng = np.random.RandomState(utt.fetch_seed())
        v_u = rng.uniform(size=(4,), low=-5.0, high=5.0)
        v_x0 = rng.uniform()
        W = rng.uniform()
        W_in = rng.uniform()

        # compute the output in numpy
        v_out = np.zeros((4,))
        v_out[0] = v_u[0] * W_in + v_x0 * W
        for step in range(1, 4):
            v_out[step] = v_u[step] * W_in + v_out[step - 1] * W

        aesara_values = f2(v_u, v_x0, W_in, W)
        utt.assert_allclose(aesara_values, v_out)

        topo = f2.maker.fgraph.toposort()
        assert sum([isinstance(node.op, HostFromGpu) for node in topo]) == 1
        assert sum([isinstance(node.op, GpuFromHost) for node in topo]) == 4

        scan_node = [
            node
            for node in topo
            if isinstance(node.op, aesara.scan_module.scan_op.Scan)
        ]
        assert len(scan_node) == 1
        scan_node = scan_node[0]
        scan_node_topo = scan_node.op.fn.maker.fgraph.toposort()

        # check that there is no gpu transfer in the inner loop.
        assert any([isinstance(node.op, GpuElemwise) for node in scan_node_topo])
        assert not any([isinstance(node.op, HostFromGpu) for node in scan_node_topo])
        assert not any([isinstance(node.op, GpuFromHost) for node in scan_node_topo])

    # This third test checks that scan can deal with a mixture of dtypes as
    # outputs when is running on GPU
    def test_gpu3_mixture_dtype_outputs(self):
        def f_rnn(u_t, x_tm1, W_in, W):
            return (u_t * W_in + x_tm1 * W, aesara.tensor.cast(u_t + x_tm1, "int64"))

        u = aesara.tensor.fvector("u")
        x0 = aesara.tensor.fscalar("x0")
        W_in = aesara.tensor.fscalar("win")
        W = aesara.tensor.fscalar("w")
        output, updates = aesara.scan(
            f_rnn,
            u,
            [x0, None],
            [W_in, W],
            n_steps=None,
            truncate_gradient=-1,
            go_backwards=False,
            mode=mode_with_gpu,
        )

        f2 = aesara.function(
            [u, x0, W_in, W],
            output,
            updates=updates,
            allow_input_downcast=True,
            mode=mode_with_gpu,
        )

        # get random initial values
        rng = np.random.RandomState(utt.fetch_seed())
        v_u = rng.uniform(size=(4,), low=-5.0, high=5.0)
        v_x0 = rng.uniform()
        W = rng.uniform()
        W_in = rng.uniform()

        # compute the output in numpy
        v_out1 = np.zeros((4,))
        v_out2 = np.zeros((4,), dtype="int64")
        v_out1[0] = v_u[0] * W_in + v_x0 * W
        v_out2[0] = v_u[0] + v_x0
        for step in range(1, 4):
            v_out1[step] = v_u[step] * W_in + v_out1[step - 1] * W
            v_out2[step] = np.int64(v_u[step] + v_out1[step - 1])

        aesara_out1, aesara_out2 = f2(v_u, v_x0, W_in, W)
        utt.assert_allclose(aesara_out1, v_out1)
        utt.assert_allclose(aesara_out2, v_out2)

        topo = f2.maker.fgraph.toposort()
        scan_node = [
            node
            for node in topo
            if isinstance(node.op, aesara.scan_module.scan_op.Scan)
        ]
        assert len(scan_node) == 1
        scan_node = scan_node[0]
        assert scan_node.op.gpua

        scan_node_topo = scan_node.op.fn.maker.fgraph.toposort()

        # check that there is no gpu transfer in the inner loop.
        assert not any([isinstance(node.op, HostFromGpu) for node in scan_node_topo])
        assert not any([isinstance(node.op, GpuFromHost) for node in scan_node_topo])

    def test_gpu4_gibbs_chain(self):
        rng = np.random.RandomState(utt.fetch_seed())
        v_vsample = np.array(
            rng.binomial(
                1,
                0.5,
                size=(3, 20),
            ),
            dtype="float32",
        )
        vsample = aesara.shared(v_vsample)
        trng = aesara.sandbox.rng_mrg.MRG_RandomStreams(utt.fetch_seed())

        def f(vsample_tm1):
            return (
                trng.binomial(vsample_tm1.shape, n=1, p=0.3, dtype="float32")
                * vsample_tm1
            )

        aesara_vsamples, updates = aesara.scan(
            f,
            [],
            vsample,
            [],
            n_steps=10,
            truncate_gradient=-1,
            go_backwards=False,
            mode=mode_with_gpu,
        )
        my_f = aesara.function(
            [],
            aesara_vsamples[-1],
            updates=updates,
            allow_input_downcast=True,
            mode=mode_with_gpu,
        )

        # I leave this to tested by debugmode, this test was anyway
        # more of does the graph compile kind of test
        my_f()
