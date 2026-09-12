<script>
  import { 
    hideOneOffChats, 
    selectedActionabilityTier, 
    minTurnsFilter, 
    maxTurnsFilter, 
    minEdgesFilter,
    maxEdgesFilter,
    showUnlinkedNodes,
    showUngroupedNodes,
    allGroupsEnabled,
    selectedGroupTags,
    availableGroupTags,
    degreeHistogramData,
    turnsHistogramData,
    isLayerFiltersOpen,
    correlationThresholdPct,
    isCorrelationModalOpen 
  } from '../stores.js';

  let groupSearchQuery = $state('');

  function toggleOneOffs() {
    hideOneOffChats.update(v => !v);
  }

  function toggleUnlinked() {
    showUnlinkedNodes.update(v => !v);
  }

  function toggleUngrouped() {
    showUngroupedNodes.update(v => !v);
  }

  function selectTier(tier) {
    selectedActionabilityTier.set(tier);
  }

  function openCorrModal() {
    isCorrelationModalOpen.set(true);
  }

  function toggleLayerPanel() {
    isLayerFiltersOpen.update(v => !v);
  }

  function selectAllGroups() {
    allGroupsEnabled.set(true);
    selectedGroupTags.set(new Set());
  }

  function clearAllGroups() {
    allGroupsEnabled.set(false);
    selectedGroupTags.set(new Set());
  }

  function toggleGroupTag(tag) {
    selectedGroupTags.update(set => {
      const next = new Set(set);
      if ($allGroupsEnabled) {
        allGroupsEnabled.set(false);
        // Deselect only this tag if all were on
        $availableGroupTags.forEach(g => {
          if (g.tag !== tag) next.add(g.tag);
        });
      } else {
        if (next.has(tag)) {
          next.delete(tag);
        } else {
          next.add(tag);
        }
        if (next.size === $availableGroupTags.length) {
          allGroupsEnabled.set(true);
          return new Set();
        }
      }
      return next;
    });
  }

  function resetAllFilters() {
    hideOneOffChats.set(false);
    selectedActionabilityTier.set('');
    minTurnsFilter.set(1);
    maxTurnsFilter.set(100);
    minEdgesFilter.set(0);
    maxEdgesFilter.set(50);
    showUnlinkedNodes.set(true);
    showUngroupedNodes.set(true);
    allGroupsEnabled.set(true);
    selectedGroupTags.set(new Set());
  }

  let filteredGroupTags = $derived(
    ($availableGroupTags || []).filter(g => 
      !groupSearchQuery || g.tag.toLowerCase().includes(groupSearchQuery.toLowerCase())
    )
  );

  let activeFiltersCount = $derived(
    ($hideOneOffChats ? 1 : 0) +
    ($selectedActionabilityTier ? 1 : 0) +
    ($minTurnsFilter > 1 || $maxTurnsFilter < 100 ? 1 : 0) +
    ($minEdgesFilter > 0 || $maxEdgesFilter < 50 ? 1 : 0) +
    (!$showUnlinkedNodes ? 1 : 0) +
    (!$showUngroupedNodes ? 1 : 0) +
    (!$allGroupsEnabled ? 1 : 0)
  );
</script>

