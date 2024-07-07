import logging
import os, sys
import tempfile

from langchain.chains import ConversationalRetrievalChain
from langchain.retrievers.document_compressors import EmbeddingsFilter
from langchain.chat_models import ChatOpenAI
from langchain.chains.base import Chain
from langchain.document_loaders import TextLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Qdrant
from langchain.retrievers import ContextualCompressionRetriever
from langchain.schema import BaseRetriever, Document
from dotenv import load_dotenv

rpath = os.path.abspath('..')
if rpath not in sys.path:
    sys.path.insert(0, rpath)

from scripts.utils import MEMORY, load_document
logging.basicConfig(encoding="utf-8", level=logging.INFO)
LOGGER = logging.getLogger()

load_dotenv()
OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')

LLM = ChatOpenAI(
    model_name="gpt-3.5-turbo", temperature=0, streaming=True
)

def configure_retriever(
    docs: list[Document]
) -> BaseRetriever:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1500, chunk_overlap=200)
    splits = text_splitter.split_documents(docs)

    embeddings = OpenAIEmbeddings()

    vectordb = Qdrant.from_documents(
        docs, 
        embeddings,
        path='new_embeding',
        collection_name="contract_documents",
        force_recreate=True,    
    )
    
    retriever = vectordb.as_retriever (
        search_type = "mmr", search_kwargs={
            "k": 5,
            "fetch_k": 7
        },
    )

    embeddings_filter = EmbeddingsFilter(
        embeddings=embeddings, similarity_threshold=0.76
    )
    return ContextualCompressionRetriever(
        base_compressor=embeddings_filter,
        base_retriever=retriever,
    )

    # return retriever

def configure_chain(retriever: BaseRetriever) -> Chain:
    params = dict(
        llm=LLM,
        retriever=retriever,
        memory=MEMORY,
        verbose=True,
        max_tokens_limit=4000,
        return_source_documents=True
    )

    return ConversationalRetrievalChain.from_llm(
        **params
    )

def configure_retrieval_chain(
    uploaded_files
) -> Chain:
    print("uploaded Files: ", uploaded_files)
     
    docs = []
    temp_dir = tempfile.TemporaryDirectory()
    for file in uploaded_files:
        temp_filepath = os.path.join(temp_dir.name, file.filename)
        file.save(temp_filepath)
        docs.extend(load_document(temp_filepath))

    retriever = configure_retriever(docs=docs)
    chain = configure_chain(retriever=retriever)
    return chain