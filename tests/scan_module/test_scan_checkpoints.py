import numpy as np
import pytest

import aesara
import aesara.gpuarray
import aesara.tensor as tt


try:
    from pygpu.gpuarray import GpuArrayException

    PYGPU_AVAILABLE = True
except ImportError:
    PYGPU_AVAILABLE = False


class TestScanCheckpoint:
    def setup_method(self):
        self.k = tt.iscalar("k")
        self.A = tt.vector("A")
        result, _ = aesara.scan(
            fn=lambda prior_result, A: prior_result * A,
            outputs_info=tt.ones_like(self.A),
            non_sequences=self.A,
            n_steps=self.k,
        )
        result_check, _ = aesara.scan_checkpoints(
            fn=lambda prior_result, A: prior_result * A,
            outputs_info=tt.ones_like(self.A),
            non_sequences=self.A,
            n_steps=self.k,
            save_every_N=100,
        )
        self.result = result[-1]
        self.result_check = result_check[-1]
        self.grad_A = tt.grad(self.result.sum(), self.A)
        self.grad_A_check = tt.grad(self.result_check.sum(), self.A)

    def test_forward_pass(self):
        # Test forward computation of A**k.
        f = aesara.function(
            inputs=[self.A, self.k], outputs=[self.result, self.result_check]
        )
        out, out_check = f(range(10), 101)
        assert np.allclose(out, out_check)

    def test_backward_pass(self):
        # Test gradient computation of A**k.
        f = aesara.function(
            inputs=[self.A, self.k], outputs=[self.grad_A, self.grad_A_check]
        )
        out, out_check = f(range(10), 101)
        assert np.allclose(out, out_check)

    @pytest.mark.skipif(~PYGPU_AVAILABLE, reason="Requires pygpu.")
    @pytest.mark.skipif(
        None not in aesara.gpuarray.type.list_contexts(),
        reason="Requires gpuarray backend.",
    )
    def test_memory(self):
        from tests.gpuarray.config import mode_with_gpu  # noqa

        f = aesara.function(
            inputs=[self.A, self.k], outputs=self.grad_A, mode=mode_with_gpu
        )
        f_check = aesara.function(
            inputs=[self.A, self.k], outputs=self.grad_A_check, mode=mode_with_gpu
        )
        free_gmem = aesara.gpuarray.type._context_reg[None].free_gmem
        data = np.ones(free_gmem // 3000, dtype=np.float32)
        # Check that it works with the checkpoints
        size = 1000
        if isinstance(mode_with_gpu, aesara.compile.DebugMode):
            size = 100
        f_check(data, size)
        # Check that the basic scan fails in that case
        # Skip that check in DebugMode, as it can fail in different ways
        if not isinstance(mode_with_gpu, aesara.compile.DebugMode):
            with pytest.raises(GpuArrayException):
                f(data, 1000)

    def test_taps_error(self):
        # Test that an error rises if we use taps in outputs_info.
        with pytest.raises(RuntimeError):
            aesara.scan_checkpoints(lambda: None, [], {"initial": self.A, "taps": [-2]})
