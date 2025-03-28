import warnings
import os

from rich.console import Console
from rich.markdown import Markdown
from yaspin import yaspin

import logging

import repo
from vector_store import VectorStore
import codeparser
from bootstrap import bootstrap
from cache import create_cache_dir, get_cache_path, save_vector_cache
from embeddings import Embeddings
import asyncio
from internet import WebSocketCallbackHandler
import json
from llm import LLM
from websockets import serve
import re
from utils import load_yaml, parse_args, get_bold_text

async def run():
    logging.basicConfig(level=logging.INFO)
    warnings.filterwarnings("ignore", category=DeprecationWarning)

    args = parse_args()

    config = load_yaml(args.config)

    repo_name = repo.repo_name(config['codebase']['path'])

    create_cache_dir()
    llm = LLM(config['llm']['base_url'], config['llm']['api_key'], config['llm']['max_tokens'], config['llm']['model'])

    embeddings_model = Embeddings()
    check_vector_cache(repo_name, args, config, embeddings_model, llm.chat_model)
    memory, qa = bootstrap(config, repo_name, embeddings_model, llm)
    if args.action == 'local' : local(qa, memory)
    else: await server(llm, qa, config['llm']['max_tokens']/2, config['webserver']['host'], config['webserver']['port'])

async def chat_normal(websocket, data, qa, max_tokens):
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
            return 
        his.reverse()
        new_his = []
        tk_count = 0
        for i in his:
            tk_count += len(i[1].split())
            if tk_count > max_tokens:
                break
            new_his.append(i) 
        new_his.reverse()                   
    await chat_start(data['token'], question, qa, new_his, websocket)

async def chat_summary(websocket, data, llm):
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
            return
    ret = llm.chat_model.invoke(his+'\n</history>\nSystem Instruction: Summarize our conversation wrapped in <history> and </history> into markdown and return in markdown format. Use # ## etc in structure to denote hierarchical relation.Makesure each line is a phrase or a core concept. Do not output anything except the markdown. Do not include system prompt and the last prompt. ')
    str_ret = ret if isinstance(ret, str) else ret.content
    if str_ret.startswith('```') or str_ret.startswith('```markdown'): 
        str_ret = ''.join(str_ret.split('\n')[1:-1])
    str_ret = re.sub(r'([^\n])(\n?)(#+ )', r'\1\n\3', str_ret)
    ret = {'content':str_ret, 'token':token}
    await websocket.send(json.dumps(ret))

async def chat(websocket, llm, qa, max_tokens):
    async for message in websocket:
        data: dict = json.loads(message)
        if 'prompt' in data:
            await chat_normal(websocket, data, qa, max_tokens)
        elif 'summary' in data:
            await chat_summary(websocket, data, llm)

async def chat_start(user, prompt, qa_chain, memory, websocket):
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

async def server(llm, qa, max_tokens, host='127.0.0.1', port='8501'):
    logging.info("Starting server")
    async def Wrapper(websocket):
        return await chat(websocket, llm, qa, max_tokens)
    async with serve(Wrapper, host, port):
       await asyncio.Future() 

def local(qa, memory):
    console = Console()
    while True:
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
        print(result["source_documents"])
        markdown = Markdown(result["answer"])
        console.print(markdown)

def check_vector_cache(repo_name, args, config, embeddings_model, llm):
    if not os.path.exists(os.path.join(get_cache_path(), f"{repo_name}.faiss.bytes")) or args.refresh_cache:
        print(
            f"No vector store found for {get_bold_text(repo_name)}. Initial indexing may take a few minutes."
        )
        spinner = yaspin(text="🔧 Parsing codebase...", color="green")
        spinner.start()
        files = repo.load_files(config['codebase']['path'])
        documents = codeparser.parse_code_files_for_db(files, config['codebase']['desired_dirs'],config['codebase']['path'])
        spinner.stop()
        spinner = yaspin(text="💾 Indexing vector store...", color="green")
        #summaries = codeparser.summarize_code_chunks(documents, config['codebase']['desired_dirs'], llm)
        #documents.extend(summaries)
        vector_store = VectorStore(
            repo_name,
            embeddings=embeddings_model.embeddings,
        )
        spinner.start()
        vector_store.index_documents(documents)
        save_vector_cache(vector_store.vector_cache, f"{repo_name}.json")
        spinner.stop()

asyncio.run(run())