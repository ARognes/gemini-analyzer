#!/usr/bin/env python3
"""
Harvest Chat Narratives & Conversation Stream Sub-Division Engine
Traverses all thread files, synthesizes executive summaries, detects topic shifts,
sub-divides long-running threads into structured thematic chapters/streams, and
enriches search indices.
"""

import json
import glob
import re
import os
from collections import Counter

STOP_WORDS = {
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', "you're", "you've",
    "you'll", "you'd", 'your', 'yours', 'yourself', 'yourselves', 'he', 'him', 'his',
    'himself', 'she', "she's", 'her', 'hers', 'herself', 'it', "it's", 'its', 'itself',
    'they', 'them', 'their', 'theirs', 'themselves', 'what', 'which', 'who', 'whom',
    'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be',
    'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did', 'doing', 'a',
    'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at',
    'by', 'for', 'with', 'about', 'against', 'between', 'into', 'through', 'during',
    'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out', 'on',
    'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here', 'there', 'when',
    'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more', 'most', 'other',
    'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
    'very', 's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've",
    'now', 'd', 'll', 'm', 'o', 're', 've', 'y', 'ain', 'aren', "aren't", 'couldn',
    "couldn't", 'did', "didn't", 'does', "doesn't", 'had', "hadn't", 'has',
    "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn', "mightn't",
    'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
    'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't",
    'tell', 'explain', 'show', 'give', 'please', 'help', 'want', 'like', 'know', 'make'
}

def strip_html(html_str):
    if not html_str:
        return ''
    text = re.sub(r'<pre><code>.*?</code></pre>', ' [code block] ', html_str, flags=re.DOTALL)
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
    text = re.sub(r'\s+', ' ', text)
    return text.strip()

def extract_keywords(text, top_k=6):
    words = re.findall(r'\b[a-zA-Z0-9_\-\.]{3,}\b', text.lower())
    clean_words = [w for w in words if w not in STOP_WORDS and not w.isdigit()]
    counts = Counter(clean_words)
    return [word for word, _ in counts.most_common(top_k)]

