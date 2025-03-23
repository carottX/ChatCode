from constants import Language
from treesitter.treesitter import Treesitter
from treesitter.treesitter_registry import TreesitterRegistry


class TreesitterGo(Treesitter):
    def __init__(self):
        super().__init__(Language.GO, "function_declaration", "identifier", "comment")


TreesitterRegistry.register_treesitter(Language.GO, TreesitterGo)
