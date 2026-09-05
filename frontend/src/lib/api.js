/**
 * API Client for Gemini Analyzer Python Backend & GitHub Pages Static Fallback
 */

async function fetchWithFallback(apiPath, staticJsonPath, fallbackValue = null) {
  try {
    const res = await fetch(apiPath);
    if (res.ok) {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        return await res.json();
      }
    }
  } catch (err) {
    // API backend server is offline or unreachable (e.g. static GitHub Pages environment)
  }

  // Fallback to static JSON file relative to current page URL
  try {
    const staticUrl = new URL(staticJsonPath, window.location.href).href;
    const staticRes = await fetch(staticUrl);
    if (staticRes.ok) {
      return await staticRes.json();
    }
  } catch (err) {
    console.warn(`Failed to fetch static fallback from ${staticJsonPath}:`, err);
  }

  if (fallbackValue !== null) return fallbackValue;
  throw new Error(`Data unavailable from ${apiPath} or ${staticJsonPath}`);
}

export async function fetchStats() {
  return fetchWithFallback('/api/stats', 'data/stats.json', { total_chats: 0, voice_chats: 0, total_threads: 0 });
}

export async function fetchAnalytics() {
  return fetchWithFallback('/api/analytics', 'data/analytics.json', { daily_heatmap: {}, hourly_distribution: [], media_items: [] });
}

export async function fetchCategories() {
  return fetchWithFallback('/api/categories', 'data/categories.json', { categories_summary: [], threads: [] });
}

export async function fetchDataTags() {
  return fetchWithFallback('/api/data_tags', 'data/data_tags.json', []);
}

export async function fetchCanvasData(granularity = 'chat', minSim = 0.38) {
  return fetchWithFallback(`/api/overlap?min_similarity=${minSim}&limit=3000`, 'data/overlap.json', { nodes: [], relations: [] });
}

export async function fetchCorrelationStats(minSim = 0.30) {
  return fetchWithFallback(`/api/correlation_stats?min_similarity=${minSim}`, 'data/correlation_stats.json', { bins: [], stats: {} });
}

export async function fetchMindmapTree() {
  return fetchWithFallback('/api/mindmap_tree', 'data/mindmap_tree.json', null);
}

export async function fetchDomainMatrix(minSim = 0.38) {
  return fetchWithFallback(`/api/domain_matrix?min_similarity=${minSim}`, 'data/domain_matrix.json', { domains: [], matrix: [] });
}

export async function fetchStitchedThread(threadId) {
  if (!threadId) return null;
  
  // Try live API first
  try {
    const res = await fetch(`/api/chats?thread_id=${encodeURIComponent(threadId)}&limit=1`);
    if (res.ok) {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        const data = await res.json();
        if (data.threads && data.threads.length > 0) return data.threads[0];
      }
    }
  } catch (e) {}

  // Fallback to static per-thread JSON file
  try {
    const staticUrl = new URL(`data/threads/${threadId}.json`, window.location.href).href;
    const staticRes = await fetch(staticUrl);
    if (staticRes.ok) {
      return await staticRes.json();
    }
  } catch (e) {}

  return null;
}

export async function fetchSubgraphSearch(query) {
  if (!query || !query.trim()) {
    return { query: '', matching_node_ids: [], path_edge_ids: [], snippets: {}, total_matches: 0, threads: [] };
  }

  // Try live backend search first
  try {
    const res = await fetch(`/api/search_subgraph?q=${encodeURIComponent(query)}`);
    if (res.ok) {
      const contentType = res.headers.get('content-type') || '';
      if (contentType.includes('application/json')) {
        return await res.json();
      }
    }
  } catch (e) {}

  // Fallback to static search index
  try {
    const indexUrl = new URL('data/search_index.json', window.location.href).href;
    const res = await fetch(indexUrl);
    if (res.ok) {
      const searchIndex = await res.json();
      const cleanQ = query.trim().toLowerCase();
      const terms = cleanQ.split(/\s+/).filter(Boolean);
      
      const matches = searchIndex.filter(item => {
        const text = `${item.title} ${item.snippet}`.toLowerCase();
        return terms.every(term => text.includes(term));
      });

      const matchingIds = matches.map(m => m.id);
      const snippets = {};
      matches.forEach(m => { snippets[m.id] = m.snippet; });

      return {
        query,
        matching_node_ids: matchingIds,
        path_edge_ids: [],
        snippets,
        total_matches: matches.length,
        threads: matches
      };
    }
  } catch (e) {}

  return { query, matching_node_ids: [], path_edge_ids: [], snippets: {}, total_matches: 0, threads: [] };
}
