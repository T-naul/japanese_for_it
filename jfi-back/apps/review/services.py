# apps/review/services.py

import random
from django.db import transaction
from django.utils import timezone

from apps.content.models import Grammar, Vocabulary
from apps.users.models import UserGrammar, UserVocabulary

from .models import (
    ReviewContentType,
    ReviewQuestion,
    ReviewQuestionType,
    ReviewSession,
    ReviewSessionStatus,
)
from .question_generators import generate_question_for_item


class ReviewService:

    @staticmethod
    def get_available_content_summary(user):
        """
        Thống kê tổng số từ vựng và ngữ pháp đã học (learned_at IS NOT NULL) của user.
        """
        vocab_count = UserVocabulary.objects.filter(
            user=user,
            learned_at__isnull=False,
        ).count()

        grammar_count = UserGrammar.objects.filter(
            user=user,
            learned_at__isnull=False,
        ).count()

        total = vocab_count + grammar_count

        if total == 0:
            return {
                "available": False,
                "reason": "NO_LEARNED_CONTENT",
                "message": "No learned content available for review.",
                "vocabulary_count": 0,
                "grammar_count": 0,
                "total": 0,
            }

        return {
            "available": True,
            "vocabulary_count": vocab_count,
            "grammar_count": grammar_count,
            "total": total,
        }

    @classmethod
    @transaction.atomic
    def create_session(cls, user, limit=10):
        """
        Tạo ReviewSession mới và sinh các câu hỏi ReviewQuestion ngẫu nhiên từ learned content.
        """
        if limit < 1 or limit > 50:
            raise ValueError("Limit phải nằm trong khoảng từ 1 đến 50.")

        learned_vocabs = list(
            UserVocabulary.objects.filter(
                user=user,
                learned_at__isnull=False,
            ).select_related("vocabulary")
        )

        learned_grammars = list(
            UserGrammar.objects.filter(
                user=user,
                learned_at__isnull=False,
            ).select_related("grammar")
        )

        candidates = [
            (uv.vocabulary, ReviewContentType.VOCABULARY) for uv in learned_vocabs
        ] + [
            (ug.grammar, ReviewContentType.GRAMMAR) for ug in learned_grammars
        ]

        if not candidates:
            raise ValueError("No learned content available for review.")

        # Tráo đổi thứ tự ngẫu nhiên
        random.shuffle(candidates)
        selected_candidates = candidates[:limit]

        # Lấy pool các nghĩa làm distractors
        vocab_meanings = list(
            Vocabulary.objects.filter(status="accepted").values_list("meaning", flat=True)
        )
        grammar_meanings = list(
            Grammar.objects.filter(status="accepted").values_list("meaning", flat=True)
        )
        meanings_pool = vocab_meanings + grammar_meanings

        session = ReviewSession.objects.create(
            user=user,
            total_questions=len(selected_candidates),
            status=ReviewSessionStatus.ACTIVE,
        )

        questions = []
        for order, (item, c_type) in enumerate(selected_candidates, start=1):
            gen = generate_question_for_item(item, c_type, meanings_pool)

            q_obj = ReviewQuestion(
                session=session,
                content_type=c_type,
                vocabulary=item if c_type == ReviewContentType.VOCABULARY else None,
                grammar=item if c_type == ReviewContentType.GRAMMAR else None,
                question_type=gen["question_type"],
                prompt=gen["prompt"],
                choices=gen["choices"],
                correct_answer=gen["correct_answer"],
                order=order,
            )
            questions.append(q_obj)

        ReviewQuestion.objects.bulk_create(questions)
        return session

    @staticmethod
    def get_session(user, session_id):
        """
        Lấy chi tiết ReviewSession của user.
        """
        session = (
            ReviewSession.objects.filter(user=user, id=session_id)
            .prefetch_related("questions")
            .first()
        )
        if not session:
            raise ValueError("ReviewSession không tồn tại.")
        return session

    @staticmethod
    @transaction.atomic
    def submit_answer(user, session_id, question_id, user_answer_payload):
        """
        Submit đáp án cho một câu hỏi trong session.
        """
        session = ReviewSession.objects.filter(user=user, id=session_id).first()
        if not session:
            raise ValueError("ReviewSession không tồn tại.")

        question = ReviewQuestion.objects.filter(session=session, id=question_id).first()
        if not question:
            raise ValueError("ReviewQuestion không tồn tại trong session này.")

        if question.answered_at is not None:
            raise ValueError("Câu hỏi này đã được trả lời trước đó.")

        if isinstance(user_answer_payload, dict):
            submitted_val = str(user_answer_payload.get("answer", "")).strip()
        else:
            submitted_val = str(user_answer_payload).strip()

        correct_info = question.correct_answer
        if question.question_type in [
            ReviewQuestionType.MEANING_CHOICE,
            ReviewQuestionType.TRUE_FALSE,
        ]:
            expected_id = str(correct_info.get("choice_id", "")).strip().lower()
            is_correct = (submitted_val.lower() == expected_id)
            correct_display = correct_info.get("choice_id")
        else:
            expected_text = str(correct_info.get("answer_text", "")).strip().lower()
            user_str = submitted_val.lower()
            is_correct = (
                user_str == expected_text
                or user_str in expected_text
                or expected_text in user_str
            ) if user_str else False
            correct_display = correct_info.get("answer_text")

        question.user_answer = {"answer": submitted_val}
        question.is_correct = is_correct
        question.answered_at = timezone.now()
        question.save(update_fields=["user_answer", "is_correct", "answered_at"])

        session.answered_questions += 1
        if is_correct:
            session.correct_answers += 1

        if session.answered_questions >= session.total_questions:
            session.status = ReviewSessionStatus.COMPLETED
            session.completed_at = timezone.now()

        session.save(
            update_fields=[
                "answered_questions",
                "correct_answers",
                "status",
                "completed_at",
            ]
        )

        percentage = (
            round(session.correct_answers / session.total_questions * 100, 2)
            if session.total_questions > 0
            else 0.0
        )

        return {
            "question_id": str(question.id),
            "is_correct": is_correct,
            "correct_answer": correct_display,
            "answered_questions": session.answered_questions,
            "total_questions": session.total_questions,
            "correct_answers": session.correct_answers,
            "percentage": percentage,
            "session_completed": (session.status == ReviewSessionStatus.COMPLETED),
        }

    @staticmethod
    def get_session_progress(user, session_id):
        """
        Lấy tiến độ kết quả của ReviewSession.
        """
        session = ReviewSession.objects.filter(user=user, id=session_id).first()
        if not session:
            raise ValueError("ReviewSession không tồn tại.")

        percentage = (
            round(session.correct_answers / session.total_questions * 100, 2)
            if session.total_questions > 0
            else 0.0
        )

        return {
            "session_id": str(session.id),
            "status": session.status,
            "total_questions": session.total_questions,
            "answered_questions": session.answered_questions,
            "correct_answers": session.correct_answers,
            "percentage": percentage,
            "completed": (session.status == ReviewSessionStatus.COMPLETED),
        }
