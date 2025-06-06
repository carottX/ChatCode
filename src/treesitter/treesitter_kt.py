from constants import Language
from treesitter.treesitter import Treesitter
from treesitter.treesitter_registry import TreesitterRegistry


class TreesitterKotlin(Treesitter):
    def __init__(self):
        super().__init__(
            Language.KOTLIN, "function_declaration", "simple_identifier", "comment"
        )


TreesitterRegistry.register_treesitter(Language.KOTLIN, TreesitterKotlin)
