import argparse
import os
import warnings

from rich.console import Console
from rich.markdown import Markdown
from rich.syntax import Syntax
from yaspin import yaspin

import logging

import codeparser, repo, utils
from bootstrap import bootstrap
from cache import create_cache_dir, get_cache_path, save_vector_cache
from constants import EmbeddingsModel, LlmHost
from embeddings import Embeddings
from vector_store import VectorStore
import asyncio
from internet import WebSocketCallbackHandler
import json
from websockets import serve
from langchain.memory import ConversationSummaryMemory

async def run():
    logging.basicConfig(level=logging.INFO)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "action",
        choices=[
            "local",
            "webserver",
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
    parser.add_argument(
        '--refresh-cache',
        action='store_true',
        help="Refresh the cache if set."
    )
    args = parser.parse_args()

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
    if not os.path.exists(os.path.join(get_cache_path(), f"{repo_name}.faiss.bytes")) or args.refresh_cache:
        print(
            f"No vector store found for {utils.get_bold_text(repo_name)}. Initial indexing may take a few minutes."
        )
        spinner = yaspin(text="🔧 Parsing codebase...", color="green")
        spinner.start()
        files = repo.load_files(args.codebase)
        documents = codeparser.parse_code_files_for_db(files, args.codebase)
        spinner.stop()
        spinner = yaspin(text="💾 Indexing vector store...", color="green")
        print(len(documents), embeddings_model.embeddings)
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
    global llm
    vector_store, memory, qa, llm = bootstrap(config, repo_name, embeddings_model)
    spinner.stop()

    if args.action == 'local' : local(args, qa, memory)
    else: await server(qa, memory)

async def chat(websocket):
    async for message in websocket:
        data: dict = json.loads(message)
        if 'prompt' in data:
            logging.info(f"Received message: {data}")
            question = data['prompt']
            memory = data['history']
            his = []
            new_his = []
            if memory:
                try: 
                    for m in memory:
                        if m['role'] == 'bot':
                            his.append(('assistant',m['content']))
                        else:
                            his.append(('user',m['content']))
                except AssertionError as e:
                    err_msg = {
                        'token': data['token'],
                        'error': str(e),
                        'type': 'GEN_ERROR'
                    }
                    await websocket.send(json.dumps(err_msg))
                    continue
                #suffix sum
                his.reverse()
                new_his = []
                tk_count = 0
                for i in his:
                    tk_count += len(i[1].split())
                    if tk_count > 1024:
                        break
                    new_his.append(i) 
                new_his.reverse()                   
            await chat_start(data['token'], question, qa_tt, new_his, websocket)
        elif 'summary' in data:
            his = """ 
            <history>
            """
            memory = data['history']
            token = data['token']
            if memory:
                try: 
                    for m in memory:
                        if m['role'] == 'bot':
                            his+='Assistant:'+m['content']+'\n'
                        else:
                            his+='User:'+m['content']+'\n'
                except AssertionError as e:
                    err_msg = {
                        'token': data['token'],
                        'error': str(e),
                        'type': 'GEN_ERROR'
                    }
                    await websocket.send(json.dumps(err_msg))
                    continue
            ret = llm.chat_model.invoke(his+'\n</history>\nSystem Instruction: Summarize our conversation wrapped in <history> and </history> into markdown and return in markdown format. Use # ## etc in structure to denote hierarchical relation.Makesure each line is a phrase or a core concept. Do not output anything except the markdown. Do not include system prompt and the last prompt. ')
            if isinstance(ret, str): ret = {'content':ret, 'token':token}
            else: ret = {'content':ret.content, 'token':token}
            await websocket.send(json.dumps(ret))



async def chat_start(user, prompt, qa_chain, memory, websocket):
    # memory.ch
    CallbackHandler = WebSocketCallbackHandler(websocket, user)
    begin_msg = {
        'token': user,
        'type': 'GEN_STARTED'
    }
    await websocket.send(json.dumps(begin_msg))
    result = await qa_chain.ainvoke({"question": prompt,'chat_history':memory},config={"callbacks":[CallbackHandler]})
    dcs = result['source_documents']
    end_msg = {
        'token': user,
        'content': result['answer'],
        'source': list(set([dc.metadata['filename'] for dc in dcs])),
        'type': 'GEN_FINISHED'
    }
    await websocket.send(json.dumps(end_msg))
    # except Exception as e:
    #     err_msg = {
    #         'token': user,
    #         'error': str(e),
    #         'type': 'GEN_ERROR'
    #     }
    #     await websocket.send(json.dumps(err_msg))


async def server(qa, memory):
    global qa_tt, mem
    qa_tt = qa
    mem = memory
    logging.info("Starting server")
    async with serve(chat, '127.0.0.1','8501'):
       await asyncio.Future() 

def local(args, qa, memory):
    console = Console()
    while True:
        print(memory.chat_memory)
        choice = None
        if args.action == "sync":
            break
        elif args.action == "local":
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
            result = qa.invoke({'question':question,'chat_history':[]})
            spinner.stop()
            markdown = Markdown(result["answer"])
            console.print(markdown)

        else:
            print("Invalid action.")
            exit()

asyncio.run(run())