import os
import sys
import sqlite3
import json
import re
import collections

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

TAXONOMY_PATTERNS = {
    'software': [
        r'\b(python|javascript|typescript|js|ts|html|css|sql|sqlite|database|api|http|git|github|bug|error|exception|traceback|refactor|function|class|import|def|return|code|script|server|docker|json|parse|regex|node|npm|pip|async|await)\b'
    ],
    'hardware': [
        r'\b(bambu|3d print|printer|printing|stl|step|cad|engine|motor|mechanic|mechanical|screw|bolt|gear|filament|nozzle|bed|layer|mesh|hardware|assembly|part|cylinder|bearing|torque|rpm|valve|exhaust|intake)\b'
    ],
    'ai_agents': [
        r'\b(agent|agents|subagent|prompt|prompts|llm|llms|gemini|antigravity|context|reasoning|model|models|sdk|token|tokens|claude|openai|gpt|system prompt|tool|mcp|rag|vector|embedding)\b'
    ],
    'finance': [
        r'\b(transaction|transactions|spending|bank|banking|receipt|order|shipping|cost|dollar|dollars|\$|account|budget|purchase|chase|financial|expense|invoice|statement|card|credit)\b'
    ],
    'creative': [
        r'\b(music|debussy|audio|video|image|images|design|writing|idea|lyric|lyrics|poem|art|color|harmony|melody|piano|composition|creative|story)\b'
    ]
}

CATEGORY_LABELS = {
    'software': '💻 Software & Systems Architecture',
    'hardware': '🛠️ Hardware & 3D Fabrication',
    'ai_agents': '🤖 AI Agents & Cognition',
    'finance': '💼 Finance & Commerce',
    'creative': '🎨 Creative, Music & Media',
    'outliers': '🔍 Outliers & Miscellanea'
}

def extract_keywords(text, top_n=10):
    if not text:
        return []
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
    stopwords = {
        'the', 'and', 'for', 'that', 'this', 'with', 'you', 'have', 'are', 'was', 'not', 'can', 'will',
        'from', 'what', 'how', 'about', 'just', 'more', 'some', 'out', 'all', 'one', 'would', 'there',
        'they', 'has', 'been', 'which', 'when', 'who', 'than', 'into', 'them', 'other', 'their', 'your'
    }
    filtered = [w for w in words if w not in stopwords]
    counts = collections.Counter(filtered)
    return [w for w, c in counts.most_common(top_n)]

def classify_thread(combined_text):
    text_lower = combined_text.lower()
    scores = {}
    
    for cat, patterns in TAXONOMY_PATTERNS.items():
        score = 0
        for pat in patterns:
            matches = re.findall(pat, text_lower)
            score += len(matches)
        scores[cat] = score
        
    total_matches = sum(scores.values())
    
    if total_matches == 0:
        primary = 'outliers'
        outlier_score = 0.95
        secondaries = []
    else:
        sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        primary = sorted_cats[0][0]
        max_score = sorted_cats[0][1]
        
        secondaries = [cat for cat, sc in sorted_cats[1:] if sc >= max_score * 0.4 and sc > 0]
        
        outlier_score = max(0.0, round(1.0 - (max_score / 10.0), 2))
        if max_score == 1 and total_matches == 1:
            outlier_score = 0.8
            
    keywords = extract_keywords(combined_text, top_n=8)
    return primary, secondaries, keywords, outlier_score

ACTIONABILITY_TIERS = {
    'one_off': '⚡ One-Off Conversation',
    'journal': '📓 Journal Entry / Reflection',
    'theory': '💡 Theoretical Concept / Hypothesis',
    'small_project': '📦 Small Project / Script',
    'large_project': '🚀 Large Project / Pipeline',
    'specialty_project': '🔬 Specialty Domain Project'
}

JOURNAL_PATTERNS = [
    r'\b(journal|today i|my goal|reflection|feel|feeling|felt|diary|personal|habit|mindset|meditation|gratitude|mood|workout|health|diet|sleep)\b'
]

THEORY_PATTERNS = [
    r'\b(theory|hypothesis|theoretical|concept|what if|philosophy|paradigm|abstract|framework|principle|speculation|thought experiment|postulate|model comparison)\b'
]

SPECIALTY_PATTERNS = [
    r'\b(stl|bambu|3d print|cad|step file|debussy|piano|harmony|composition|chord progression|agent sdk|mcp server|vector database|financial statement|balance sheet)\b'
]

