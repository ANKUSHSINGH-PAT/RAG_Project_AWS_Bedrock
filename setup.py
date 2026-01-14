from setuptools import setup, find_packages

setup(
    name="QA_System",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "boto3",
        "langchain",
        "langchain-core",
        "langchain-aws",
        "langchain-community",
        "chromadb",
        "sentence-transformers",
        "python-dotenv",
        "setuptools",
        "streamlit",
        "langchain-text-splitters",
        "pypdf",
        "faiss-cpu"
    ],
)
