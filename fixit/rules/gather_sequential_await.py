# Copyright (c) Facebook, Inc. and its affiliates.
#
# This source code is licensed under the MIT license found in the
# LICENSE file in the root directory of this source tree.

import libcst as cst

from fixit.common.base import CstLintRule
from fixit.common.utils import InvalidTestCase as Invalid, ValidTestCase as Valid


class GatherSequentialAwaitRule(CstLintRule):
    MESSAGE: str = (
        "IG02 Using await in a loop will run async function sequentially. Use "
        + "asyncio.gather() to run async functions concurrently. See more "
        + "examples here: https://fburl.com/ez1lnkzy"
    )
    VALID = [
        Valid(
            """
            async def async_foo():
                return await async_bar()
            """
        ),
        # await in a loop is fine if it's a test.
        Valid(
            """
            async def async_check_call():
                for _i in range(0, 2):
                    await async_foo()
            """,
            filename="foo/tests/test_foo.py",
        ),
    ]

    INVALID = [
        Invalid(
            """
            async def async_check_call():
                for _i in range(0, 2):
                    await async_foo()
            """,
            "IG02",
            line=3,
        ),
        Invalid(
            """
            async def async_check_assignment():
                for _i in range(0, 2):
                    x = await async_foo()
            """,
            "IG02",
            line=3,
        ),
        Invalid(
            """
            async def async_check_list_comprehension():
                [await async_foo() for _i in range(0, 2)]
            """,
            "IG02",
            line=2,
        ),
    ]

    def should_skip_file(self) -> bool:
        return self.context.in_tests

    def visit_Await(self, node: cst.Await) -> None:
        parent = self.context.node_stack[-2]

        if isinstance(parent, (cst.Expr, cst.Assign)) and parent.value is node:
            grand_parent = self.context.node_stack[-5]
            # for and while code block contain IndentBlock and SimpleStatementLine
            if isinstance(grand_parent, (cst.For, cst.While)):
                self.report(node)

        if (
            isinstance(parent, (cst.ListComp, cst.SetComp, cst.GeneratorExp))
            and parent.elt is node
        ):
            self.report(node)
