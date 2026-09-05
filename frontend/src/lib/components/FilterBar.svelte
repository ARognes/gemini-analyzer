<script>
  import { 
    hideOneOffChats, 
    hideAppCommands, 
    selectedActionabilityTier, 
    minTurnsFilter, 
    maxTurnsFilter, 
    correlationThresholdPct,
    isCorrelationModalOpen 
  } from '../stores.js';

  function toggleOneOffs() {
    hideOneOffChats.update(v => !v);
  }

  function toggleAppCommands() {
    hideAppCommands.update(v => !v);
  }

  function selectTier(tier) {
    selectedActionabilityTier.set(tier);
  }

  function openCorrModal() {
    isCorrelationModalOpen.set(true);
  }
</script>

<div class="filter-bar">
  <!-- Actionability Tier Filter Pills -->
  <div class="filter-group">
    <span class="group-label">Actionability:</span>
    <button 
      class="pill-btn" 
      class:active={$selectedActionabilityTier === ''}
      onclick={() => selectTier('')}
    >
      All Tiers
    </button>
    <button 
      class="pill-btn tier-project" 
      class:active={$selectedActionabilityTier === 'large_project'}
      onclick={() => selectTier('large_project')}
    >
      🚀 Large Projects
    </button>
    <button 
      class="pill-btn tier-standard" 
      class:active={$selectedActionabilityTier === 'standard'}
      onclick={() => selectTier('standard')}
    >
      💬 Standard Threads
    </button>
  </div>

  <!-- Noise Pre-Filtering Toggle Switches -->
  <div class="filter-group">
    <span class="group-label">Pre-Filters:</span>
    <button 
      id="btnToggleOneOffs"
      class="toggle-pill" 
      class:active={!$hideOneOffChats}
      onclick={toggleOneOffs}
    >
      ⚡ One-Off Chats: <span class="state">{#if $hideOneOffChats}HIDDEN{:else}SHOWING{/if}</span>
    </button>

    <button 
      id="btnToggleAppCmds"
      class="toggle-pill" 
      class:active={!$hideAppCommands}
      onclick={toggleAppCommands}
    >
      📱 App Commands: <span class="state">{#if $hideAppCommands}HIDDEN{:else}SHOWING{/if}</span>
    </button>
  </div>

  <!-- Turn Count Range Slider -->
  <div class="filter-group slider-group">
    <span class="group-label">Turns ({$minTurnsFilter} - {$maxTurnsFilter}):</span>
    <input 
      type="range" 
      id="minTurnsSlider"
      min="1" 
      max="50" 
      bind:value={$minTurnsFilter}
    />
    <input 
      type="range" 
      id="maxTurnsSlider"
      min="1" 
      max="50" 
      bind:value={$maxTurnsFilter}
    />
  </div>

  <!-- Correlation Cutoff Spectrum Trigger -->
  <div class="filter-group">
    <button class="corr-btn" onclick={openCorrModal}>
      📊 Similarity Cutoff: <span class="val">{$correlationThresholdPct}%</span>
    </button>
  </div>
</div>

<style>
  .filter-bar {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.5rem 1.25rem;
    background: rgba(15, 23, 42, 0.7);
    backdrop-filter: blur(12px);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    flex-wrap: wrap;
    gap: 0.75rem;
    z-index: 90;
  }

  .filter-group {
    display: flex;
    align-items: center;
    gap: 0.4rem;
  }

  .group-label {
    font-size: 0.75rem;
    color: #94a3b8;
    font-weight: 500;
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
    background: rgba(16, 185, 129, 0.2);
    border-color: rgba(16, 185, 129, 0.4);
    color: #34d399;
  }

  .toggle-pill .state {
    font-weight: 700;
  }

  .slider-group input[type="range"] {
    width: 70px;
    accent-color: #3b82f6;
    cursor: pointer;
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
    box-shadow: 0 0 10px rgba(245, 158, 11, 0.3);
  }

  .corr-btn .val {
    color: #ffffff;
    font-weight: 700;
  }
</style>
