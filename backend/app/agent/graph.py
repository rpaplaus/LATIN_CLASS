import logging
from typing import Any, Literal, TypedDict

from langgraph.graph import END, StateGraph

from app.agent.evaluator import evaluate_student_exercise
from app.agent.professor import generate_lesson_for_student
from app.schemas.evaluation import (
    ExerciseEvaluationRequest,
    ExerciseEvaluationResponse,
)
from app.schemas.lesson import LessonContent

logger = logging.getLogger(__name__)


class LatiumWorkflowState(TypedDict, total=False):
    """Unified LangGraph state for the Latium AI multi-agent orchestration."""

    action_type: Literal["generate_lesson", "evaluate_exercise"]
    student_name: str
    lesson_id: str
    module_title: str
    lesson_title: str
    pedagogical_objective: str
    grammar_topics: list[str]

    # Evaluation specific state
    evaluation_request: ExerciseEvaluationRequest
    evaluation_response: ExerciseEvaluationResponse

    # Tutor specific state
    library_context: str
    lesson_content: LessonContent


async def router_node(state: LatiumWorkflowState) -> dict[str, Any]:
    """Inspect the incoming intent and route to the appropriate specialized LLM agent."""
    action = state.get("action_type", "generate_lesson")
    logger.info("LangGraph router directed workflow to action: %s", action)
    return {"action_type": action}


def route_decision(state: LatiumWorkflowState) -> str:
    """Conditional edge router determining the target node."""
    if state.get("action_type") == "evaluate_exercise":
        return "evaluator"
    return "tutor"


async def tutor_node(state: LatiumWorkflowState) -> dict[str, Any]:
    """Tutor Node: Claude 3.5 Sonnet generates the structured Latin lesson enriched with Alexandria RAG."""
    from app.agent.tools import search_latin_library

    library_context = ""
    try:
        query_text = (
            f"{state.get('lesson_title', '')} "
            f"{state.get('pedagogical_objective', '')} "
            f"{' '.join(state.get('grammar_topics', []))}"
        )
        library_context = await search_latin_library.ainvoke(
            {"query": query_text.strip()}
        )
    except Exception as exc:
        logger.warning(
            "Alexandria RAG pre-retrieval failed (%s). Continuing without it.", exc
        )

    content = await generate_lesson_for_student(
        lesson_id=state.get("lesson_id", ""),
        student_name=state.get("student_name", "Discipulus"),
        module_title=state.get("module_title", "Módulo Geral"),
        lesson_title=state.get("lesson_title", "Lição Geral"),
        pedagogical_objective=state.get("pedagogical_objective", "Aprender Latim"),
        grammar_topics=state.get("grammar_topics", []),
        library_context=library_context or None,
    )
    return {"lesson_content": content, "library_context": library_context}


async def evaluator_node(state: LatiumWorkflowState) -> dict[str, Any]:
    """Evaluator Node: GPT-4o performs analytical morphological and syntactic grading."""
    req = state.get("evaluation_request")
    if not req:
        raise ValueError("evaluation_request is required for evaluator_node")

    eval_result = await evaluate_student_exercise(req)
    return {"evaluation_response": eval_result}


def create_latium_graph() -> Any:
    """Build and compile the multi-model LangGraph StateGraph."""
    workflow = StateGraph(LatiumWorkflowState)

    workflow.add_node("router", router_node)
    workflow.add_node("tutor", tutor_node)
    workflow.add_node("evaluator", evaluator_node)

    workflow.set_entry_point("router")

    workflow.add_conditional_edges(
        "router",
        route_decision,
        {
            "tutor": "tutor",
            "evaluator": "evaluator",
        },
    )

    workflow.add_edge("tutor", END)
    workflow.add_edge("evaluator", END)

    return workflow.compile()


latium_graph = create_latium_graph()
