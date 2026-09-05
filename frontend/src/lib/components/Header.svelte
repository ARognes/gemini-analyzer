<script>
  import { activeSubtab, stats, activeSearchQuery, searchResultsData, searchMatchingNodeIds, searchPathEdges, isSearchDrawerOpen } from '../stores.js';
  import { fetchSubgraphSearch } from '../api.js';

  let searchInputText = $state('');
  let searchDebounceTimer = null;

  function handleSearchInput(e) {
    const val = e.target.value;
    searchInputText = val;
    if (searchDebounceTimer) clearTimeout(searchDebounceTimer);

    if (!val || val.trim().length === 0) {
      activeSearchQuery.set('');
      searchResultsData.set(null);
      searchMatchingNodeIds.set(new Set());
      searchPathEdges.set(new Set());
      isSearchDrawerOpen.set(false);
      return;
    }

    searchDebounceTimer = setTimeout(async () => {
      try {
        const query = val.trim();
        const data = await fetchSubgraphSearch(query);
        activeSearchQuery.set(query);
        searchResultsData.set(data);
        searchMatchingNodeIds.set(new Set(data.matching_node_ids || []));
        searchPathEdges.set(new Set(data.matching_edge_ids || []));
        if (data.matching_node_ids && data.matching_node_ids.length > 0) {
          isSearchDrawerOpen.set(true);
        }
      } catch (err) {
        console.error('Subgraph search failed:', err);
      }
    }, 250);
  }

  function clearSearch() {
    searchInputText = '';
    activeSearchQuery.set('');
    searchResultsData.set(null);
    searchMatchingNodeIds.set(new Set());
    searchPathEdges.set(new Set());
    isSearchDrawerOpen.set(false);
  }
</script>

<header class="navbar">
  <div class="brand">
    <span class="icon">🌌</span>
    <span class="title">Gemini Constellation</span>
    <span class="badge">v2.0 Svelte</span>
  </div>

  <div class="stats-row">
    <div class="stat-pill">
      <span class="val">{$stats.total_chats.toLocaleString()}</span>
      <span class="lbl">Chats</span>
    </div>
    <div class="stat-pill">
      <span class="val">{$stats.voice_chats.toLocaleString()}</span>
      <span class="lbl">Voice Inputs</span>
    </div>
    <div class="stat-pill accent">
      <span class="val">{$stats.total_threads.toLocaleString()}</span>
      <span class="lbl">Thread Clusters</span>
    </div>
  </div>

  <!-- Interwoven Topic Subgraph Search Bar -->
  <div class="search-container">
    <span class="search-icon">🔍</span>
    <input 
      type="text"
      id="canvasSearch"
      placeholder="Search interwoven topics (e.g., 'jam', 'lock picking')..."
      value={searchInputText}
      oninput={handleSearchInput}
    />
    {#if searchInputText}
      <button class="clear-btn" onclick={clearSearch}>✕</button>
    {/if}
  </div>

  <!-- Subtabs Navigation -->
  <div class="subtabs">
    <button 
      class="subtab-btn" 
      class:active={$activeSubtab === 'topic_clusters'}
      id="subtabUnified" 
      onclick={() => activeSubtab.set('topic_clusters')}
    >
      🌌 Galaxy Graph
    </button>
    <button 
      class="subtab-btn" 
      class:active={$activeSubtab === 'd3_constellation'} 
      id="subtabD3"
      onclick={() => activeSubtab.set('d3_constellation')}
    >
      🪐 D3 Graph
    </button>
    <button 
      class="subtab-btn" 
      class:active={$activeSubtab === 'mindmap'} 
      id="subtabMindmap"
      onclick={() => activeSubtab.set('mindmap')}
    >
      🌳 Mindmap Tree
    </button>
    <button 
      class="subtab-btn" 
      class:active={$activeSubtab === 'matrix'} 
      id="subtabMatrix"
      onclick={() => activeSubtab.set('matrix')}
    >
      📊 Similarity Matrix
    </button>
  </div>
</header>

<style>
  .navbar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.25rem;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    gap: 1rem;
    z-index: 1200;
  }

  .brand {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    color: #f8fafc;
    font-size: 1.1rem;
  }

  .brand .icon {
    font-size: 1.3rem;
  }

  .brand .badge {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    border: 1px solid rgba(96, 165, 250, 0.3);
    font-size: 0.7rem;
    padding: 0.15rem 0.4rem;
    border-radius: 999px;
  }

  .stats-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }

  .stat-pill {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 0.35rem 0.75rem;
    border-radius: 8px;
    font-size: 0.8rem;
  }

  .stat-pill.accent {
    background: rgba(59, 130, 246, 0.15);
    border-color: rgba(59, 130, 246, 0.3);
  }

  .stat-pill .val {
    font-weight: 700;
    color: #f8fafc;
  }

  .stat-pill .lbl {
    color: #94a3b8;
  }

  .search-container {
    position: relative;
    display: flex;
    align-items: center;
    flex: 1;
    max-width: 380px;
  }

  .search-icon {
    position: absolute;
    left: 0.75rem;
    font-size: 0.85rem;
    opacity: 0.6;
    pointer-events: none;
  }

  .search-container input {
    width: 100%;
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(245, 158, 11, 0.3);
    color: #f8fafc;
    padding: 0.45rem 2rem 0.45rem 2.2rem;
    border-radius: 8px;
    font-size: 0.85rem;
    outline: none;
    transition: all 0.2s ease;
  }

  .search-container input:focus {
    border-color: #f59e0b;
    box-shadow: 0 0 12px rgba(245, 158, 11, 0.3);
  }

  .clear-btn {
    position: absolute;
    right: 0.6rem;
    background: none;
    border: none;
    color: #94a3b8;
    cursor: pointer;
    font-size: 0.85rem;
  }

  .subtabs {
    display: flex;
    gap: 0.35rem;
    background: rgba(30, 41, 59, 0.6);
    padding: 0.25rem;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .subtab-btn {
    background: none;
    border: none;
    color: #94a3b8;
    padding: 0.4rem 0.8rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .subtab-btn:hover {
    color: #f8fafc;
    background: rgba(255, 255, 255, 0.04);
  }

  .subtab-btn.active {
    background: #3b82f6;
    color: #ffffff;
    font-weight: 600;
    box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
  }
</style>
