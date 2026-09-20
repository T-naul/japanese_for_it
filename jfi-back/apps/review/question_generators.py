# apps/review/question_generators.py

import random
from apps.review.models import ReviewContentType, ReviewQuestionType


def generate_meaning_choice(content_item, content_type, meanings_pool):
    """
    Sinh câu hỏi meaning_choice (Trắc nghiệm 4 lựa chọn).
    """
    if content_type == ReviewContentType.VOCABULARY:
        kanji = content_item.kanji
        hiragana = content_item.hiragana
        prompt = f"{kanji}（{hiragana}）の意味は？" if kanji != hiragana else f"{hiragana}の意味は？"
        correct_meaning = content_item.meaning
    else:
        pattern = content_item.pattern
        prompt = f"「{pattern}」の意味は？"
        correct_meaning = content_item.meaning

    # Lọc distractors không trùng với correct_meaning
    available_distractors = [m for m in meanings_pool if m != correct_meaning]
    # Lấy tối đa 3 distractors ngẫu nhiên không lặp lại
    num_distractors = min(3, len(set(available_distractors)))
    distractor_choices = random.sample(list(set(available_distractors)), num_distractors) if num_distractors > 0 else []

    all_choice_texts = [correct_meaning] + distractor_choices
    random.shuffle(all_choice_texts)

    choice_labels = ["A", "B", "C", "D"]
    choices = []
    correct_choice_id = "A"

    for idx, text in enumerate(all_choice_texts):
        c_id = choice_labels[idx] if idx < len(choice_labels) else f"C{idx+1}"
        choices.append({"id": c_id, "text": text})
        if text == correct_meaning:
            correct_choice_id = c_id

    return {
        "prompt": prompt,
        "choices": choices,
        "correct_answer": {"choice_id": correct_choice_id, "correct_text": correct_meaning},
    }


def generate_true_false(content_item, content_type, meanings_pool):
    """
    Sinh câu hỏi true_false (Đúng / Sai).
    """
    if content_type == ReviewContentType.VOCABULARY:
        item_text = content_item.kanji
        correct_meaning = content_item.meaning
    else:
        item_text = content_item.pattern
        correct_meaning = content_item.meaning

    is_true = random.choice([True, False])
    available_distractors = [m for m in meanings_pool if m != correct_meaning]

    if is_true or not available_distractors:
        display_meaning = correct_meaning
        correct_choice_id = "true"
    else:
        display_meaning = random.choice(available_distractors)
        correct_choice_id = "false"

    prompt = f"「{item_text}」は「{display_meaning}」という意味です。"
    choices = [
        {"id": "true", "text": "Đúng"},
        {"id": "false", "text": "Sai"},
    ]

    return {
        "prompt": prompt,
        "choices": choices,
        "correct_answer": {"choice_id": correct_choice_id, "correct_text": correct_meaning},
    }


def generate_translation(content_item, content_type):
    """
    Sinh câu hỏi translation (Dịch thuật / Tự luận).
    """
    if content_type == ReviewContentType.VOCABULARY:
        if content_item.example and content_item.example.strip():
            prompt = f"Dịch câu sau: {content_item.example}"
            correct_meaning = content_item.meaning
        else:
            prompt = f"Dịch nghĩa từ: {content_item.kanji} ({content_item.hiragana})"
            correct_meaning = content_item.meaning
    else:
        if content_item.example and content_item.example.strip():
            prompt = f"Dịch mấu câu ví dụ: {content_item.example}"
            correct_meaning = content_item.meaning
        else:
            prompt = f"Giải thích nghĩa cấu trúc: {content_item.pattern}"
            correct_meaning = content_item.meaning

    return {
        "prompt": prompt,
        "choices": [],
        "correct_answer": {"answer_text": correct_meaning},
    }


def generate_question_for_item(content_item, content_type, meanings_pool):
    """
    Chọn ngẫu nhiên loại câu hỏi (meaning_choice, true_false, translation) cho content_item.
    """
    q_type = random.choice([
        ReviewQuestionType.MEANING_CHOICE,
        ReviewQuestionType.TRUE_FALSE,
        ReviewQuestionType.TRANSLATION,
    ])

    if q_type == ReviewQuestionType.MEANING_CHOICE:
        generated = generate_meaning_choice(content_item, content_type, meanings_pool)
    elif q_type == ReviewQuestionType.TRUE_FALSE:
        generated = generate_true_false(content_item, content_type, meanings_pool)
    else:
        generated = generate_translation(content_item, content_type)

    return {
        "question_type": q_type,
        "prompt": generated["prompt"],
        "choices": generated["choices"],
        "correct_answer": generated["correct_answer"],
    }
