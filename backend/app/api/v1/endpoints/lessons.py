import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.agent.graph import latium_graph
from app.agent.professor import generate_lesson_for_student
from app.api.deps import get_current_user, get_db
from app.models.course import CourseModule, Lesson
from app.models.progress import LessonCompletion, UserProgress
from app.models.user import User
from app.schemas.evaluation import (
    ExerciseEvaluationRequest,
    ExerciseEvaluationResponse,
)
from app.schemas.lesson import (
    CourseModuleResponse,
    LessonCompleteRequest,
    LessonContent,
    LessonProgressResponse,
    LessonSummaryResponse,
)

router = APIRouter()


async def _get_or_create_user_progress(
    db: AsyncSession, user_id: uuid.UUID
) -> UserProgress:
    """Retrieve or initialize student progress pointing to Module 1, Lesson 1."""
    query = (
        select(UserProgress)
        .where(UserProgress.user_id == user_id)
        .options(
            selectinload(UserProgress.current_module),
            selectinload(UserProgress.current_lesson),
        )
    )
    result = await db.execute(query)
    progress = result.scalar_one_or_none()

    if progress is None:
        # Find first module and first lesson
        first_mod_query = (
            select(CourseModule).order_by(CourseModule.order_index).limit(1)
        )
        first_mod = (await db.execute(first_mod_query)).scalar_one_or_none()

        first_lesson = None
        if first_mod:
            first_lesson_query = (
                select(Lesson)
                .where(Lesson.module_id == first_mod.id)
                .order_by(Lesson.order_index)
                .limit(1)
            )
            first_lesson = (await db.execute(first_lesson_query)).scalar_one_or_none()

        progress = UserProgress(
            user_id=user_id,
            current_module_id=first_mod.id if first_mod else None,
            current_lesson_id=first_lesson.id if first_lesson else None,
            completed_lessons_count=0,
            total_points=0,
            current_streak_days=1,
        )
        db.add(progress)
        await db.commit()
        await db.refresh(progress)

        # Reload with relationships
        result = await db.execute(query)
        progress = result.scalar_one()

    return progress


@router.get("/modules", response_model=list[CourseModuleResponse])
async def list_course_modules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """List all course modules and lessons, marking student completion status."""
    # 1. Fetch modules with lessons
    query = (
        select(CourseModule)
        .where(CourseModule.is_published.is_(True))
        .order_by(CourseModule.order_index)
        .options(selectinload(CourseModule.lessons))
    )
    result = await db.execute(query)
    modules = result.scalars().all()

    # 2. Fetch completed lesson IDs for this user
    completions_query = select(LessonCompletion.lesson_id).where(
        LessonCompletion.user_id == current_user.id
    )
    completed_ids = set((await db.execute(completions_query)).scalars().all())

    response: list[CourseModuleResponse] = []
    for mod in modules:
        lessons_summary = [
            LessonSummaryResponse(
                id=lesson.id,
                module_id=lesson.module_id,
                order_index=lesson.order_index,
                title=lesson.title,
                pedagogical_objective=lesson.pedagogical_objective,
                grammar_topics=lesson.grammar_topics,
                is_completed=lesson.id in completed_ids,
            )
            for lesson in mod.lessons
        ]
        response.append(
            CourseModuleResponse(
                id=mod.id,
                order_index=mod.order_index,
                title=mod.title,
                description=mod.description,
                level=mod.level,
                lessons=lessons_summary,
            )
        )

    return response


@router.get("/progress", response_model=LessonProgressResponse)
async def get_student_progress(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Retrieve current student progress and stage."""
    progress = await _get_or_create_user_progress(db, current_user.id)

    mod_title = progress.current_module.title if progress.current_module else None
    lesson_title = progress.current_lesson.title if progress.current_lesson else None

    return LessonProgressResponse(
        user_id=progress.user_id,
        current_module_id=progress.current_module_id,
        current_lesson_id=progress.current_lesson_id,
        current_module_title=mod_title,
        current_lesson_title=lesson_title,
        completed_lessons_count=progress.completed_lessons_count,
        total_points=progress.total_points,
        current_streak_days=progress.current_streak_days,
    )


@router.post("/next", response_model=LessonContent)
async def generate_next_lesson(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Generate structured Latin lesson for the student based on current progress."""
    progress = await _get_or_create_user_progress(db, current_user.id)

    if not progress.current_lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma lição pendente encontrada para o aluno.",
        )

    lesson = progress.current_lesson
    module = progress.current_module

    student_name = current_user.full_name or current_user.email.split("@")[0].title()
    module_title = module.title if module else "Módulo Geral"

    content = await generate_lesson_for_student(
        lesson_id=str(lesson.id),
        student_name=student_name,
        module_title=module_title,
        lesson_title=lesson.title,
        pedagogical_objective=lesson.pedagogical_objective,
        grammar_topics=lesson.grammar_topics,
    )
    return content


