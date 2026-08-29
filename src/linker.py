import os
import sys
import sqlite3
import json
import re
import collections
import math

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def compute_tfidf_vectors(threads_dict):
    # Calculate Document Frequencies
    doc_freq = collections.Counter()
    total_docs = len(threads_dict)
    
    threads_terms = {}
    for key, text in threads_dict.items():
        terms = set(re.findall(r'\b[a-zA-Z]{3,}\b', text.lower()))
        threads_terms[key] = terms
        for term in terms:
            doc_freq[term] += 1
            
    # IDF calculation
    idf = {}
    for term, df in doc_freq.items():
        if df > 1 and df < total_docs * 0.4:
            idf[term] = math.log10(total_docs / (1 + df))
            
    # Compute Normalized Sparse Vector (term: tfidf_weight)
    vectors = {}
    for key, text in threads_dict.items():
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        tf = collections.Counter(words)
        vec = {}
        norm_sq = 0.0
        for term, cnt in tf.items():
            if term in idf:
                w = cnt * idf[term]
                vec[term] = w
                norm_sq += w * w
        norm = math.sqrt(norm_sq)
        if norm > 0:
            for term in vec:
                vec[term] /= norm
            vectors[key] = vec
            
    return vectors

def cosine_similarity(v1, v2):
    # Dot product of unit vectors
    if len(v1) > len(v2):
        v1, v2 = v2, v1
    dot = sum(w * v2.get(term, 0.0) for term, w in v1.items())
    return dot

def run_knowledge_linker(db_path, min_similarity=0.38):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    from src.db import init_synthesis_tables
    init_synthesis_tables(conn)

    print("Step 1: Fetching thread texts for Knowledge Overlap linking...")
    cursor.execute('''
        SELECT 
            COALESCE(NULLIF(thread_id, ''), CAST(id AS TEXT)) as group_key,
            MIN(timestamp_iso) as first_ts,
            GROUP_CONCAT(prompt_text, ' ') as all_prompts
        FROM chats
        WHERE timestamp_iso != "1970-01-01 00:00:00"
        GROUP BY group_key
        ORDER BY first_ts ASC
    ''')
    rows = cursor.fetchall()
    
    threads_dict = {}
    timestamps = {}
    for r in rows:
        gk = r['group_key']
        threads_dict[gk] = r['all_prompts'] or ""
        timestamps[gk] = r['first_ts']

    print("Step 2: Computing TF-IDF vectors across threads...")
    vectors = compute_tfidf_vectors(threads_dict)
    
    keys = list(vectors.keys())
    total_keys = len(keys)
    print(f"Step 3: Calculating pairwise cosine similarities across {total_keys} threads...")
    
    relations = []
    for i in range(total_keys):
        k1 = keys[i]
        v1 = vectors[k1]
        for j in range(i + 1, total_keys):
            k2 = keys[j]
            v2 = vectors[k2]
            
            sim = cosine_similarity(v1, v2)
            if sim >= min_similarity:
                shared_terms = sorted(list(set(v1.keys()) & set(v2.keys())), key=lambda t: v1[t] * v2[t], reverse=True)[:5]
                relations.append((
                    k1,
                    k2,
                    round(sim, 3),
                    json.dumps(shared_terms)
                ))

    print(f"Step 4: Saving {len(relations)} cross-thread knowledge overlap links...")
    cursor.execute('DELETE FROM thread_relations;')
    cursor.executemany('''
        INSERT INTO thread_relations (source_key, target_key, similarity_score, shared_topics_json)
        VALUES (?, ?, ?, ?);
    ''', relations)
    
    conn.commit()
    conn.close()
    print("✅ Knowledge Overlap Linker Complete!")
    return len(relations)

if __name__ == '__main__':
    project_db = '/Users/austinrognes/Documents/Projects/gemini-analyzer/data/gemini_archive.db'
    run_knowledge_linker(project_db)
