import argparse
import os
import warnings

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from yaspin import yaspin

from codeqai import codeparser, repo, utils
from bootstrap import bootstrap
from cache import create_cache_dir, get_cache_path, save_vector_cache
from constants import EmbeddingsModel, LlmHost
from embeddings import Embeddings
from vector_store import VectorStore

def run():
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "action",
        choices=[
            "chat",
            "configure",
        ],
        help='Action to perform.'
        + "'chat' to chat with the model, 'configure' to start config wizard, "
        + "'sync' to sync the vector store with the current git checkout",
    )
    parser.add_argument(
        "--max-tokens",
        type=int,
        default=1024,
        help="Token limit per code block for distillation dataset extraction. Default is 1024.",
    )
    parser.add_argument(
        "--codebase",
        type=str,
        default='.',
        help="Path to the codebase to analyze. Default is current directory.",
    )
    args = parser.parse_args()
    # print(args)

    # load config
    config = {
        'chat-model': 'asdkmkmaskd', 
        'embeddings': 'SentenceTransformers-all-MiniLM-L6-v2', 
        'llm-host': 'OpenAI'
    }

    repo_name = repo.repo_name(args.codebase)

    create_cache_dir()

    embeddings_model = Embeddings(
        model=EmbeddingsModel[config["embeddings"].upper().replace("-", "_")],
        deployment=(
            config["embeddings-deployment"]
            if "embeddings-deployment" in config
            else None
        ),
    )

    # check if faiss.index exists
    if not os.path.exists(os.path.join(get_cache_path(), f"{repo_name}.faiss.bytes")):
        print(
            f"No vector store found for {utils.get_bold_text(repo_name)}. Initial indexing may take a few minutes."
        )
        spinner = yaspin(text="🔧 Parsing codebase...", color="green")
        spinner.start()
        files = repo.load_files()
        documents = codeparser.parse_code_files_for_db(files)
        spinner.stop()
        spinner = yaspin(text="💾 Indexing vector store...", color="green")
        vector_store = VectorStore(
            repo_name,
            embeddings=embeddings_model.embeddings,
        )
        spinner.start()
        vector_store.index_documents(documents)
        save_vector_cache(vector_store.vector_cache, f"{repo_name}.json")
        spinner.stop()

    spinner = yaspin(text="💾 Loading vector store...", color="green")
    spinner.start()
    vector_store, memory, qa = bootstrap(config, repo_name, embeddings_model)
    spinner.stop()
    console = Console()
    while True:
        choice = None
        if args.action == "sync":
            break
        elif args.action == "chat":
            question = input("💬 Ask anything about the codebase: ")
            if question.startswith('/'):
                if question == '/exit':
                    break
                elif question == '/reset':
                    memory.reset()
                    print('Reset!')
                else:
                    print("Invalid command.")
                continue
            spinner = yaspin(text="🤖 Processing...", color="green")
            spinner.start()
            result = qa(question)
            spinner.stop()
            markdown = Markdown(result["answer"])
            console.print(markdown)

        else:
            print("Invalid action.")
            exit()
run()