"""
Works out which news story each spoken line is about, so the video can
show a headline card that changes with the conversation.

No extra model call: the script already quotes the companies, numbers and
places from the shortlist, so distinctive-word overlap against each
headline is enough. A line that matches nothing keeps the previous card,
which is what you want mid-discussion of one story.
"""
import re

STOP = {
    "the", "a", "an", "and", "or", "but", "of", "to", "in", "on", "for",
    "with", "at", "by", "from", "as", "is", "are", "was", "were", "be",
    "been", "it", "its", "this", "that", "these", "those", "has", "have",
    "had", "will", "would", "can", "could", "says", "said", "say", "new",
    "after", "over", "more", "than", "up", "down", "out", "about", "into",
    "we", "you", "they", "he", "she", "i", "so", "not", "no", "yes",
    "what", "how", "why", "when", "who", "all", "one", "two", "first",
    "now", "today", "year", "week", "day", "per", "cent", "percent",
}

MIN_HITS = 2


def tokens(text):
    words = re.findall(r"[a-z0-9]+", (text or "").lower())
    return {w for w in words if len(w) > 2 and w not in STOP}


def assign(timeline, stories):
    """Returns a list, one entry per timeline line: the index of the story
    that line is about, or None before any story is recognised."""
    story_tokens = [tokens(s.get("title", "")) for s in stories]
    out, current = [], None
    for item in timeline:
        line = tokens(item.get("text", ""))
        best, best_hits = None, 0
        for i, st in enumerate(story_tokens):
            hits = len(line & st)
            if hits > best_hits:
                best, best_hits = i, hits
        if best is not None and best_hits >= MIN_HITS:
            current = best
        out.append(current)
    return out


def spans(timeline, assigned):
    """Collapse per-line assignments into (start, end, story_index) runs,
    so each headline card is drawn once rather than per line."""
    runs = []
    for item, idx in zip(timeline, assigned):
        if idx is None:
            continue
        if runs and runs[-1][2] == idx:
            runs[-1][1] = item["end"]
        else:
            runs.append([item["start"], item["end"], idx])
    return [(a, b, i) for a, b, i in runs]
