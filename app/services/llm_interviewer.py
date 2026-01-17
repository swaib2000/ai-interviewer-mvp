from app.services.llm_client import generate_llm_question

def ask_question(project_memory: str):
    if not project_memory.strip():
        project_memory = "Student is presenting a software project."

    question = generate_llm_question(project_memory)

    if not question:
        question = "Can you explain the architecture of your project?"

    return question

