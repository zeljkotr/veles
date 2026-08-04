from .loader import load_all_knowledge


def search_knowledge(query, limit=3):
    """
    Pretraga lokalnog znanja.
    """

    knowledge = load_all_knowledge()

    query_words = query.lower().split()

    results = []


    for document in knowledge:

        content = document.get("content", "").lower()

        score = 0


        for word in query_words:

            if word in content:
                score += 1


            if word in document.get("name", "").lower():
                score += 2


        if score > 0:

            results.append(
                {
                    "score": score,
                    "name": document["name"],
                    "path": document["path"],
                    "content": document["content"]
                }
            )


    results.sort(
        key=lambda x: x["score"],
        reverse=True
    )


    return results[:limit]



def get_knowledge_context(query):
    """
    Priprema pronađeno znanje za LLM.
    """

    results = search_knowledge(query)


    if not results:
        return ""


    context = "LOKALNO ZNANJE:\n\n"


    for item in results:

        context += (
            f"--- {item['name']} ---\n"
            f"{item['content']}\n\n"
        )


    return context
