#!/usr/bin/env python3
"""
Build Macro Super-Groups & Domain Hierarchy
Groups micro-tags and clusters into 7 cohesive Macro Super-Groups with rich
metadata, domain-family color palettes, and aggregate metrics.
"""

import json
import os
import re

MACRO_DOMAINS = {
    'software': {
        'id': 'software',
        'label': 'Software & Engineering',
        'icon': '💻',
        'color': '#38bdf8',
        'base_hue': 200,
        'keywords': ['code', 'python', 'javascript', 'svelte', 'react', 'git', 'api', 'server', 'docker', 'database', 'css', 'html', 'vite', 'linux', 'bash', 'terminal', 'frontend', 'backend', 'bug', 'debug', 'function', 'class', 'repo', 'algorithm', 'web', 'sql', 'json']
    },
    'ai_agents': {
        'id': 'ai_agents',
        'label': 'AI & Autonomous Agents',
        'icon': '🧠',
        'color': '#a855f7',
        'base_hue': 270,
        'keywords': ['gemini', 'gpt', 'llm', 'prompt', 'agent', 'rag', 'embedding', 'mcp', 'transformer', 'neural', 'model', 'inference', 'vision', 'multimodal', 'antigravity', 'claude', 'token', 'fine-tune']
    },
    'hardware': {
        'id': 'hardware',
        'label': 'Hardware & Electronics',
        'icon': '⚡',
        'color': '#f59e0b',
        'base_hue': 38,
        'keywords': ['arduino', 'esp32', 'sensor', 'voltage', 'circuit', 'resistor', 'battery', 'pin', 'gpio', 'led', 'motor', 'soldering', 'relay', 'power', 'solar', 'wire', '3d print', 'cad', 'cnc', 'radio', 'rfid', 'usb']
    },
    'creative': {
        'id': 'creative',
        'label': 'Creative & Narrative',
        'icon': '🎨',
        'color': '#ec4899',
        'base_hue': 330,
        'keywords': ['story', 'character', 'plot', 'writing', 'poem', 'fiction', 'novel', 'dialogue', 'scene', 'art', 'music', 'drawing', 'design', 'audio', 'video', 'animation', 'voice', 'movie', 'game design']
    },
    'finance': {
        'id': 'finance',
        'label': 'Finance & Strategy',
        'icon': '📈',
        'color': '#10b981',
        'base_hue': 150,
        'keywords': ['money', 'invest', 'stock', 'crypto', 'budget', 'tax', 'real estate', 'loan', 'cost', 'revenue', 'market', 'portfolio', 'dividend', 'business', 'startup', 'pricing', 'roi']
    },
    'science': {
        'id': 'science',
        'label': 'Science, Health & Philosophy',
        'icon': '🔬',
        'color': '#06b6d4',
        'base_hue': 180,
        'keywords': ['physics', 'math', 'quantum', 'chemistry', 'biology', 'gravity', 'formula', 'equation', 'pendulum', 'relativity', 'energy', 'evolution', 'philosophy', 'ethics', 'logic', 'calculus', 'astronomy', 'health', 'medical', 'pain', 'heart', 'chest', 'stroke', 'alkaline', 'diet', 'sleep', 'stress', 'psychology', 'degrees of freedom', 'dimensions', 'space', 'sound', 'light']
    },
    'explorations': {
        'id': 'explorations',
        'label': 'General Life & Curiosity',
        'icon': '🧭',
        'color': '#64748b',
        'base_hue': 220,
        'keywords': []
    }
}

def classify_node_macro_domain(node):
    cat = (node.get('category') or '').lower()
    tag = (node.get('data_tag') or '').lower()
    title = (node.get('title') or '').lower()
    combined = f"{cat} {tag} {title}"
    
    if cat in MACRO_DOMAINS and cat != 'outliers':
        return cat
        
    # Test keywords
    for domain_id, domain_data in MACRO_DOMAINS.items():
        if domain_id == 'explorations':
            continue
        for kw in domain_data['keywords']:
            if re.search(r'\b' + re.escape(kw) + r'\b', combined):
                return domain_id
                
    return 'explorations'

def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    overlap_path = os.path.join(base_dir, 'frontend', 'static', 'data', 'overlap.json')
    harvest_path = os.path.join(base_dir, 'frontend', 'static', 'data', 'harvest_narratives.json')
    
    with open(overlap_path, 'r', encoding='utf-8') as f:
        overlap = json.load(f)
        
    harvest_data = {}
    if os.path.exists(harvest_path):
        with open(harvest_path, 'r', encoding='utf-8') as f:
            harvest_data = json.load(f)
            
    nodes = overlap.get('nodes', [])
    relations = overlap.get('relations', [])
    
    domain_stats = {d_id: {**d_data, 'node_count': 0, 'total_turns': 0, 'high_yield_count': 0, 'sample_titles': []} for d_id, d_data in MACRO_DOMAINS.items()}
    
    for n in nodes:
        macro = classify_node_macro_domain(n)
        n['macro_domain'] = macro
        n['macro_domain_label'] = MACRO_DOMAINS[macro]['label']
        n['macro_domain_icon'] = MACRO_DOMAINS[macro]['icon']
        n['macro_domain_color'] = MACRO_DOMAINS[macro]['color']
        
        tc = n.get('turn_count', 1)
        domain_stats[macro]['node_count'] += 1
        domain_stats[macro]['total_turns'] += tc
        if tc >= 5:
            domain_stats[macro]['high_yield_count'] += 1
            
        if len(domain_stats[macro]['sample_titles']) < 5:
            domain_stats[macro]['sample_titles'].append(n.get('title', ''))
            
        # Attach harvested executive narrative snippet if available
        h_info = harvest_data.get(n['id'])
        if h_info:
            n['executive_narrative'] = h_info.get('executive_narrative', '')
            n['stream_count'] = h_info.get('stream_count', 1)
            
    with open(overlap_path, 'w', encoding='utf-8') as f:
        json.dump(overlap, f, indent=2, ensure_ascii=False)
        
    macro_out_path = os.path.join(base_dir, 'frontend', 'static', 'data', 'macro_domains.json')
    with open(macro_out_path, 'w', encoding='utf-8') as f:
        json.dump(list(domain_stats.values()), f, indent=2, ensure_ascii=False)
        
    print(f"✅ Classified {len(nodes)} nodes across 7 Macro Super-Groups:")
    for d_id, stat in domain_stats.items():
        print(f"  {stat['icon']} {stat['label']}: {stat['node_count']} nodes ({stat['high_yield_count']} high-yield, {stat['total_turns']} turns)")
        
    print(f"📁 Macro domain taxonomy written to: {macro_out_path}")

if __name__ == '__main__':
    main()
