import tree_sitter

from constants import Language
from treesitter.treesitter import Treesitter, TreesitterMethodNode
from treesitter.treesitter_registry import TreesitterRegistry


class TreesitterHaskell(Treesitter):
    def __init__(self):
        super().__init__(Language.HASKELL, "function", "variable", "comment")

    def parse(self, file_bytes: bytes) -> list[TreesitterMethodNode]:
        """
        Parses the given file bytes and extracts method nodes.

        Args:
            file_bytes (bytes): The content of the file to be parsed.

        Returns:
            list[TreesitterMethodNode]: A list of TreesitterMethodNode objects representing the methods in the file.
        """
        self.tree = self.parser.parse(file_bytes)
        result = []
        methods = self._query_all_methods(self.tree.root_node)
        for method in methods:
            method_name = self._query_method_name(method["method"])
            doc_comment = method["doc_comment"]
            source_code = None
            if method["method"].type == "signature":
                sc = map(
                    lambda x: "\n" + x.text.decode() if x.type == "function" else "",
                    method["method"].children,
                )
                source_code = method["method"].text.decode() + "".join(sc)
            result.append(
                TreesitterMethodNode(
                    method_name, doc_comment, source_code, method["method"]
                )
            )
        return result

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
            doc_comment_node = None
            if (
                node.prev_named_sibling
                and node.prev_named_sibling.type == self.doc_comment_identifier
            ):
                doc_comment_node = node.prev_named_sibling.text.decode()
            else:
                if (
                    node.prev_named_sibling
                    and node.prev_named_sibling.type == "signature"
                ):
                    prev_node = node.prev_named_sibling
                    if (
                        prev_node.prev_named_sibling
                        and prev_node.prev_named_sibling.type
                        == self.doc_comment_identifier
                    ):
                        doc_comment_node = prev_node.prev_named_sibling.text.decode()
                    prev_node.children.append(node)
                    node = prev_node
            methods.append({"method": node, "doc_comment": doc_comment_node})
        else:
            for child in node.children:
                current = self._query_all_methods(child)
                if methods and current:
                    previous = methods[-1]
                    if self._query_method_name(
                        previous["method"]
                    ) == self._query_method_name(current[0]["method"]):
                        previous["method"].children.extend(
                            map(lambda x: x["method"], current)
                        )
                        methods = methods[:-1]
                        methods.append(previous)
                    else:
                        methods.extend(current)
                else:
                    methods.extend(current)
        return methods

    def _query_method_name(self, node: tree_sitter.Node):
        """
        Queries the method name from the given syntax tree node.

        Args:
            node (tree_sitter.Node): The syntax tree node to query.

        Returns:
            str or None: The method name if found, otherwise None.
        """
        if node.type == "signature" or node.type == self.method_declaration_identifier:
            for child in node.children:
                if child.type == self.method_name_identifier:
                    return child.text.decode()
        return None


TreesitterRegistry.register_treesitter(Language.HASKELL, TreesitterHaskell)
