# CodebaseRAG

A high-performance backend for codebase retrieval augmented generation (RAG) that allows you to ask natural language questions about your codebase and get accurate, contextual answers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

English | [简体中文](README_zh.md)

## 🚀 Features

- **Superior Performance**: Outperforms existing open-source alternatives with faster retrieval and more accurate results
- **Semantic Code Understanding**: Leverages advanced embeddings to understand code semantics
- **Cross-Reference Awareness**: Maintains awareness of relationships between files and functions
- **Contextual Answers**: Provides answers with relevant code snippets and references
- **Efficient Caching**: Smart caching system minimizes redundant processing

## 📋 Requirements

- Python 3.10+
- Git

## 🔧 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/codebase-rag.git
cd codebase-rag
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 💻 Usage

### Basic Usage

```bash
python src/main.py local
```

### Serve as backend

```bash
python src/main.py webserver
```

### Refresh vector cache
```bash
python src/main.py local --refresh_cache
```

### Specify the config file
```bash
python src/main.py local --config /path/to/config
```


### Advanced Configuration

Edit the `src/config.yaml` file to customize:
- Codebase path
- Webserver parameters
- LLM parameters

## 🏗️ Architecture

CodebaseRAG consists of several key components:
- **Code Parser** (`codeparser.py`): Analyzes and extracts structured information from source code
- **Embeddings Engine** (`embeddings.py`): Creates semantic representations of code
- **Vector Store** (`vector_store.py`): Efficiently indexes and retrieves relevant code snippets
- **LLM Interface** (`llm.py`): Generates human-readable answers from retrieved context
- **Caching Layer** (`cache.py`): Optimizes performance through intelligent caching

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.