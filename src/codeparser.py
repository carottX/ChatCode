import os

import inquirer
from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from yaspin import yaspin

import repo, utils
from constants import Language
from treesitter.treesitter import Treesitter, TreesitterMethodNode


def parse_code_files_for_db(code_files: list[str], base_path) -> list[Document]:
    """
    Parses a list of code files and returns a list of Document objects for database storage.

    Args:
        code_files (list[str]): List of paths to code files to be parsed.

    Returns:
        list[Document]: List of Document objects containing parsed code information.
    """
    documents = []
    code_splitter = None
    for code_file in code_files:
        # print(code_file)
        try:
            with open(code_file, "r", encoding="utf-8") as file:
                file_bytes = file.read().encode()

                file_extension = utils.get_file_extension(code_file)
                programming_language = utils.get_programming_language(file_extension)
                if programming_language == Language.UNKNOWN:
                    continue

                langchain_language = utils.get_langchain_language(programming_language)

                if langchain_language:
                    code_splitter = RecursiveCharacterTextSplitter.from_language(
                        language=langchain_language,
                        chunk_size=512,
                        chunk_overlap=128,
                    )

                treesitter_parser = Treesitter.create_treesitter(programming_language)
                treesitterNodes: list[TreesitterMethodNode] = treesitter_parser.parse(
                    file_bytes
                )
                for node in treesitterNodes:
                    method_source_code = node.method_source_code
                    # print()
                    filename = os.path.basename(code_file)

                    if node.doc_comment and programming_language != Language.PYTHON:
                        method_source_code = node.doc_comment + "\n" + method_source_code

                    splitted_documents = [method_source_code]
                    if code_splitter:
                        splitted_documents = code_splitter.split_text(method_source_code)

                    for splitted_document in splitted_documents:
                        document = Document(
                            page_content=splitted_document,
                            metadata={
                                "filename": os.path.relpath(code_file, base_path),
                                "method_name": node.name,
                            },
                        )
                        # document.metadata
                        documents.append(document)
        except Exception as e:
            print(f"Error parsing code file: {code_file}, {e}")
            continue

    return documents