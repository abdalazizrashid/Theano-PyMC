import os
import re

import aesara
from aesara import tensor


class FunctionName:
    def test_function_name(self):
        x = tensor.vector("x")
        func = aesara.function([x], x + 1.0)

        regex = re.compile(os.path.basename(".*test_function_name.pyc?:14"))
        assert regex.match(func.name) is not None
