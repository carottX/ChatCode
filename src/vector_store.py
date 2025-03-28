import os

import inquirer
from langchain.embeddings.base import Embeddings
from langchain.schema import Document
from langchain_community.vectorstores.faiss import FAISS

import utils
from cache import VectorCache, get_cache_path, load_vector_cache
from codeparser import parse_code_files_for_db
from repo import get_commit_hash


class VectorStore:
    def __init__(self, name: str, embeddings: Embeddings):
        self.name = name
        self.embeddings = embeddings
        self.install_faiss()

    def load_documents(self):
        """
        Loads documents into the vector store.

        This method reads the serialized FAISS index from a file, deserializes it, and loads it into the FAISS database.
        It also loads the vector cache from a JSON file and initializes the retriever with the specified search parameters.
        """
        with open(
            os.path.join(get_cache_path(), f"{self.name}.faiss.bytes"), "rb"
        ) as file:
            index = file.read()

        self.db = FAISS.deserialize_from_bytes(
            embeddings=self.embeddings, serialized=index
        )
        self.vector_cache = load_vector_cache(f"{self.name}.json")
        self.retriever = self.db.as_retriever(search_type="mmr")

    def index_documents(self, documents: list[Document]):
        """
        Indexes the given documents and stores them in the vector store.

        This method creates a FAISS index from the provided documents and serializes it to a file.
        It also creates a vector cache for quick lookup of document vectors and initializes the retriever.

        Args:
            documents (list[Document]): A list of Document objects to be indexed.
        """
        self.vector_cache = {}
        self.db = FAISS.from_documents(documents, self.embeddings)
        index = self.db.serialize_to_bytes()
        with open(
            os.path.join(get_cache_path(), f"{self.name}.faiss.bytes"), "wb"
        ) as binary_file:
            binary_file.write(index)
        # Create vector cache
        index_to_docstore_id = self.db.index_to_docstore_id
        for i in range(len(documents)):
            print('Parsing {:.2f}%'.format((i + 1) / len(documents) * 100))
            document = self.db.docstore.search(index_to_docstore_id[i])
            if document and isinstance(document, Document):
                # Check if the document is already present in the vector cache
                # if yes, then add the vector id to the vector cache entry
                if self.vector_cache.get(document.metadata["filename"]):
                    self.vector_cache[document.metadata["filename"]].vector_ids.append(
                        index_to_docstore_id[i]
                    )
                # if no, then create a new entry in the vector cache
                else:
                    self.vector_cache[document.metadata["filename"]] = VectorCache(
                        document.metadata["filename"],
                        [index_to_docstore_id[i]],
                    )

        self.retriever = self.db.as_retriever(search_type="mmr", search_kwargs={"k": 8})

    def similarity_search(self, query: str):
        return self.db.similarity_search(query, k=4)

    def install_faiss(self):
        try:
            import faiss  # noqa: F401
        except ImportError:
            question = [
                inquirer.Confirm(
                    "confirm",
                    message=f"{utils.get_bold_text('faiss')} package not found in this python environment. Do you want to install it now?",
                    default=True,
                ),
            ]

            answers = inquirer.prompt(question)
            if answers and answers["confirm"]:
                import subprocess
                import sys

                question = [
                    inquirer.List(
                        "faiss-installation",
                        message="Please select the appropriate option to install FAISS. Use gpu if your system supports CUDA",
                        choices=[
                            "faiss-cpu",
                            "faiss-gpu",
                        ],
                        default="faiss-cpu",
                    ),
                ]

                answers = inquirer.prompt(question)
                if answers and answers["faiss-installation"]:
                    try:
                        subprocess.run(
                            [
                                sys.executable,
                                "-m",
                                "pip",
                                "install",
                                answers["faiss-installation"],
                            ],
                            check=True,
                        )
                    except subprocess.CalledProcessError as e:
                        print(f"Error during faiss installation: {e}")
            else:
                exit("faiss package is required for codeqai to work.")
