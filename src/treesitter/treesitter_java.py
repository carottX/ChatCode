from constants import Language
from treesitter.treesitter import Treesitter
from treesitter.treesitter_registry import TreesitterRegistry


class TreesitterJava(Treesitter):
    def __init__(self):
        super().__init__(
            Language.JAVA, "method_declaration", "identifier", "block_comment"
        )


TreesitterRegistry.register_treesitter(Language.JAVA, TreesitterJava)