def calculate_jaccard_similarity(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    intersection = len(set_a.intersection(set_b))
    union = len(set_a.union(set_b))
    return intersection / union if union > 0 else 0.0

def generate_stream_title(keywords, first_prompt):
    clean_prompt = re.sub(r'\s+', ' ', first_prompt).strip()
    clean_prompt = re.sub(r'^(can you|could you|please|how do I|what is|tell me about|I want to|I need to)\s+', '', clean_prompt, flags=re.IGNORECASE)
    
    if len(clean_prompt) > 4:
        words = clean_prompt.split(' ')[:6]
        snippet = ' '.join(words).strip('.,?!:;')
        if snippet:
            return snippet[0].upper() + snippet[1:]
    
    if keywords:
        return ' • '.join([k.capitalize() for k in keywords[:3]])
    
    return "General Inquiry"

def process_single_thread(thread_data):
    turns = thread_data.get('turns', [])
    n_turns = len(turns)
    
    if n_turns == 0:
        return {
            'executive_narrative': "Archived thread metadata with no recorded prompt transcript.",
            'streams': [],
            'key_insights': []
        }
        
    turn_texts = []
    turn_keywords = []
    
    for t in turns:
        p_text = t.get('prompt_text', '') or ''
        r_text = strip_html(t.get('response_html', '')) or ''
        combined = f"{p_text} {r_text[:300]}"
        turn_texts.append((p_text, r_text))
        turn_keywords.append(set(extract_keywords(combined, top_k=10)))

    # 1. Single Turn Chat
    if n_turns == 1:
        p0, r0 = turn_texts[0]
        p_clean = p0.strip()
        kw = extract_keywords(p0 + ' ' + r0, 4)
        narrative = f"Direct inquiry regarding {p_clean[:120]}{'...' if len(p_clean) > 120 else ''}."
        if r0:
            first_sent = r0.split('. ')[0]
            if len(first_sent) > 20:
                narrative += f" Provided concise guidance on {first_sent[:140]}."
                
        stream = {
            'stream_id': 1,
            'title': generate_stream_title(kw, p0),
            'turn_range': [1, 1],
            'turn_count': 1,
            'summary': narrative,
            'keywords': kw
        }
        return {
            'executive_narrative': narrative,
            'streams': [stream],
            'key_insights': [f"Core focus: {', '.join(kw[:3])}"] if kw else []
        }

    # 2. Short to Medium Multi-Turn Chat (2 to 5 turns)
    if n_turns <= 5:
        all_kw = extract_keywords(' '.join([p + ' ' + r[:200] for p, r in turn_texts]), 6)
        p0 = turn_texts[0][0]
        plast = turn_texts[-1][0]
        
        narrative = f"Focused {n_turns}-turn exploration initiated with '{p0[:80]}'."
        if plast != p0:
            narrative += f" Followed up with clarifications on '{plast[:80]}'."
            
        stream = {
            'stream_id': 1,
            'title': generate_stream_title(all_kw, p0),
            'turn_range': [1, n_turns],
            'turn_count': n_turns,
            'summary': narrative,
            'keywords': all_kw
        }
        return {
            'executive_narrative': narrative,
            'streams': [stream],
            'key_insights': [
                f"Main topic: {all_kw[0] if all_kw else 'Investigation'}",
                f"Total dialogue depth: {n_turns} iterative exchanges"
            ]
        }

    # 3. Long-Running Deep Multi-Turn Chat (6+ turns) -> Segment into Streams / Chapters
    stream_boundaries = [0]
    current_kw_window = turn_keywords[0]
    
    for i in range(1, n_turns):
        curr_kw = turn_keywords[i]
        sim = calculate_jaccard_similarity(current_kw_window, curr_kw)
        
        p_curr = turn_texts[i][0].lower()
        is_explicit_shift = any(p_curr.startswith(phrase) for phrase in [
            'now ', 'next ', 'moving on', 'another question', 'what about', 'how about',
            'change of topic', 'different question', 'switch gears', 'by the way'
        ])
        
        turns_in_current_stream = i - stream_boundaries[-1]
        if (sim < 0.08 or is_explicit_shift) and turns_in_current_stream >= 2:
            stream_boundaries.append(i)
            current_kw_window = curr_kw
        else:
            current_kw_window = current_kw_window.union(curr_kw)
            
    if len(stream_boundaries) > 1 and (n_turns - stream_boundaries[-1]) == 1:
        stream_boundaries.pop()
        
    streams = []
    for s_idx, start_idx in enumerate(stream_boundaries):
        end_idx = stream_boundaries[s_idx + 1] if (s_idx + 1) < len(stream_boundaries) else n_turns
        
        stream_turn_texts = turn_texts[start_idx:end_idx]
        stream_text_blob = ' '.join([p + ' ' + r[:200] for p, r in stream_turn_texts])
        s_kw = extract_keywords(stream_text_blob, top_k=5)
        
        first_p = stream_turn_texts[0][0]
        s_title = generate_stream_title(s_kw, first_p)
        
        s_summary = f"Covered {end_idx - start_idx} turns focusing on {s_title}. Key discussions around {', '.join(s_kw[:3])}."
        
        streams.append({
            'stream_id': s_idx + 1,
            'title': s_title,
            'turn_range': [start_idx + 1, end_idx],
            'turn_count': end_idx - start_idx,
            'summary': s_summary,
            'keywords': s_kw
        })
        
    stream_titles = [s['title'] for s in streams]
    executive_narrative = (
        f"Deep {n_turns}-turn dialogue spanning {len(streams)} thematic streams: "
        f"{' → '.join(stream_titles)}."
    )
    
    top_overall_kw = extract_keywords(' '.join([p + ' ' + r[:150] for p, r in turn_texts]), 6)
    
    return {
        'executive_narrative': executive_narrative,
        'streams': streams,
        'key_insights': [
            f"Multi-stream breadth: {len(streams)} distinct discussion phases",
            f"Core conceptual anchors: {', '.join(top_overall_kw[:4])}",
            f"Conversation longevity: {n_turns} total turns"
        ]
    }

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    threads_dir = os.path.join(base_dir, 'frontend', 'static', 'data', 'threads')
    thread_files = sorted(glob.glob(os.path.join(threads_dir, '*.json')))
    
    print(f"🌾 Harvesting narratives across {len(thread_files)} thread files...")
    
    harvest_catalog = {}
    multi_stream_count = 0
    total_streams_generated = 0
    
    for p in thread_files:
        thread_id = os.path.splitext(os.path.basename(p))[0]
        with open(p, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        res = process_single_thread(data)
        
        data['executive_narrative'] = res['executive_narrative']
        data['streams'] = res['streams']
        data['key_insights'] = res['key_insights']
        
        # Save enriched thread
        with open(p, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
        harvest_catalog[thread_id] = {
            'thread_id': thread_id,
            'turn_count': len(data.get('turns', [])),
            'stream_count': len(res['streams']),
            'executive_narrative': res['executive_narrative'],
            'streams': res['streams'],
            'key_insights': res['key_insights']
        }
        
        total_streams_generated += len(res['streams'])
        if len(res['streams']) > 1:
            multi_stream_count += 1
            
    # Save master harvest narratives index
    out_catalog_path = os.path.join(base_dir, 'frontend', 'static', 'data', 'harvest_narratives.json')
    with open(out_catalog_path, 'w', encoding='utf-8') as f:
        json.dump(harvest_catalog, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Successfully harvested {len(harvest_catalog)} thread narratives!")
    print(f"📊 Streams generated: {total_streams_generated} total ({multi_stream_count} multi-stream chapter threads)")
    print(f"📁 Master narrative index written to: {out_catalog_path}")

if __name__ == '__main__':
    main()
