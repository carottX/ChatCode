import os

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter

from constants import Language
from treesitter.treesitter import Treesitter, TreesitterMethodNode
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage
from langchain.chains.combine_documents import create_stuff_documents_chain
import uuid
import utils


def parse_code_files_for_db(code_files: list[str], dirs, base_path) -> list[Document]:
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
        ctinue = True
        for d in dirs:
            if d in code_file:
                ctinue = False
        if(ctinue and dirs != '*'): continue
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

def summarize_code_chunks(code_chunks: list[Document], dirs, llm) -> list[Document]:
    """
    Summarizes a list of code chunks and returns a list of Document objects containing the summaries.

    Args:
        code_chunks (list[Document]): List of code chunks to be summarized.

    Returns:
        list[Document]: List of Document objects containing the summaries.
    """
    prompt = ChatPromptTemplate.from_messages(
        [
            SystemMessage(
                content=(
                    "Summarize the following content in a single, concise paragraph. "
                    "Include key information from all headers provided, maintaining the overall context and meaning. "
                    "Output only the summary text without any introductory phrases, labels, or concluding remarks."
                )
            ),
            HumanMessagePromptTemplate.from_template("{context}"),
        ]
    )

    chain = create_stuff_documents_chain(llm, prompt)
    summarized_documents = []
    for code_chunk in code_chunks:
        ctinue = True
        for d in dirs:
            if d in code_chunk.metadata['filename']:
                ctinue = False
        if(ctinue): continue
        print(code_chunk.metadata['filename'])
        metadata = '\n'.join([f"{k}: {v}" for k, v in code_chunk.metadata.items()])
        merged_docs = [Document(page_content=metadata), Document(page_content=code_chunk.page_content)]
        result = chain.invoke({'context':merged_docs})
        unique_id = str(uuid.uuid4())
        summarized_document = Document(
            page_content=result,
            metadata={
                "filename": code_chunk.metadata['filename'],
                "method_name": code_chunk.metadata['method_name'],
                "unique_id": unique_id,
                'type':'summary'
            },
        )
        updated_metadata = code_chunk.metadata.copy()
        updated_metadata.update({"unique_id": unique_id,'type':'original'})
        code_chunk.metadata = updated_metadata
        summarized_documents.append(summarized_document)
    return summarized_documents
