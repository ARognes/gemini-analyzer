<script>
  import { onMount } from 'svelte';
  import { activeSubtab, stats } from '$lib/stores.js';
  import { fetchStats } from '$lib/api.js';

  import Header from '$lib/components/Header.svelte';
  import FilterBar from '$lib/components/FilterBar.svelte';
  import CanvasConstellation from '$lib/components/CanvasConstellation.svelte';
  import D3Constellation from '$lib/components/D3Constellation.svelte';
  import SubgraphDrawer from '$lib/components/SubgraphDrawer.svelte';
  import ThreadDrawer from '$lib/components/ThreadDrawer.svelte';
  import CorrelationModal from '$lib/components/CorrelationModal.svelte';
  import MindmapTree from '$lib/components/MindmapTree.svelte';
  import DomainMatrix from '$lib/components/DomainMatrix.svelte';

  onMount(async () => {
    try {
      const data = await fetchStats();
      stats.set(data);
    } catch (err) {
      console.error('Failed to load system stats:', err);
    }
  });
</script>

<div class="app-layout">
  <Header />

  {#if $activeSubtab === 'topic_clusters' || $activeSubtab === 'd3_constellation'}
    <FilterBar />
  {/if}

  <main class="main-viewport">
    {#if $activeSubtab === 'topic_clusters'}
      <CanvasConstellation />
    {:else if $activeSubtab === 'd3_constellation'}
      <D3Constellation />
    {:else if $activeSubtab === 'mindmap'}
      <MindmapTree />
    {:else if $activeSubtab === 'matrix'}
      <DomainMatrix />
    {/if}
  </main>

  <SubgraphDrawer />
  <ThreadDrawer />
  <CorrelationModal />
</div>

<style>
  :global(body, html) {
    margin: 0;
    padding: 0;
    width: 100%;
    height: 100%;
    background: #090d16;
    font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
    color: #f8fafc;
    overflow: hidden;
  }

  .app-layout {
    display: flex;
    flex-direction: column;
    width: 100vw;
    height: 100vh;
    overflow: hidden;
  }

  .main-viewport {
    flex: 1;
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
  }
</style>
