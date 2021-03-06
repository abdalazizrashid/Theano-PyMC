import warnings

from aesara.tensor.nnet.blocksparse import (
    SparseBlockGemv,
    SparseBlockOuter,
    sparse_block_dot,
    sparse_block_gemv,
    sparse_block_gemv_inplace,
    sparse_block_outer,
    sparse_block_outer_inplace,
)


__all__ = [
    SparseBlockGemv,
    SparseBlockOuter,
    sparse_block_dot,
    sparse_block_gemv,
    sparse_block_gemv_inplace,
    sparse_block_outer,
    sparse_block_outer_inplace,
]

warnings.warn(
    "DEPRECATION: aesara.sandbox.blocksparse does not exist anymore,"
    "it has been moved to aesara.tensor.nnet.blocksparse.",
    category=DeprecationWarning,
)
