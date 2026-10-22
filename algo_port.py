import re
from typing import List, Dict, Any

def run_sentence_algo(text: str, triggers: List[str]) -> Dict[str, Any]:
    # Sentence splitting regex
    sentence_split_regex = r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s+'
    
    def get_word_count(s: str) -> int:
        words = re.findall(r"\b[\w'-]+\b", s)
        return len(words)

    def is_short_sentence(s: str) -> int:
        return get_word_count(s) < 10

    def contains_trigger(sentence: str, trig_list: List[str]) -> bool:
        for trig in trig_list:
            clean = (trig or "").strip()
            if not clean:
                continue
            safe = re.escape(clean)
            if re.search(rf"\b{safe}\b", sentence, re.IGNORECASE):
                return True
        return False

    raw_sentences = [s.strip() for s in re.split(sentence_split_regex, text) if s.strip()]
    eligible_sentences = [s for s in raw_sentences if not is_short_sentence(s)]

    flagged_sentences = []
    flagged_count = 0
    for s in eligible_sentences:
        if contains_trigger(s, triggers):
            flagged_sentences.append(s)
            flagged_count += 1

    word_count = len(re.findall(r"\b[\w'-]+\b", text))
    char_count = len(text)

    score = 0
    if word_count > 50 and len(eligible_sentences) > 0:
        score = min(100, round((flagged_count / len(eligible_sentences)) * 100))

    if score < 30:
        score = 0

    return {
        "score": score,
        "word_count": word_count,
        "char_count": char_count,
        "flagged_count": flagged_count,
        "eligible_sentence_count": len(eligible_sentences),
        "total_sentence_count": len(raw_sentences),
        "flagged_sentences": flagged_sentences
    }
