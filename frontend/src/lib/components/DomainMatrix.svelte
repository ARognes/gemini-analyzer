<script>
  import { onMount } from 'svelte';
  import { fetchDomainMatrix } from '../api.js';

  let matrixData = $state(null);
  let linkMap = $state({});

  onMount(async () => {
    try {
      matrixData = await fetchDomainMatrix(0.38);
      if (matrixData && matrixData.matrix) {
        const map = {};
        matrixData.matrix.forEach(item => {
          map[`${item.source_cat}:${item.target_cat}`] = item.link_count;
        });
        linkMap = map;
      }
    } catch (err) {
      console.error('Failed to load domain matrix:', err);
    }
  });
</script>

<div class="matrix-container">
  {#if matrixData && matrixData.categories}
    <div class="matrix-table-wrapper">
      <h3>📊 Cross-Domain Interconnection Similarity Matrix</h3>
      <table class="matrix-table">
        <thead>
          <tr>
            <th>Domain</th>
            {#each matrixData.categories as dom}
              <th>{dom}</th>
            {/each}
          </tr>
        </thead>
        <tbody>
          {#each matrixData.categories as domA}
            <tr>
              <th class="row-header">{domA}</th>
              {#each matrixData.categories as domB}
                {@const count = linkMap[`${domA}:${domB}`] || 0}
                <td 
                  class="cell"
                  style="background: rgba(59, 130, 246, {Math.min(0.85, count / 1500)});"
                  title="{domA} ↔ {domB}: {count} connecting links"
                >
                  {count}
                </td>
              {/each}
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  {:else}
    <div class="loading">Loading domain similarity matrix...</div>
  {/if}
</div>

<style>
  .matrix-container {
    width: 100%;
    height: 100%;
    overflow-y: auto;
    padding: 2rem;
    background: #090d16;
    color: #f8fafc;
    display: flex;
    justify-content: center;
  }

  .matrix-table-wrapper {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    max-width: 950px;
  }

  h3 {
    margin: 0;
    color: #38bdf8;
    font-size: 1.1rem;
  }

  .matrix-table {
    border-collapse: collapse;
    width: 100%;
    background: rgba(30, 41, 59, 0.4);
    border-radius: 10px;
    overflow: hidden;
    border: 1px solid rgba(255, 255, 255, 0.08);
  }

  th, td {
    padding: 0.75rem 1rem;
    text-align: center;
    font-size: 0.8rem;
    border: 1px solid rgba(255, 255, 255, 0.06);
  }

  th {
    background: rgba(15, 23, 42, 0.8);
    color: #94a3b8;
    font-weight: 600;
  }

  .row-header {
    text-align: left;
    background: rgba(15, 23, 42, 0.8);
    color: #f8fafc;
  }

  .cell {
    color: #ffffff;
    font-weight: 600;
    transition: all 0.2s ease;
  }

  .cell:hover {
    transform: scale(1.05);
    box-shadow: 0 0 12px rgba(255, 255, 255, 0.3);
    z-index: 10;
  }

  .loading {
    text-align: center;
    color: #64748b;
    margin-top: 5rem;
  }
</style>
