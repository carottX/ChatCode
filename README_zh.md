# CodebaseRAG

一个高性能的代码库检索增强生成（RAG）后端，允许您用自然语言提问关于代码库的问题，并获得准确、上下文相关的答案。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

[English](README.md) | 简体中文

## 🚀 特点

- **卓越性能**：比现有开源替代方案具有更快的检索速度和更准确的结果
- **语义代码理解**：利用高级嵌入技术理解代码语义
- **交叉引用感知**：维护文件和函数之间关系的感知能力
- **上下文相关回答**：提供带有相关代码片段和引用的答案
- **高效缓存**：智能缓存系统最大限度减少冗余处理

## 📋 要求

- Python 3.10+
- Git

## 🔧 安装

1. 克隆仓库：
```bash
git clone https://github.com/yourusername/codebase-rag.git
cd codebase-rag
```

2. 安装依赖：
```bash
pip install -r requirements.txt
```

## 💻 使用方法

### 基本用法

```bash
python src/main.py local
```

### 作为后端服务运行

```bash
python src/main.py webserver
```

### 刷新向量缓存
```bash
python src/main.py local --refresh_cache
```

### 指定配置文件
```bash
python src/main.py local --config /path/to/config
```

### 高级配置

编辑 `src/config.yaml` 文件以自定义：
- 代码仓库路径
- 后端监听参数
- LLM 参数

## 🏗️ 架构

CodebaseRAG 由几个关键组件组成：
- **代码解析器**（`codeparser.py`）：分析并提取源代码的结构化信息
- **嵌入引擎**（`embeddings.py`）：创建代码的语义表示
- **向量存储**（`vector_store.py`）：高效索引和检索相关代码片段
- **LLM 接口**（`llm.py`）：从检索的上下文生成人类可读的答案
- **缓存层**（`cache.py`）：通过智能缓存优化性能

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

1. Fork 仓库
2. 创建您的特性分支（`git checkout -b feature/amazing-feature`）
3. 提交您的更改（`git commit -m '添加一些很棒的特性'`）
4. 推送到分支（`git push origin feature/amazing-feature`）
5. 打开一个 Pull Request

## 📄 许可证

该项目采用 MIT 许可证 - 有关详细信息，请参阅 LICENSE 文件。