<div class="filter-system">
  <!-- Top Horizontal Filter Strip -->
  <div class="filter-bar">
    <!-- Layer Filters Expander Button -->
    <button 
      class="layer-toggle-btn" 
      class:active={$isLayerFiltersOpen}
      onclick={toggleLayerPanel}
    >
      <span class="icon">🎛️</span>
      <span class="label">Layering Filters & Scales</span>
      {#if activeFiltersCount > 0}
        <span class="filter-count-badge">{activeFiltersCount}</span>
      {/if}
      <span class="chevron">{$isLayerFiltersOpen ? '▲' : '▼'}</span>
    </button>

    <!-- Actionability Tier Filter Pills -->
    <div class="filter-group">
      <span class="group-label">Tier:</span>
      <button 
        class="pill-btn" 
        class:active={$selectedActionabilityTier === ''}
        onclick={() => selectTier('')}
      >
        All
      </button>
      <button 
        class="pill-btn tier-project" 
        class:active={$selectedActionabilityTier === 'large_project'}
        onclick={() => selectTier('large_project')}
      >
        🚀 Projects
      </button>
      <button 
        class="pill-btn tier-standard" 
        class:active={$selectedActionabilityTier === 'standard'}
        onclick={() => selectTier('standard')}
      >
        💬 Threads
      </button>
    </div>

    <!-- Quick Pre-Filters & Unlinked Toggles -->
    <div class="filter-group">
      <span class="group-label">Quick:</span>
      <button 
        class="toggle-pill" 
        class:active={!$showUnlinkedNodes}
        onclick={toggleUnlinked}
        title="Toggle visibility of chats with 0 edge connections"
      >
        🔗 Unlinked: <span class="state">{#if $showUnlinkedNodes}SHOWN{:else}HIDDEN{/if}</span>
      </button>

      <button 
        class="toggle-pill" 
        class:active={!$showUngroupedNodes}
        onclick={toggleUngrouped}
        title="Toggle visibility of chats with no group"
      >
        🏷️ Ungrouped: <span class="state">{#if $showUngroupedNodes}SHOWN{:else}HIDDEN{/if}</span>
      </button>
    </div>

    <!-- Correlation Cutoff Spectrum Trigger & Reset -->
    <div class="filter-group right-group">
      <button class="corr-btn" onclick={openCorrModal}>
        📊 Similarity: <span class="val">{$correlationThresholdPct}%</span>
      </button>
      {#if activeFiltersCount > 0}
        <button class="reset-btn" onclick={resetAllFilters} title="Reset all filters">
          ↺ Reset
        </button>
      {/if}
    </div>
  </div>

  <!-- Expandable Layering Filters & Histograms Drawer -->
  {#if $isLayerFiltersOpen}
    <div class="layer-panel">
      <!-- Section 1: Edge Connections Range Scale with Live Histogram -->
      <div class="panel-section">
        <div class="section-header">
          <div class="title-with-badge">
            <span class="section-icon">🔗</span>
            <span class="section-title">Edge Connections Range</span>
            <span class="range-badge">{$minEdgesFilter} – {$maxEdgesFilter} edges</span>
          </div>
          <button class="mini-reset" onclick={() => { minEdgesFilter.set(0); maxEdgesFilter.set(50); }}>Reset</button>
        </div>

        <!-- Histogram Distribution SVG -->
        <div class="histogram-box">
          <svg class="hist-svg" viewBox="0 0 300 45" preserveAspectRatio="none">
            {#if $degreeHistogramData && $degreeHistogramData.length > 0}
              {@const maxCount = Math.max(...$degreeHistogramData.map(d => d.count), 1)}
              {#each $degreeHistogramData as d, idx}
                {@const barH = Math.max(2, (d.count / maxCount) * 40)}
                {@const inRange = d.bin >= $minEdgesFilter && d.bin <= $maxEdgesFilter}
                <rect 
                  x={idx * (300 / $degreeHistogramData.length)} 
                  y={45 - barH} 
                  width={Math.max(1.5, (300 / $degreeHistogramData.length) - 1)} 
                  height={barH} 
                  fill={inRange ? '#38bdf8' : 'rgba(100, 116, 139, 0.25)'}
                  rx="1"
                />
              {/each}
            {/if}
          </svg>
          <div class="slider-dual">
            <div class="slider-row">
              <span class="slider-lbl">Min ({$minEdgesFilter}):</span>
              <input type="range" min="0" max="50" bind:value={$minEdgesFilter} />
            </div>
            <div class="slider-row">
              <span class="slider-lbl">Max ({$maxEdgesFilter}):</span>
              <input type="range" min="0" max="50" bind:value={$maxEdgesFilter} />
            </div>
          </div>
        </div>
      </div>

      <!-- Section 2: Node Turn Size Range Scale with Live Histogram -->
      <div class="panel-section">
        <div class="section-header">
          <div class="title-with-badge">
            <span class="section-icon">💬</span>
            <span class="section-title">Chat Turn Depth Range</span>
            <span class="range-badge">{$minTurnsFilter} – {$maxTurnsFilter} turns</span>
          </div>
          <button class="mini-reset" onclick={() => { minTurnsFilter.set(1); maxTurnsFilter.set(100); }}>Reset</button>
        </div>

        <!-- Histogram Distribution SVG -->
        <div class="histogram-box">
          <svg class="hist-svg" viewBox="0 0 300 45" preserveAspectRatio="none">
            {#if $turnsHistogramData && $turnsHistogramData.length > 0}
              {@const maxCount = Math.max(...$turnsHistogramData.map(d => d.count), 1)}
              {#each $turnsHistogramData as d, idx}
                {@const barH = Math.max(2, (d.count / maxCount) * 40)}
                {@const inRange = d.bin >= $minTurnsFilter && d.bin <= $maxTurnsFilter}
                <rect 
                  x={idx * (300 / $turnsHistogramData.length)} 
                  y={45 - barH} 
                  width={Math.max(1.5, (300 / $turnsHistogramData.length) - 1)} 
                  height={barH} 
                  fill={inRange ? '#818cf8' : 'rgba(100, 116, 139, 0.25)'}
                  rx="1"
                />
              {/each}
            {/if}
          </svg>
          <div class="slider-dual">
            <div class="slider-row">
              <span class="slider-lbl">Min ({$minTurnsFilter}):</span>
              <input type="range" min="1" max="100" bind:value={$minTurnsFilter} />
            </div>
            <div class="slider-row">
              <span class="slider-lbl">Max ({$maxTurnsFilter}):</span>
              <input type="range" min="1" max="100" bind:value={$maxTurnsFilter} />
            </div>
          </div>
        </div>
      </div>

      <!-- Section 3: Group Filter Matrix -->
      <div class="panel-section group-section">
        <div class="section-header">
          <div class="title-with-badge">
            <span class="section-icon">🏷️</span>
            <span class="section-title">Group Filters ({$availableGroupTags.length} Groups)</span>
          </div>
          <div class="group-quick-actions">
            <button class="action-btn" class:active={$allGroupsEnabled} onclick={selectAllGroups}>All Groups</button>
            <button class="action-btn" onclick={clearAllGroups}>Deselect All</button>
            <button class="action-btn" class:active={$showUngroupedNodes} onclick={toggleUngrouped}>
              {$showUngroupedNodes ? '✓ Ungrouped' : '✕ Ungrouped'}
            </button>
          </div>
        </div>

        <input 
          type="text" 
          class="group-search" 
          placeholder="Filter group list by keyword..." 
          bind:value={groupSearchQuery} 
        />

        <div class="group-chips-container">
          {#each filteredGroupTags as g}
            {@const isSelected = $allGroupsEnabled || $selectedGroupTags.has(g.tag)}
            <button 
              class="group-chip" 
              class:selected={isSelected}
              onclick={() => toggleGroupTag(g.tag)}
            >
              <span class="chip-dot"></span>
              <span class="chip-tag">{g.tag}</span>
              <span class="chip-count">{g.count}</span>
            </button>
          {/each}
        </div>
      </div>
    </div>
  {/if}
</div>

<style>
  .filter-system {
    display: flex;
    flex-direction: column;
    width: 100%;
    z-index: 90;
    background: rgba(15, 23, 42, 0.85);
    backdrop-filter: blur(14px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .filter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 1.25rem;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .layer-toggle-btn {
    display: flex;
    align-items: center;
    gap: 0.45rem;
    background: rgba(59, 130, 246, 0.15);
    border: 1px solid rgba(59, 130, 246, 0.4);
    color: #60a5fa;
    padding: 0.35rem 0.8rem;
    border-radius: 8px;
    font-size: 0.8rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .layer-toggle-btn:hover {
    background: rgba(59, 130, 246, 0.25);
    border-color: #3b82f6;
    color: #ffffff;
  }

  .layer-toggle-btn.active {
    background: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
    box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
  }

  .filter-count-badge {
    background: #f59e0b;
    color: #0f172a;
    font-size: 0.65rem;
    font-weight: 800;
    padding: 0.1rem 0.4rem;
    border-radius: 10px;
  }

  .chevron {
    font-size: 0.65rem;
    opacity: 0.8;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .right-group {
    margin-left: auto;
  }

  .group-label {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 600;
    margin-right: 0.2rem;
  }

  .pill-btn {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .pill-btn:hover {
    background: rgba(51, 65, 85, 0.8);
    color: #f8fafc;
  }

  .pill-btn.active {
    background: #3b82f6;
    border-color: #3b82f6;
    color: #ffffff;
    font-weight: 600;
  }

  .pill-btn.tier-project.active {
    background: #8b5cf6;
    border-color: #8b5cf6;
  }

  .toggle-pill {
    background: rgba(30, 41, 59, 0.7);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    padding: 0.25rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .toggle-pill.active {
    background: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.4);
    color: #fbbf24;
  }

  .toggle-pill .state {
    font-weight: 700;
  }

  .corr-btn {
    background: rgba(245, 158, 11, 0.15);
    border: 1px solid rgba(245, 158, 11, 0.35);
    color: #fbbf24;
    padding: 0.3rem 0.75rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .corr-btn:hover {
    background: rgba(245, 158, 11, 0.25);
    border-color: #f59e0b;
  }

  .corr-btn .val {
    color: #ffffff;
  }

  .reset-btn {
    background: rgba(239, 68, 68, 0.15);
    border: 1px solid rgba(239, 68, 68, 0.35);
    color: #f87171;
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.75rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s ease;
  }

  .reset-btn:hover {
    background: rgba(239, 68, 68, 0.25);
    color: #ffffff;
  }

  /* Expandable Layer Panel */
  .layer-panel {
    display: grid;
    grid-template-columns: 1fr 1fr 1.6fr;
    gap: 1.25rem;
    padding: 1rem 1.25rem 1.25rem;
    background: rgba(10, 15, 29, 0.95);
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    animation: slideDown 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  }

  @keyframes slideDown {
    from { opacity: 0; transform: translateY(-8px); }
    to { opacity: 1; transform: translateY(0); }
  }

  .panel-section {
    display: flex;
    flex-direction: column;
    gap: 0.6rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 8px;
    padding: 0.75rem;
  }

  .section-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
  }

  .title-with-badge {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .section-icon {
    font-size: 0.9rem;
  }

  .section-title {
    font-size: 0.8rem;
    font-weight: 700;
    color: #e2e8f0;
  }

  .range-badge {
    font-size: 0.7rem;
    font-weight: 700;
    background: rgba(56, 189, 248, 0.15);
    color: #38bdf8;
    padding: 0.15rem 0.45rem;
    border-radius: 4px;
    border: 1px solid rgba(56, 189, 248, 0.3);
  }

  .mini-reset {
    background: transparent;
    border: none;
    color: #94a3b8;
    font-size: 0.7rem;
    cursor: pointer;
    text-decoration: underline;
  }

  .mini-reset:hover {
    color: #f87171;
  }

  .histogram-box {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .hist-svg {
    width: 100%;
    height: 45px;
    background: rgba(2, 6, 23, 0.6);
    border-radius: 4px;
    border: 1px solid rgba(255, 255, 255, 0.04);
  }

  .slider-dual {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
  }

  .slider-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 0.5rem;
  }

  .slider-lbl {
    font-size: 0.7rem;
    color: #94a3b8;
    font-weight: 500;
    min-width: 60px;
  }

  .slider-row input[type="range"] {
    flex: 1;
    accent-color: #38bdf8;
    cursor: pointer;
  }

  /* Group Section */
  .group-section {
    display: flex;
    flex-direction: column;
    max-height: 220px;
  }

  .group-quick-actions {
    display: flex;
    gap: 0.35rem;
  }

  .action-btn {
    background: rgba(30, 41, 59, 0.8);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    font-size: 0.68rem;
    cursor: pointer;
    font-weight: 600;
    transition: all 0.15s ease;
  }

  .action-btn:hover {
    background: rgba(51, 65, 85, 0.9);
    color: #f8fafc;
  }

  .action-btn.active {
    background: rgba(16, 185, 129, 0.2);
    border-color: rgba(16, 185, 129, 0.4);
    color: #34d399;
  }

  .group-search {
    background: rgba(2, 6, 23, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #f8fafc;
    padding: 0.3rem 0.6rem;
    border-radius: 6px;
    font-size: 0.72rem;
    outline: none;
  }

  .group-search:focus {
    border-color: #38bdf8;
  }

  .group-chips-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.35rem;
    overflow-y: auto;
    max-height: 120px;
    padding-right: 0.3rem;
  }

  .group-chip {
    display: flex;
    align-items: center;
    gap: 0.35rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #94a3b8;
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.7rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .group-chip:hover {
    background: rgba(51, 65, 85, 0.8);
    color: #ffffff;
  }

  .group-chip.selected {
    background: rgba(59, 130, 246, 0.2);
    border-color: rgba(59, 130, 246, 0.5);
    color: #60a5fa;
    font-weight: 600;
  }

  .group-chip .chip-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #64748b;
  }

  .group-chip.selected .chip-dot {
    background: #38bdf8;
    box-shadow: 0 0 6px #38bdf8;
  }

  .chip-count {
    background: rgba(0, 0, 0, 0.3);
    padding: 0.05rem 0.3rem;
    border-radius: 8px;
    font-size: 0.62rem;
    font-weight: 700;
  }

  @media (max-width: 900px) {
    .layer-panel {
      grid-template-columns: 1fr;
    }
  }
</style>
