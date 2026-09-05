/**
 * API Client for Gemini Analyzer Python Backend
 */

export async function fetchStats() {
  const res = await fetch('/api/stats');
  if (!res.ok) throw new Error('Failed to fetch stats');
  return res.json();
}

export async function fetchAnalytics() {
  const res = await fetch('/api/analytics');
  if (!res.ok) throw new Error('Failed to fetch analytics');
  return res.json();
}

export async function fetchCategories() {
  const res = await fetch('/api/categories');
  if (!res.ok) throw new Error('Failed to fetch categories');
  return res.json();
}

export async function fetchDataTags() {
  const res = await fetch('/api/data_tags');
  if (!res.ok) throw new Error('Failed to fetch data tags');
  return res.json();
}

export async function fetchCanvasData(granularity = 'chat', minSim = 0.38) {
  const res = await fetch(`/api/overlap?min_similarity=${minSim}&limit=3000`);
  if (!res.ok) throw new Error('Failed to fetch canvas graph data');
  return res.json();
}

export async function fetchSubgraphSearch(query) {
  const res = await fetch(`/api/search_subgraph?q=${encodeURIComponent(query)}`);
  if (!res.ok) throw new Error('Failed to search subgraph');
  return res.json();
}

export async function fetchCorrelationStats(minSim = 0.30) {
  const res = await fetch(`/api/correlation_stats?min_similarity=${minSim}`);
  if (!res.ok) throw new Error('Failed to fetch correlation stats');
  return res.json();
}

export async function fetchMindmapTree() {
  const res = await fetch('/api/mindmap_tree');
  if (!res.ok) throw new Error('Failed to fetch mindmap tree');
  return res.json();
}

export async function fetchDomainMatrix(minSim = 0.38) {
  const res = await fetch(`/api/domain_matrix?min_similarity=${minSim}`);
  if (!res.ok) throw new Error('Failed to fetch domain matrix');
  return res.json();
}

export async function fetchStitchedThread(threadId) {
  const res = await fetch(`/api/chats?thread_id=${encodeURIComponent(threadId)}&limit=1`);
  if (!res.ok) throw new Error('Failed to fetch stitched thread');
  const data = await res.json();
  return data.threads && data.threads.length > 0 ? data.threads[0] : null;
}
