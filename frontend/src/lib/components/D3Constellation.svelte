<script>
  import { onMount, onDestroy } from 'svelte';
  import * as d3 from 'd3';
  import { 
    hideOneOffChats, 
    hideAppCommands, 
    selectedActionabilityTier, 
    minTurnsFilter, 
    maxTurnsFilter,
    hoveredNode,
    selectedNode,
    searchMatchingNodeIds,
    searchPathEdges,
    isThreadDrawerOpen,
    activeThreadDrawerData
  } from '../stores.js';
  import { fetchCanvasData, fetchStitchedThread } from '../api.js';

  let canvasEl;
  let ctx;
  let simulation;

  let graphData = $state({ nodes: [], relations: [] });
  let isLoaded = $state(false);

  // Pan & Zoom transform
  let transform = d3.zoomIdentity;

  $effect(() => {
    if (isLoaded && ctx) {
      drawCanvas();
    }
  });

  onMount(async () => {
    ctx = canvasEl.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    // Setup D3 Zoom
    const zoom = d3.zoom()
      .scaleExtent([0.15, 5.0])
      .on('zoom', (event) => {
        transform = event.transform;
        drawCanvas();
      });

    d3.select(canvasEl).call(zoom);

    try {
      const data = await fetchCanvasData('chat', 0.38);
      graphData = data;
      initD3Simulation();
      isLoaded = true;
    } catch (err) {
      console.error('Failed to load D3 graph data:', err);
    }
  });

  onDestroy(() => {
    if (simulation) simulation.stop();
    window.removeEventListener('resize', resizeCanvas);
  });

  function resizeCanvas() {
    if (!canvasEl) return;
    canvasEl.width = canvasEl.clientWidth || window.innerWidth;
    canvasEl.height = canvasEl.clientHeight || window.innerHeight;
    if (isLoaded) drawCanvas();
  }

  function initD3Simulation() {
    const nodes = (graphData.nodes || []).map(n => ({
      ...n,
      x: n.x || (Math.random() * 1600 + 400),
      y: n.y || (Math.random() * 1200 + 300),
      radius: Math.max(7, Math.min(18, 5 + (n.turn_count || 1) * 0.8))
    }));

    const nodeMap = new Map(nodes.map(n => [n.id, n]));

    const links = (graphData.relations || [])
      .filter(rel => nodeMap.has(rel.source_key) && nodeMap.has(rel.target_key))
      .map(rel => ({
        id: rel.id,
        source: nodeMap.get(rel.source_key),
        target: nodeMap.get(rel.target_key),
        similarity: rel.similarity_score
      }));

    simulation = d3.forceSimulation(nodes)
      .force('charge', d3.forceManyBody().strength(-80).distanceMax(220))
      .force('link', d3.forceLink(links).id(d => d.id).distance(d => Math.max(60, 140 * (1.0 - d.similarity))))
      .force('center', d3.forceCenter(1600, 1100).strength(0.05))
      .force('collide', d3.forceCollide().radius(d => d.radius + 12).strength(0.6))
      .alphaDecay(0.02)
      .on('tick', () => {
        graphData.nodes = nodes;
        graphData.links = links;
        drawCanvas();
      });
  }

  function computeMultiHopTraversal(startNodeId, maxHops = 4) {
    if (!startNodeId) return { nodeDistances: new Map(), edgeDistances: new Map() };

    const nodeDistances = new Map();
    const edgeDistances = new Map();
    const queue = [{ id: startNodeId, depth: 0 }];
    nodeDistances.set(startNodeId, 0);

    const relations = graphData.relations || [];
    const adj = new Map();

    relations.forEach(rel => {
      if (!adj.has(rel.source_key)) adj.set(rel.source_key, []);
      if (!adj.has(rel.target_key)) adj.set(rel.target_key, []);
      adj.get(rel.source_key).push({ target: rel.target_key, relId: rel.id });
      adj.get(rel.target_key).push({ target: rel.source_key, relId: rel.id });
    });

    while (queue.length > 0) {
      const item = queue.shift();
      if (!item || item.depth >= maxHops) continue;

      const neighbors = adj.get(item.id) || [];
      neighbors.forEach(({ target, relId }) => {
        if (!nodeDistances.has(target)) {
          nodeDistances.set(target, item.depth + 1);
          edgeDistances.set(relId, item.depth + 1);
          queue.push({ id: target, depth: item.depth + 1 });
        } else if (nodeDistances.get(target) === item.depth + 1) {
          edgeDistances.set(relId, item.depth + 1);
        }
      });
    }

    return { nodeDistances, edgeDistances };
  }

  function drawCanvas() {
    if (!ctx || !canvasEl) return;
    const w = canvasEl.width;
    const h = canvasEl.height;

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(transform.x, transform.y);
    ctx.scale(transform.k, transform.k);

    const nodes = graphData.nodes || [];
    const links = graphData.links || [];

    const visibleNodes = new Set();
    nodes.forEach(n => {
      if ($hideOneOffChats && (n.actionability_tier === 'one_off' || n.turn_count <= 1)) return;
      if ($hideAppCommands && n.actionability_tier === 'app_command') return;
      if ($selectedActionabilityTier && n.actionability_tier !== $selectedActionabilityTier) return;
      if (n.turn_count < $minTurnsFilter || n.turn_count > $maxTurnsFilter) return;
      visibleNodes.add(n.id);
    });

    const isSubgraphActive = $searchMatchingNodeIds.size > 0;
    const isSelectionActive = !!$selectedNode;
    const { nodeDistances, edgeDistances } = isSelectionActive 
      ? computeMultiHopTraversal($selectedNode.id, 4) 
      : { nodeDistances: new Map(), edgeDistances: new Map() };

    // Draw D3 Links
    links.forEach(rel => {
      const srcId = rel.source.id || rel.source;
      const tgtId = rel.target.id || rel.target;
      if (!visibleNodes.has(srcId) || !visibleNodes.has(tgtId)) return;

      const edgeDist = edgeDistances.get(rel.id);
      const isPathEdge = $searchPathEdges.has(rel.id);

      ctx.beginPath();
      ctx.moveTo(rel.source.x, rel.source.y);
      ctx.lineTo(rel.target.x, rel.target.y);

      if (isPathEdge) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 3.5;
      } else if (isSelectionActive && edgeDist !== undefined) {
        const opacityMap = { 1: 0.85, 2: 0.55, 3: 0.35, 4: 0.20 };
        const opacity = opacityMap[edgeDist] || 0.15;
        ctx.strokeStyle = `rgba(96, 165, 250, ${opacity})`;
        ctx.lineWidth = Math.max(1.2, 3.0 - (edgeDist * 0.5));
      } else {
        ctx.strokeStyle = (isSubgraphActive || isSelectionActive) 
          ? 'rgba(255, 255, 255, 0.04)' 
          : 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1.0;
      }
      ctx.stroke();
    });

    // Draw D3 Nodes
    nodes.forEach(n => {
      if (!visibleNodes.has(n.id)) return;

      const isMatch = $searchMatchingNodeIds.has(n.id);
      const isHovered = $hoveredNode && $hoveredNode.id === n.id;
      const isSel = $selectedNode && $selectedNode.id === n.id;
      const dist = nodeDistances.get(n.id);

      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius || 8, 0, Math.PI * 2);

      let color = '#3b82f6';
      if (n.actionability_tier === 'large_project') color = '#8b5cf6';
      if (n.actionability_tier === 'app_command') color = '#ec4899';

      if (isMatch) color = '#f59e0b';
      if (isSel) color = '#38bdf8';

      if (isSelectionActive && dist !== undefined) {
        const opacityMap = { 0: 1.0, 1: 0.85, 2: 0.60, 3: 0.40, 4: 0.25 };
        const op = opacityMap[dist] || 0.2;
        color = dist === 0 ? '#38bdf8' : `rgba(96, 165, 250, ${op})`;
        ctx.fillStyle = color;
      } else if (isSelectionActive) {
        ctx.fillStyle = 'rgba(100, 116, 139, 0.12)';
      } else if (isSubgraphActive && !isMatch) {
        ctx.fillStyle = 'rgba(100, 116, 139, 0.25)';
      } else {
        ctx.fillStyle = color;
      }

      ctx.fill();

      if (isMatch) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 3.0;
        ctx.stroke();
      } else if (isSel) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 3.0;
        ctx.stroke();
      } else if (isSelectionActive && dist !== undefined) {
        ctx.strokeStyle = `rgba(255, 255, 255, ${dist === 1 ? 0.7 : 0.3})`;
        ctx.lineWidth = 1.5;
        ctx.stroke();
      } else if (isHovered) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.0;
        ctx.stroke();
      }
    });

    ctx.restore();
  }

  function handleMouseDown(e) {
    const rect = canvasEl.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const wx = (mx - transform.x) / transform.k;
    const wy = (my - transform.y) / transform.k;

    const nodes = graphData.nodes || [];
    const hit = nodes.find(n => {
      const dx = n.x - wx;
      const dy = n.y - wy;
      return (dx * dx + dy * dy) <= ((n.radius || 8) + 6) ** 2;
    });

    if (hit) {
      selectedNode.set(hit);
    }
  }

  function handleDblClick(e) {
    const rect = canvasEl.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const wx = (mx - transform.x) / transform.k;
    const wy = (my - transform.y) / transform.k;

    const nodes = graphData.nodes || [];
    const hit = nodes.find(n => {
      const dx = n.x - wx;
      const dy = n.y - wy;
      return (dx * dx + dy * dy) <= ((n.radius || 8) + 6) ** 2;
    });

    if (hit) {
      openThreadDrawer(hit.id);
    }
  }

  async function openThreadDrawer(threadId) {
    try {
      const thread = await fetchStitchedThread(threadId);
      if (thread) {
        activeThreadDrawerData.set(thread);
        isThreadDrawerOpen.set(true);
      }
    } catch (err) {
      console.error('Failed to open thread drawer:', err);
    }
  }
</script>

<div class="d3-wrapper">
  <canvas 
    bind:this={canvasEl}
    onmousedown={handleMouseDown}
    ondblclick={handleDblClick}
  ></canvas>

  <div class="d3-badge">🪐 D3.js Force Simulation Engine</div>
</div>

<style>
  .d3-wrapper {
    position: relative;
    width: 100%;
    height: 100%;
    overflow: hidden;
    background: #090d16;
  }

  canvas {
    width: 100%;
    height: 100%;
    display: block;
    cursor: grab;
  }

  canvas:active {
    cursor: grabbing;
  }

  .d3-badge {
    position: absolute;
    bottom: 1rem;
    left: 1rem;
    background: rgba(15, 23, 42, 0.85);
    border: 1px solid rgba(245, 158, 11, 0.4);
    color: #fbbf24;
    padding: 0.4rem 0.8rem;
    border-radius: 8px;
    font-size: 0.75rem;
    font-weight: 600;
    backdrop-filter: blur(12px);
    pointer-events: none;
  }
</style>
