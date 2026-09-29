from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph


class DocumentTutorState(TypedDict, total=False):
    question: str

    retrieval_query: str

    document_index: Any
    metadata: list
    filename: str
    client: Any

    candidate_chunks: list
    relevant_chunks: list

    prompt: str
    answer: str
    sources: list

    generate_ai: Any

    # Dependency functions supplied by app.py.
    refine_query: Any
    embed_texts: Any
    retrieve_top_chunks: Any
    rerank_chunks: Any
    build_grounded_prompt: Any
    is_answer_grounded: Any
    unverified_answer_message: Any


# ==========================================================
# NODE 1 — QUERY REFINEMENT
# ==========================================================

def refine_question(state: DocumentTutorState):

    question = state["question"]
    filename = state.get("filename")
    refine_query = state["refine_query"]

    try:

        retrieval_query = refine_query(
            question,
            filename
        )

        if (
            not isinstance(retrieval_query, str)
            or not retrieval_query.strip()
        ):
            retrieval_query = question

    except Exception as error:

        print(
            "QUERY REFINEMENT ERROR:",
            error
        )

        retrieval_query = question

    return {
        "retrieval_query": retrieval_query
    }


# ==========================================================
# NODE 2 — VECTOR RETRIEVAL
# ==========================================================

def retrieve_documents(state: DocumentTutorState):

    retrieval_query = state["retrieval_query"]

    embed_texts = state["embed_texts"]
    retrieve_top_chunks = state["retrieve_top_chunks"]

    query_embedding = embed_texts(
        [retrieval_query],
        client=state["client"]
    )[0]

    candidate_chunks = retrieve_top_chunks(
        state["document_index"],
        state["metadata"],
        query_embedding,
        top_k=12
    )

    return {
        "candidate_chunks": candidate_chunks
    }


# ==========================================================
# NODE 3 — LOCAL RERANKING
# ==========================================================

def rerank_documents(state: DocumentTutorState):

    candidate_chunks = state.get(
        "candidate_chunks",
        []
    )

    rerank_chunks = state["rerank_chunks"]

    if not candidate_chunks:

        return {
            "relevant_chunks": []
        }

    try:

        relevant_chunks = rerank_chunks(
            state["retrieval_query"],
            candidate_chunks,
            top_k=4
        )

        if not relevant_chunks:

            raise ValueError(
                "The reranker returned no chunks."
            )

    except Exception as error:

        print(
            "DOCUMENT RERANK ERROR:",
            error
        )

        relevant_chunks = candidate_chunks[:4]

    return {
        "relevant_chunks": relevant_chunks
    }


# ==========================================================
# NODE 4 — BUILD GROUNDED PROMPT
# ==========================================================

def build_prompt(state: DocumentTutorState):

    build_grounded_prompt = state[
        "build_grounded_prompt"
    ]

    prompt = build_grounded_prompt(
        state["question"],
        state.get("relevant_chunks", [])
    )

    return {
        "prompt": prompt
    }


# ==========================================================
# NODE 5 — GENERATE ANSWER
# ==========================================================

def generate_answer(state: DocumentTutorState):

    generate_ai = state["generate_ai"]

    answer = generate_ai(
        state["prompt"]
    )

    return {
        "answer": answer
    }


# ==========================================================
# NODE 6 — GROUNDEDNESS CHECK
# ==========================================================

def check_groundedness(state: DocumentTutorState):

    answer = state["answer"]

    relevant_chunks = state.get(
        "relevant_chunks",
        []
    )

    is_answer_grounded = state[
        "is_answer_grounded"
    ]

    unverified_answer_message = state[
        "unverified_answer_message"
    ]

    try:

        grounded = is_answer_grounded(
            answer,
            relevant_chunks
        )

        if not grounded:

            answer = unverified_answer_message()

    except Exception as error:

        print(
            "DOCUMENT GROUNDEDNESS CHECK ERROR:",
            error
        )

        answer = unverified_answer_message()

    return {
        "answer": answer
    }


# ==========================================================
# NODE 7 — BUILD SOURCES
# ==========================================================

def build_sources(state: DocumentTutorState):

    relevant_chunks = state.get(
        "relevant_chunks",
        []
    )

    seen_sources = set()
    sources = []

    for chunk in relevant_chunks:

        page_key = (
            chunk["filename"],
            chunk["page_number"]
        )

        if page_key in seen_sources:

            continue

        seen_sources.add(page_key)

        sources.append({
            "filename": chunk["filename"],
            "page": chunk["page_number"]
        })

    return {
        "sources": sources
    }


# ==========================================================
# CONDITIONAL ROUTING
# ==========================================================

def route_after_retrieval(state: DocumentTutorState):

    candidate_chunks = state.get(
        "candidate_chunks",
        []
    )

    if not candidate_chunks:

        return "no_documents"

    return "rerank"


def no_documents(state: DocumentTutorState):

    return {
        "answer": (
            "I could not find enough information in the "
            "uploaded document to answer that question."
        ),
        "sources": []
    }


# ==========================================================
# CREATE LANGGRAPH WORKFLOW
# ==========================================================

def create_document_tutor_workflow():

    graph = StateGraph(
        DocumentTutorState
    )

    graph.add_node(
        "refine",
        refine_question
    )

    graph.add_node(
        "retrieve",
        retrieve_documents
    )

    graph.add_node(
        "rerank",
        rerank_documents
    )

    graph.add_node(
        "build_prompt",
        build_prompt
    )

    graph.add_node(
        "generate",
        generate_answer
    )

    graph.add_node(
        "groundedness",
        check_groundedness
    )

    graph.add_node(
        "sources",
        build_sources
    )

    graph.add_node(
        "no_documents",
        no_documents
    )

    graph.add_edge(
        START,
        "refine"
    )

    graph.add_edge(
        "refine",
        "retrieve"
    )

    graph.add_conditional_edges(
        "retrieve",
        route_after_retrieval,
        {
            "rerank": "rerank",
            "no_documents": "no_documents"
        }
    )

    graph.add_edge(
        "rerank",
        "build_prompt"
    )

    graph.add_edge(
        "build_prompt",
        "generate"
    )

    graph.add_edge(
        "generate",
        "groundedness"
    )

    graph.add_edge(
        "groundedness",
        "sources"
    )

    graph.add_edge(
        "sources",
        END
    )

    graph.add_edge(
        "no_documents",
        END
    )

    return graph.compile()