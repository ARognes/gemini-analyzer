<script>
  import { 
    isSearchDrawerOpen, 
    activeSearchQuery, 
    searchResultsData 
  } from '../stores.js';

  function closeDrawer() {
    isSearchDrawerOpen.set(false);
  }

  function exportMarkdown() {
    const data = $searchResultsData;
    if (!data || !data.threads) return;

    let md = `# Interwoven Topic Subgraph Export: "${data.query}"\n\n`;
    md += `**Generated**: ${new Date().toLocaleString()}\n`;
    md += `**Total Matching Threads**: ${data.threads.length}\n`;
    md += `**Connected Path Edges**: ${data.matching_edge_ids ? data.matching_edge_ids.length : 0}\n\n`;

    data.threads.forEach((t, i) => {
      md += `### ${i + 1}. ${t.title || 'Conversation Thread'}\n`;
      md += `- **Thread ID**: \`${t.thread_id}\` | **Turns**: ${t.turn_count} | **Tier**: ${t.actionability_tier || 'standard'}\n`;
      md += `- **Domain Tag**: #${t.primary_tag || 'uncategorized'}\n\n`;

      if (t.matched_snippets && t.matched_snippets.length > 0) {
        md += `#### Matching Turn Snippets:\n`;
        t.matched_snippets.forEach(s => {
          md += `> **[${s.timestamp_iso || 'Turn'}] Prompt**: ${s.prompt_text}\n`;
          md += `> **Response**: ${s.response_plain ? s.response_plain.slice(0, 250) + '...' : ''}\n\n`;
        });
      }
      md += `---\n\n`;
    });

    const blob = new Blob([md], { type: 'text/markdown;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `subgraph_export_${data.query.replace(/\s+/g, '_')}.md`;
    link.click();
    URL.revokeObjectURL(url);
  }

  function exportJSON() {
    const data = $searchResultsData;
    if (!data) return;
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `subgraph_export_${data.query.replace(/\s+/g, '_')}.json`;
    link.click();
    URL.revokeObjectURL(url);
  }
</script>

{#if $isSearchDrawerOpen && $searchResultsData}
  <div class="drawer-overlay" onclick={closeDrawer}></div>
  <aside class="subgraph-drawer" id="queryResultsDrawer">
    <div class="drawer-header">
      <div class="header-title">
        <span class="gold-icon">🔍</span>
        <span>Subgraph: "{$activeSearchQuery}"</span>
      </div>
      <button class="close-btn" onclick={closeDrawer}>✕</button>
    </div>

    <div class="drawer-meta">
      <span>Found <strong>{$searchResultsData.threads ? $searchResultsData.threads.length : 0}</strong> matching threads</span>
      <div class="export-actions">
        <button class="export-btn md" onclick={exportMarkdown}>📥 Export MD</button>
        <button class="export-btn json" onclick={exportJSON}>📥 Export JSON</button>
      </div>
    </div>

    <div class="drawer-content">
      {#if $searchResultsData.threads && $searchResultsData.threads.length > 0}
        {#each $searchResultsData.threads as thread}
          <div class="thread-card">
            <div class="card-header">
              <span class="thread-title">{thread.title || thread.title_snippet}</span>
              <span class="tier-tag">{thread.actionability_tier || 'standard'}</span>
            </div>
            <div class="card-sub">
              <span>#{thread.primary_tag || 'general'}</span>
              <span>• {thread.turn_count} turns</span>
            </div>

            {#if thread.matched_snippets && thread.matched_snippets.length > 0}
              <div class="snippets-container">
                {#each thread.matched_snippets as snippet}
                  <div class="snippet-box">
                    <div class="snip-prompt"><strong>Prompt:</strong> {snippet.prompt_text}</div>
                    {#if snippet.response_plain}
                      <div class="snip-response"><strong>Response:</strong> {snippet.response_plain.slice(0, 180)}...</div>
                    {/if}
                  </div>
                {/each}
              </div>
            {/if}
          </div>
        {/each}
      {:else}
        <div class="empty-state">No matching interwoven threads found for "{$activeSearchQuery}".</div>
      {/if}
    </div>
  </aside>
{/if}

<style>
  .drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 1050;
  }

  .subgraph-drawer {
    position: fixed;
    top: 0;
    right: 0;
    width: 480px;
    height: 100vh;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(20px);
    border-left: 1px solid rgba(245, 158, 11, 0.3);
    z-index: 1100;
    display: flex;
    flex-direction: column;
    box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
  }

  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .header-title {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-weight: 700;
    color: #fbbf24;
    font-size: 1.05rem;
  }

  .close-btn {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.1rem;
    cursor: pointer;
  }

  .drawer-meta {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.75rem 1.25rem;
    background: rgba(30, 41, 59, 0.5);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    font-size: 0.8rem;
    color: #94a3b8;
  }

  .export-actions {
    display: flex;
    gap: 0.4rem;
  }

  .export-btn {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #fbbf24;
    padding: 0.25rem 0.5rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
  }

  .export-btn:hover {
    background: rgba(245, 158, 11, 0.3);
  }

  .drawer-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .thread-card {
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 1rem;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 0.5rem;
    margin-bottom: 0.4rem;
  }

  .thread-title {
    font-weight: 600;
    color: #f8fafc;
    font-size: 0.9rem;
  }

  .tier-tag {
    background: rgba(139, 92, 246, 0.2);
    color: #a78bfa;
    border: 1px solid rgba(139, 92, 246, 0.3);
    font-size: 0.65rem;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    white-space: nowrap;
  }

  .card-sub {
    font-size: 0.75rem;
    color: #64748b;
    margin-bottom: 0.75rem;
  }

  .snippets-container {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .snippet-box {
    background: rgba(15, 23, 42, 0.7);
    border-left: 3px solid #f59e0b;
    padding: 0.5rem 0.75rem;
    border-radius: 4px;
    font-size: 0.78rem;
    color: #cbd5e1;
  }

  .snip-prompt {
    margin-bottom: 0.2rem;
    color: #fef08a;
  }

  .snip-response {
    color: #94a3b8;
  }

  .empty-state {
    text-align: center;
    color: #64748b;
    margin-top: 3rem;
  }
</style>