@router.post("/{lesson_id}/evaluate", response_model=ExerciseEvaluationResponse)
async def evaluate_exercise(
    lesson_id: uuid.UUID,
    eval_in: ExerciseEvaluationRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Evaluate student's free-text Latin translation or composition via Censor Latium."""
    # 1. Verify lesson exists
    lesson_query = select(Lesson).where(Lesson.id == lesson_id)
    lesson = (await db.execute(lesson_query)).scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lição não encontrada.",
        )

    # 2. Invoke LangGraph evaluation workflow
    student_name = current_user.full_name or current_user.email.split("@")[0].title()
    workflow_state = await latium_graph.ainvoke(
        {
            "action_type": "evaluate_exercise",
            "lesson_id": str(lesson_id),
            "student_name": student_name,
            "evaluation_request": eval_in,
        }
    )
    result = workflow_state.get("evaluation_response")
    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao processar avaliação com o Censor Latium.",
        )

    if result.score >= 100:
        from app.services.gamification import evaluate_and_award_badges

        await evaluate_and_award_badges(
            db=db,
            user_id=current_user.id,
            trigger_event="censor_evaluation",
            context={"score": result.score, "lesson_id": str(lesson_id)},
        )

    return result


@router.post("/{lesson_id}/complete", response_model=LessonProgressResponse)
async def complete_lesson(
    lesson_id: uuid.UUID,
    completion_in: LessonCompleteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Any:
    """Mark a lesson as completed, record score and advance student to next lesson."""
    # 1. Verify lesson exists
    lesson_query = select(Lesson).where(Lesson.id == lesson_id)
    lesson = (await db.execute(lesson_query)).scalar_one_or_none()
    if not lesson:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lição não encontrada.",
        )

    # 2. Record or update LessonCompletion
    comp_query = select(LessonCompletion).where(
        LessonCompletion.user_id == current_user.id,
        LessonCompletion.lesson_id == lesson_id,
    )
    existing_completion = (await db.execute(comp_query)).scalar_one_or_none()

    if existing_completion:
        existing_completion.score = max(existing_completion.score, completion_in.score)
    else:
        new_comp = LessonCompletion(
            user_id=current_user.id,
            lesson_id=lesson_id,
            score=completion_in.score,
        )
        db.add(new_comp)

    # 3. Find next lesson in the syllabus
    next_lesson_query = (
        select(Lesson)
        .where(Lesson.order_index > lesson.order_index)
        .order_by(Lesson.order_index)
        .limit(1)
    )
    next_lesson = (await db.execute(next_lesson_query)).scalar_one_or_none()

    # 4. Update user progress
    progress = await _get_or_create_user_progress(db, current_user.id)
    if not existing_completion:
        progress.completed_lessons_count += 1
        progress.total_points += completion_in.score

    if next_lesson:
        progress.current_lesson_id = next_lesson.id
        progress.current_module_id = next_lesson.module_id

    db.add(progress)
    await db.commit()
    await db.refresh(progress)

    # 5. Evaluate and award Roman Senate Badges
    from app.services.gamification import evaluate_and_award_badges

    await evaluate_and_award_badges(
        db=db,
        user_id=current_user.id,
        trigger_event="complete_lesson",
        context={"score": completion_in.score, "lesson_id": str(lesson_id)},
    )

    # Refresh relationships efficiently without redundant full-table queries
    await db.refresh(progress, ["current_module", "current_lesson"])
    mod_title = progress.current_module.title if progress.current_module else None
    lesson_title = progress.current_lesson.title if progress.current_lesson else None

    return LessonProgressResponse(
        user_id=progress.user_id,
        current_module_id=progress.current_module_id,
        current_lesson_id=progress.current_lesson_id,
        current_module_title=mod_title,
        current_lesson_title=lesson_title,
        completed_lessons_count=progress.completed_lessons_count,
        total_points=progress.total_points,
        current_streak_days=progress.current_streak_days,
    )
