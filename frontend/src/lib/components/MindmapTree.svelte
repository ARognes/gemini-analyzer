<script>
  import { onMount } from 'svelte';
  import { fetchMindmapTree } from '../api.js';

  let treeData = $state(null);
  let expandedNodes = $state(new Set(['root']));

  onMount(async () => {
    try {
      treeData = await fetchMindmapTree();
      if (treeData && treeData.children) {
        // Expand root and first domain by default
        const newSet = new Set(['root']);
        treeData.children.forEach(c => newSet.add(c.id));
        expandedNodes = newSet;
      }
    } catch (err) {
      console.error('Failed to load mindmap tree:', err);
    }
  });

  function toggleNode(nodeId) {
    const newSet = new Set(expandedNodes);
    if (newSet.has(nodeId)) {
      newSet.delete(nodeId);
    } else {
      newSet.add(nodeId);
    }
    expandedNodes = newSet;
  }
</script>

<div class="mindmap-container">
  {#if treeData}
    <div class="tree-root">
      <div class="node-item level-0" onclick={() => toggleNode(treeData.id)}>
        <span class="icon">{expandedNodes.has(treeData.id) ? '📂' : '📁'}</span>
        <span class="label">Gemini Taxonomy ({treeData.thread_count} threads)</span>
      </div>

      {#if expandedNodes.has(treeData.id) && treeData.children}
        <div class="children-block">
          {#each treeData.children as domain}
            <div class="tree-branch">
              <div class="node-item level-1" onclick={() => toggleNode(domain.id)}>
                <span class="icon">{expandedNodes.has(domain.id) ? '📂' : '📁'}</span>
                <span class="label">{domain.name}</span>
                <span class="count">({domain.thread_count})</span>
              </div>

              {#if expandedNodes.has(domain.id) && domain.children}
                <div class="children-block">
                  {#each domain.children as tierBranch}
                    <div class="tree-branch">
                      <div class="node-item level-2" onclick={() => toggleNode(tierBranch.id)}>
                        <span class="icon">{expandedNodes.has(tierBranch.id) ? '📂' : '📁'}</span>
                        <span class="label">{tierBranch.name}</span>
                        <span class="count">({tierBranch.thread_count})</span>
                      </div>

                      {#if expandedNodes.has(tierBranch.id) && tierBranch.children}
                        <div class="children-block">
                          {#each tierBranch.children as leaf}
                            <div class="node-item level-3 leaf">
                              <span class="icon">💬</span>
                              <span class="label">{leaf.name}</span>
                              <span class="turns">• {leaf.turn_count} turns</span>
                            </div>
                          {/each}
                        </div>
                      {/if}
                    </div>
                  {/each}
                </div>
              {/if}
            </div>
          {/each}
        </div>
      {/if}
    </div>
  {:else}
    <div class="loading">Loading mindmap taxonomy tree...</div>
  {/if}
</div>

<style>
  .mindmap-container {
    width: 100%;
    height: 100%;
    overflow-y: auto;
    padding: 2rem;
    background: #090d16;
    color: #f8fafc;
  }

  .tree-root {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    max-width: 900px;
    margin: 0 auto;
  }

  .tree-branch {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .node-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.8rem;
    border-radius: 8px;
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    cursor: pointer;
    font-size: 0.85rem;
    transition: all 0.15s ease;
  }

  .node-item:hover {
    background: rgba(51, 65, 85, 0.7);
    border-color: rgba(255, 255, 255, 0.15);
  }

  .node-item.level-0 {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.4);
    font-weight: 700;
    font-size: 1rem;
    color: #60a5fa;
  }

  .node-item.level-1 {
    font-weight: 600;
    color: #cbd5e1;
  }

  .node-item.level-2 {
    color: #94a3b8;
  }

  .node-item.leaf {
    cursor: default;
    background: rgba(15, 23, 42, 0.6);
    border-left: 3px solid #3b82f6;
  }

  .label {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    line-height: 1.35;
  }

  .children-block {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    padding-left: 1.5rem;
    border-left: 1px dashed rgba(255, 255, 255, 0.1);
    margin-left: 0.75rem;
  }

  .count {
    color: #64748b;
    font-size: 0.75rem;
  }

  .turns {
    color: #64748b;
    font-size: 0.75rem;
    margin-left: auto;
  }

  .loading {
    text-align: center;
    color: #64748b;
    margin-top: 5rem;
  }
</style>
