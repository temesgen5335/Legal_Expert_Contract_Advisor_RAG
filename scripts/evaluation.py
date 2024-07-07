import nest_asyncio
import asyncio
import os, sys
import openai
from dotenv import load_dotenv, find_dotenv
import pandas as pd

from werkzeug.datastructures import FileStorage
from ragas.langchain.evalchain import RagasEvaluatorChain
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_precision,
    context_recall,
)

rpath = os.path.abspath('..')
if rpath not in sys.path:
    sys.path.insert(0, rpath)
from backend.rag_app import configure_retrieval_chain
from scripts.utils import MEMORY

load_dotenv(find_dotenv())
api_key = os.environ.get("OPENAI_API_KEY")
openai.api_key = api_key
nest_asyncio.apply()

def load_data(file_path):
    qna = pd.read_csv(file_path)
    eval_questions = qna['Questions'].tolist()
    eval_answers = qna['Answers'].tolist()

    examples = [
        {"query": q, "ground_truths": [eval_answers[i]]}
        for i, q in enumerate(eval_questions)
    ]

    return examples

def evaluate_chain(examples, chain):
    size = len(examples)
    print(size)
    examples = [{
        "question": examples[i]['query']
    } for i in range(size)]
    print(examples)
    predictions = chain.batch(examples)
    return predictions

def evaluate_metrics(examples, chain):
    faithfulness_chain = RagasEvaluatorChain(metric=faithfulness)
    answer_rel_chain = RagasEvaluatorChain(metric=answer_relevancy)
    context_rel_chain = RagasEvaluatorChain(metric=context_precision)
    context_recall_chain = RagasEvaluatorChain(metric=context_recall)

    # print(len(examples), len(predictions))
    result_dict = {
        "faithfulness_score": [],
        "answer_relevancy_score": [],
        "context_precision_score": [],
        "context_recall_score": []
    }
    for example in examples:
        result = chain(
            {
            "question": example["query"],
            "chat_history": MEMORY.chat_memory.messages
            }
        )

        result["result"] = result["answer"]
        result["query"] = result["question"]

        result_dict["faithfulness_score"].append(faithfulness_chain(result))
        result_dict["answer_relevancy_score"].append(answer_rel_chain(result))
        # result_dict["context_precision_score"].append(context_rel_chain(result))
        result_dict["context_recall_score"].append(context_recall_chain(result))


    return result_dict

def create_dataframe(qna, faithfulness_scores, answer_relevancy_scores, context_precision_scores, context_recall_scores):
    df = pd.DataFrame({
        "Faithfulness Score": [score["faithfulness_score"] for score in faithfulness_scores],
        "Answer Relevancy Score": [score["answer_relevancy_score"] for score in answer_relevancy_scores],
        "Context Precision Score": [score["context_precision_score"] for score in context_precision_scores],
        "Context Recall Score": [score["context_recall_score"] for score in context_recall_scores]
    })

    result_df = pd.concat([qna, df], axis=1)
    return result_df

def convert_filepath_to_FileStorage(file_path, filename):
    temp_files = FileStorage(stream=open(file_path, 'rb'), filename=filename, content_type='application/pdf')
    return temp_files

def main():
    file_path = convert_filepath_to_FileStorage('../data/contracts/Robinson Advisory.docx.pdf', 'Robinson Advisory.docx.pdf')
    print(file_path)
    
    chain = configure_retrieval_chain([file_path])
    examples = load_data('../data/Q&A/Rapter Q&A - Sheet1.csv')
    # print(*examples)
    question = examples[0]['query']
    result = chain({"question": question})
    print(result["answer"])

    result_dict = evaluate_metrics(examples, chain)
    # result_df = create_dataframe(qna, faithfulness_score, answer_relevancy_score, context_precision_score, context_recall_score)
    # result_df.to_csv('evaluation.csv')
    return result_dict

if __name__ == "__main__":
    result_dataframe = main()
    print(result_dataframe)