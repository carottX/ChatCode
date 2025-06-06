import tree_sitter

from constants import Language
from treesitter.treesitter import Treesitter
from treesitter.treesitter_registry import TreesitterRegistry


class TreesitterCpp(Treesitter):
    def __init__(self):
        super().__init__(Language.CPP, "function_definition", "identifier", "comment")

    def _query_method_name(self, node: tree_sitter.Node):
        """
        Queries the method name from the given syntax tree node.

        Args:
            node (tree_sitter.Node): The syntax tree node to query.

        Returns:
            str or None: The method name if found, otherwise None.
        """
        if node.type == self.method_declaration_identifier:
            for child in node.children:
                # if method returns pointer, skip pointer declarator
                if child.type == "pointer_declarator":
                    child = child.children[1]
                if child.type == "function_declarator":
                    for child in child.children:
                        if child.type == self.method_name_identifier:
                            return child.text.decode()
        return None


TreesitterRegistry.register_treesitter(Language.CPP, TreesitterCpp)
