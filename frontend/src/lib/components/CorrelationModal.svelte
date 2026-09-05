<script>
  import { onMount } from 'svelte';
  import { isCorrelationModalOpen, correlationThresholdPct } from '../stores.js';
  import { fetchCorrelationStats } from '../api.js';

  let modalData = $state(null);
  let sliderVal = $state(38);

  $effect(() => {
    sliderVal = $correlationThresholdPct;
    if ($isCorrelationModalOpen) {
      loadStats(sliderVal);
    }
  });

  async function loadStats(val) {
    try {
      const minSim = val / 100.0;
      modalData = await fetchCorrelationStats(minSim);
    } catch (err) {
      console.error('Failed to load correlation stats:', err);
    }
  }

  function handleSliderChange(e) {
    const val = parseInt(e.target.value, 10);
    sliderVal = val;
    correlationThresholdPct.set(val);
    loadStats(val);
  }

  function closeModal() {
    isCorrelationModalOpen.set(false);
  }
</script>

{#if $isCorrelationModalOpen}
  <div class="modal-backdrop" onclick={closeModal}>
    <div class="modal-box" id="correlationModal" style="display: flex;" onclick={(e) => e.stopPropagation()}>
      <div class="modal-header">
        <h3>📊 Similarity Spectrum & Correlation Histogram</h3>
        <button class="close-btn" onclick={closeModal}>✕</button>
      </div>

      <div class="modal-body">
        <div class="slider-row">
          <label for="corrSlider">Cutoff Threshold:</label>
          <input 
            type="range" 
            id="corrSlider"
            min="15" 
            max="95" 
            step="5"
            value={sliderVal} 
            oninput={handleSliderChange}
          />
          <span id="corrSliderValDisplay" class="slider-val">{sliderVal}%</span>
        </div>

        {#if modalData}
          <div class="stats-summary">
            <div>Total Link Pairs: <strong id="corrTotalPairs">{modalData.total_pairs ? modalData.total_pairs.toLocaleString() : 0}</strong></div>
            <div>Above {sliderVal}% Cutoff</div>
          </div>

          <!-- Histogram Distribution -->
          {#if modalData.buckets && modalData.buckets.length > 0}
            <div class="histogram-container">
              {#each modalData.buckets as bucket}
                <div 
                  class="bar" 
                  style="height: {Math.max(12, Math.min(120, (bucket.count / 1000) * 10))}px;"
                  title="{bucket.range}: {bucket.count} pairs"
                ></div>
              {/each}
            </div>
          {/if}

          <!-- Sample Pairs List -->
          {#if modalData.sample_pairs && modalData.sample_pairs.length > 0}
            <div class="samples-list">
              <h4>Sample Related Pairs:</h4>
              {#each modalData.sample_pairs.slice(0, 5) as pair}
                <div class="sample-row">
                  <span class="score">{pair.similarity_pct || Math.round(pair.similarity_score * 100)}%</span>
                  <span class="titles">{pair.source_title} ↔ {pair.target_title}</span>
                </div>
              {/each}
            </div>
          {/if}
        {:else}
          <div class="loading">Loading similarity spectrum data...</div>
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .modal-backdrop {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.65);
    backdrop-filter: blur(8px);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1200;
  }

  .modal-box {
    background: #0f172a;
    border: 1px solid rgba(245, 158, 11, 0.4);
    border-radius: 14px;
    width: 560px;
    max-width: 90vw;
    display: flex;
    flex-direction: column;
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8);
    overflow: hidden;
  }

  .modal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem 1.5rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    background: rgba(30, 41, 59, 0.5);
  }

  .modal-header h3 {
    margin: 0;
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

  .modal-body {
    padding: 1.5rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .slider-row {
    display: flex;
    align-items: center;
    gap: 1rem;
    background: rgba(30, 41, 59, 0.6);
    padding: 0.75rem 1rem;
    border-radius: 8px;
    color: #f8fafc;
    font-size: 0.85rem;
  }

  .slider-row input[type="range"] {
    flex: 1;
    accent-color: #f59e0b;
    cursor: pointer;
  }

  .slider-val {
    font-weight: 700;
    color: #fbbf24;
    min-width: 40px;
  }

  .stats-summary {
    display: flex;
    justify-content: space-between;
    font-size: 0.85rem;
    color: #cbd5e1;
    background: rgba(245, 158, 11, 0.1);
    border: 1px solid rgba(245, 158, 11, 0.2);
    padding: 0.6rem 1rem;
    border-radius: 6px;
  }

  .histogram-container {
    display: flex;
    align-items: flex-end;
    gap: 4px;
    height: 130px;
    background: rgba(30, 41, 59, 0.4);
    padding: 0.75rem;
    border-radius: 8px;
    border: 1px solid rgba(255, 255, 255, 0.05);
  }

  .bar {
    flex: 1;
    background: #f59e0b;
    border-radius: 3px 3px 0 0;
    transition: height 0.2s ease;
  }

  .samples-list {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  .samples-list h4 {
    margin: 0 0 0.25rem 0;
    font-size: 0.85rem;
    color: #94a3b8;
  }

  .sample-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: rgba(30, 41, 59, 0.5);
    padding: 0.5rem 0.75rem;
    border-radius: 6px;
    font-size: 0.78rem;
  }

  .score {
    background: rgba(245, 158, 11, 0.2);
    color: #fbbf24;
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
    font-weight: 700;
  }

  .titles {
    color: #cbd5e1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .loading {
    text-align: center;
    color: #64748b;
    padding: 2rem 0;
  }
</style>
