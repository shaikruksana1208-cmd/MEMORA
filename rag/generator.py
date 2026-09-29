def build_grounded_prompt(question, relevant_chunks):
    context_parts = []

    for chunk in relevant_chunks:
        context_parts.append(
            f"[Filename: {chunk['filename']} | Page {chunk['page_number']} | Chunk ID: {chunk['chunk_id']}]\n{chunk['chunk_text']}"
        )

    context_text = "\n\n".join(context_parts)

    return f"""RETRIEVED DOCUMENT CONTEXT:
{context_text}

USER QUESTION:
{question}

INSTRUCTIONS:
- Answer using the retrieved document context.
- Do not invent information.
- Do not claim information exists in the document when it was not retrieved.
- If the retrieved context does not contain enough information, clearly say that the answer could not be found in the uploaded document.
- Give a concise student-friendly answer.
- Do not use unnecessary markdown decorations.
- Do not use LaTeX unless the existing project specifically requires it.
"""
