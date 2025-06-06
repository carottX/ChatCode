import tree_sitter

from constants import Language
from treesitter.treesitter import Treesitter, TreesitterMethodNode
from treesitter.treesitter_registry import TreesitterRegistry


class TreesitterRuby(Treesitter):
    def __init__(self):
        super().__init__(Language.RUBY, "method", "identifier", "comment")

    def parse(self, file_bytes: bytes) -> list[TreesitterMethodNode]:
        return super().parse(file_bytes)

    def _query_all_methods(
        self,
        node: tree_sitter.Node,
    ):
        """
        Recursively queries all method nodes in the given syntax tree node.

        Args:
            node (tree_sitter.Node): The root node to start the query from.

        Returns:
            list: A list of dictionaries, each containing a method node and its associated doc comment (if any).
        """
        methods = []
        if node.type == self.method_declaration_identifier:
            doc_comment = []
            doc_comment_node = node
            while (
                doc_comment_node.prev_named_sibling
                and doc_comment_node.prev_named_sibling.type
                == self.doc_comment_identifier
            ):
                doc_comment_node = doc_comment_node.prev_named_sibling
                doc_comment.insert(0, doc_comment_node.text.decode())
            methods.append({"method": node, "doc_comment": "\n".join(doc_comment)})
        else:
            for child in node.children:
                methods.extend(self._query_all_methods(child))
        return methods


# Register the TreesitterRuby class in the registry
TreesitterRegistry.register_treesitter(Language.RUBY, TreesitterRuby)