def classify_actionability(combined_text, turn_count, primary_category):
    text_lower = combined_text.lower()
    tags = set()
    
    # 1. Detect Journal Patterns
    is_journal = any(re.search(pat, text_lower) for pat in JOURNAL_PATTERNS)
    if is_journal:
        tags.add('personal_reflection')

    # 2. Detect Theory Patterns
    is_theory = any(re.search(pat, text_lower) for pat in THEORY_PATTERNS)
    if is_theory:
        tags.add('brainstorming')
        tags.add('learning_research')

    # 3. Detect Code / Architecture Patterns
    code_block_count = combined_text.count('```')
    if code_block_count > 0 or 'def ' in combined_text or 'function ' in combined_text or 'import ' in combined_text:
        tags.add('code_generation')
    if 'error' in text_lower or 'bug' in text_lower or 'traceback' in text_lower or 'exception' in text_lower:
        tags.add('debugging')
    if 'architecture' in text_lower or 'pipeline' in text_lower or 'system' in text_lower:
        tags.add('architectural_design')

    # 4. Check Specialty Domain
    is_specialty = any(re.search(pat, text_lower) for pat in SPECIALTY_PATTERNS) or primary_category in ('hardware', 'creative')

    # 5. Determine Primary Actionability Tier
    if is_journal and turn_count <= 6:
        tier = 'journal'
    elif is_theory and turn_count <= 8:
        tier = 'theory'
    elif is_specialty and (turn_count >= 5 or code_block_count >= 2):
        tier = 'specialty_project'
    elif turn_count >= 9 or code_block_count >= 4:
        tier = 'large_project'
    elif turn_count >= 3 or code_block_count >= 1:
        tier = 'small_project'
    else:
        tier = 'one_off'

    tags.add(tier)
    tags.add(primary_category)

    return tier, sorted(list(tags))

def run_thread_classification(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    from src.db import init_synthesis_tables
    init_synthesis_tables(conn)

    print("Step 1: Fetching all conversation threads for taxonomy & actionability classification...")
    cursor.execute('''
        SELECT id, thread_id, prompt_text, substr(response_plain, 1, 400) as snippet
        FROM chats
        WHERE timestamp_iso != "1970-01-01 00:00:00"
        ORDER BY id ASC
    ''')
    rows = cursor.fetchall()
    
    threads_text = collections.defaultdict(list)
    for r in rows:
        gk = r['thread_id'] or str(r['id'])
        t_str = (r['prompt_text'] or "") + " " + (r['snippet'] or "")
        threads_text[gk].append(t_str)

    records = []
    category_counts = collections.Counter()
    tier_counts = collections.Counter()
    
    for gk, text_list in threads_text.items():
        combined_text = " ".join(text_list)
        turn_count = len(text_list)
        primary, secondaries, keywords, outlier_score = classify_thread(combined_text)
        actionability_tier, actionability_tags = classify_actionability(combined_text, turn_count, primary)
        
        category_counts[primary] += 1
        tier_counts[actionability_tier] += 1

        records.append((
            gk,
            primary,
            json.dumps(secondaries),
            json.dumps(keywords),
            outlier_score,
            actionability_tier,
            json.dumps(actionability_tags)
        ))
        
    print(f"Step 2: Saving taxonomy & actionability metadata for {len(records)} threads...")
    cursor.execute('DELETE FROM thread_categories;')
    cursor.executemany('''
        INSERT INTO thread_categories (group_key, primary_category, secondary_categories_json, keywords_json, outlier_score, actionability_tier, actionability_tags_json)
        VALUES (?, ?, ?, ?, ?, ?, ?);
    ''', records)
    
    conn.commit()
    conn.close()
    
    print("✅ Taxonomy Classification Complete! Domain Summary:")
    for cat_key, count in category_counts.most_common():
        label = CATEGORY_LABELS.get(cat_key, cat_key)
        print(f"  {label}: {count} threads")

    print("\n✅ Actionability Tiers Summary:")
    for tier_key, count in tier_counts.most_common():
        label = ACTIONABILITY_TIERS.get(tier_key, tier_key)
        print(f"  {label}: {count} threads")
        
    return category_counts

if __name__ == '__main__':
    project_db = '/Users/austinrognes/Documents/Projects/gemini-analyzer/data/gemini_archive.db'
    run_thread_classification(project_db)
