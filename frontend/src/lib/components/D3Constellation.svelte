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
  let zoomInstance;

  let graphData = $state({ nodes: [], relations: [] });
  let isLoaded = $state(false);

  // Pan & Zoom transform
  let transform = $state(d3.zoomIdentity);
  let isDraggingNode = false;
  let lastClickTime = 0;

  // Graph Context Menu state
  let isContextMenuOpen = $state(false);
  let contextMenuX = $state(0);
  let contextMenuY = $state(0);
  let contextMenuNode = $state(null);

  $effect(() => {
    if (isLoaded && ctx) {
      drawCanvas();
    }
  });

  onMount(async () => {
    ctx = canvasEl.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);
    window.addEventListener('click', closeContextMenu);

    // Setup D3 Zoom - Filter strictly for Middle Mouse Button (button === 1) or Scroll Wheel
    zoomInstance = d3.zoom()
      .scaleExtent([0.15, 5.0])
      .filter((event) => {
        if (event.type === 'wheel') return true;
        if (event.type === 'mousedown') return event.button === 1; // Middle Mouse Button Panning
        return true;
      })
      .on('zoom', (event) => {
        transform = event.transform;
        drawCanvas();
      });

    const d3Canvas = d3.select(canvasEl);
    d3Canvas.call(zoomInstance);

    // Initial zoom centering (scale 0.45, centered on 1600, 1100)
    resetCameraView();

    // Setup D3 Drag - Left Mouse Button (button === 0) for Node Dragging
    let dragOffsetX = 0;
    let dragOffsetY = 0;

    const drag = d3.drag()
      .container(canvasEl)
      .filter((event) => event.button === 0)
      .subject(event => {
        const sourceEvt = event.sourceEvent || event;
        const [mx, my] = d3.pointer(sourceEvt, canvasEl);
        const wx = (mx - transform.x) / transform.k;
        const wy = (my - transform.y) / transform.k;
        const nodes = graphData.nodes || [];
        return nodes.find(n => {
          const dx = n.x - wx;
          const dy = n.y - wy;
          return (dx * dx + dy * dy) <= ((n.radius || 8) + 6) ** 2;
        });
      })
      .on('start', (event) => {
        if (!event.subject) return;
        isDraggingNode = true;
        if (!event.active && simulation) simulation.alphaTarget(0.3).restart();
        
        const sourceEvt = event.sourceEvent || event;
        const [mx, my] = d3.pointer(sourceEvt, canvasEl);
        const wx = (mx - transform.x) / transform.k;
        const wy = (my - transform.y) / transform.k;
        dragOffsetX = event.subject.x - wx;
        dragOffsetY = event.subject.y - wy;

        event.subject.fx = event.subject.x;
        event.subject.fy = event.subject.y;
      })
      .on('drag', (event) => {
        if (!event.subject) return;
        const sourceEvt = event.sourceEvent || event;
        const [mx, my] = d3.pointer(sourceEvt, canvasEl);
        const wx = (mx - transform.x) / transform.k;
        const wy = (my - transform.y) / transform.k;
        event.subject.fx = wx + dragOffsetX;
        event.subject.fy = wy + dragOffsetY;
        drawCanvas();
      })
      .on('end', (event) => {
        if (!event.subject) return;
        isDraggingNode = false;
        if (!event.active && simulation) simulation.alphaTarget(0);
        if (!event.subject.isPinned) {
          event.subject.fx = null;
          event.subject.fy = null;
        }
      });

    d3Canvas.call(drag);

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
    window.removeEventListener('click', closeContextMenu);
  });

  function resizeCanvas() {
    if (!canvasEl) return;
    canvasEl.width = canvasEl.clientWidth || window.innerWidth;
    canvasEl.height = canvasEl.clientHeight || window.innerHeight;
    if (isLoaded) drawCanvas();
  }

  function resetCameraView() {
    if (!canvasEl || !zoomInstance) return;
    const initialTransform = d3.zoomIdentity
      .translate((canvasEl.width / 2) - (1600 * 0.45), (canvasEl.height / 2) - (1100 * 0.45))
      .scale(0.45);
    d3.select(canvasEl).call(zoomInstance.transform, initialTransform);
  }

  function forceClusterCentroid(strength = 0.14) {
    let nodes;
    function force(alpha) {
      const centroids = {};
      const counts = {};

      nodes.forEach(n => {
        const tag = n.data_tag || n.category;
        if (!tag || tag === 'outliers') return;
        if (!centroids[tag]) {
          centroids[tag] = { x: 0, y: 0 };
          counts[tag] = 0;
        }
        centroids[tag].x += n.x;
        centroids[tag].y += n.y;
        counts[tag]++;
      });

      Object.keys(centroids).forEach(tag => {
        if (counts[tag] > 0) {
          centroids[tag].x /= counts[tag];
          centroids[tag].y /= counts[tag];
        }
      });

      const k = alpha * strength;
      nodes.forEach(n => {
        const tag = n.data_tag || n.category;
        if (!tag || tag === 'outliers' || !centroids[tag]) return;
        const target = centroids[tag];
        n.vx += (target.x - n.x) * k;
        n.vy += (target.y - n.y) * k;
      });
    }

    force.initialize = _nodes => { nodes = _nodes; };
    return force;
  }

  function initD3Simulation() {
    const rawNodes = graphData.nodes || [];

    // Group initial nodes in circular sectors around canvas center
    const clusters = {};
    rawNodes.forEach(n => {
      const tag = n.data_tag || n.category || 'outliers';
      if (!clusters[tag]) clusters[tag] = [];
      clusters[tag].push(n);
    });

    const tags = Object.keys(clusters);
    const centerCanvasX = 1600;
    const centerCanvasY = 1100;
    const numTags = tags.length;
    const mainRadius = 550;

    tags.forEach((tag, idx) => {
      const angle = (idx / numTags) * 2 * Math.PI;
      const sectorCenterX = centerCanvasX + Math.cos(angle) * mainRadius;
      const sectorCenterY = centerCanvasY + Math.sin(angle) * mainRadius;

      const clusterNodes = clusters[tag];
      const goldenAngle = 2.399963229728653;
      clusterNodes.forEach((n, nIdx) => {
        const r = 35 * Math.sqrt(nIdx + 1);
        const theta = nIdx * goldenAngle;
        n.x = sectorCenterX + r * Math.cos(theta);
        n.y = sectorCenterY + r * Math.sin(theta);
        n.radius = Math.max(7, Math.min(18, 5 + (n.turn_count || 1) * 0.8));
      });
    });

    const nodeMap = new Map(rawNodes.map(n => [n.id, n]));

    const links = (graphData.relations || [])
      .filter(rel => nodeMap.has(rel.source_key) && nodeMap.has(rel.target_key))
      .map(rel => ({
        id: rel.id,
        source: nodeMap.get(rel.source_key),
        target: nodeMap.get(rel.target_key),
        similarity: rel.similarity_score
      }));

    simulation = d3.forceSimulation(rawNodes)
      .force('charge', d3.forceManyBody().strength(-90).distanceMax(240))
      .force('link', d3.forceLink(links).id(d => d.id).distance(d => Math.max(70, 160 * (1.0 - d.similarity))).strength(0.4))
      .force('center', d3.forceCenter(1600, 1100).strength(0.04))
      .force('collide', d3.forceCollide().radius(d => d.radius + 14).strength(0.7))
      .force('cluster', forceClusterCentroid(0.14))
      .alphaDecay(0.02)
      .on('tick', () => {
        graphData.nodes = rawNodes;
        graphData.links = links;
        drawCanvas();
      });
  }

  function computeMultiHopTraversal(startNodeId, maxHops = 25) {
    if (!startNodeId) return { nodeDistances: new Map(), edgeDistances: new Map() };

    const nodeDistances = new Map();
    const edgeDistances = new Map();
    const queue = [{ id: startNodeId, depth: 0 }];
    nodeDistances.set(startNodeId, 0);

    const links = graphData.links || [];
    const relations = graphData.relations || [];
    const adj = new Map();

    const addEdge = (u, v, id) => {
      if (!adj.has(u)) adj.set(u, []);
      adj.get(u).push({ target: v, relId: id });
    };

    links.forEach(rel => {
      const u = rel.source.id || rel.source_key || rel.source;
      const v = rel.target.id || rel.target_key || rel.target;
      if (u && v) {
        addEdge(u, v, rel.id);
        addEdge(v, u, rel.id);
      }
    });

    relations.forEach(rel => {
      if (rel.source_key && rel.target_key) {
        addEdge(rel.source_key, rel.target_key, rel.id);
        addEdge(rel.target_key, rel.source_key, rel.id);
      }
    });

    while (queue.length > 0) {
      const item = queue.shift();
      if (!item || item.depth >= maxHops) continue;

      const neighbors = adj.get(item.id) || [];
      neighbors.forEach(({ target }) => {
        if (!nodeDistances.has(target)) {
          nodeDistances.set(target, item.depth + 1);
          queue.push({ id: target, depth: item.depth + 1 });
        }
      });
    }

    links.forEach(rel => {
      const u = rel.source.id || rel.source_key || rel.source;
      const v = rel.target.id || rel.target_key || rel.target;
      if (nodeDistances.has(u) && nodeDistances.has(v)) {
        const du = nodeDistances.get(u);
        const dv = nodeDistances.get(v);
        edgeDistances.set(rel.id, Math.max(du, dv));
      }
    });

    return { nodeDistances, edgeDistances };
  }

  function drawClusterBoundingHulls(visibleNodes) {
    const nodes = graphData.nodes || [];
    const clusterMap = {};

    nodes.forEach(n => {
      if (!visibleNodes.has(n.id) || typeof n.x !== 'number' || typeof n.y !== 'number') return;
      const tag = n.data_tag || n.category || 'outliers';
      if (!clusterMap[tag]) clusterMap[tag] = [];
      clusterMap[tag].push(n);
    });

    Object.keys(clusterMap).forEach(tag => {
      const cNodes = clusterMap[tag];
      if (cNodes.length < 3) return;

      const allPoints = [];
      const padding = 22;
      const angleSteps = 8;

      cNodes.forEach(n => {
        const r = (n.radius || 8) + padding;
        for (let i = 0; i < angleSteps; i++) {
          const angle = (i * 2 * Math.PI) / angleSteps;
          allPoints.push([
            n.x + r * Math.cos(angle),
            n.y + r * Math.sin(angle)
          ]);
        }
      });

      const hull = d3.polygonHull(allPoints);
      if (!hull || hull.length < 3) return;

      ctx.beginPath();
      ctx.moveTo(hull[0][0], hull[0][1]);
      for (let i = 1; i < hull.length; i++) {
        ctx.lineTo(hull[i][0], hull[i][1]);
      }
      ctx.closePath();

      ctx.fillStyle = 'rgba(59, 130, 246, 0.05)';
      ctx.fill();
      ctx.strokeStyle = 'rgba(59, 130, 246, 0.18)';
      ctx.lineWidth = 1.5;
      ctx.lineJoin = 'round';
      ctx.lineCap = 'round';
      ctx.setLineDash([6, 4]);
      ctx.stroke();
      ctx.setLineDash([]);
    });
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
      ? computeMultiHopTraversal($selectedNode.id, 25) 
      : { nodeDistances: new Map(), edgeDistances: new Map() };

    // Draw Translucent Cluster Hulls
    drawClusterBoundingHulls(visibleNodes);

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
        ctx.shadowColor = '#f59e0b';
        ctx.shadowBlur = 18;
      } else if (isSelectionActive && edgeDist !== undefined) {
        const edgeWidth = Math.max(0.7, 5.2 * Math.pow(0.68, edgeDist - 1));
        const edgeOpacity = Math.max(0.12, 0.92 * Math.pow(0.70, edgeDist - 1));
        const edgeBlur = edgeDist === 1 ? 14 : (edgeDist === 2 ? 6 : 0);

        ctx.strokeStyle = `rgba(96, 165, 250, ${edgeOpacity})`;
        ctx.lineWidth = edgeWidth;
        ctx.shadowBlur = edgeBlur;
        ctx.shadowColor = '#60a5fa';
      } else {
        ctx.strokeStyle = (isSubgraphActive || isSelectionActive) 
          ? 'rgba(255, 255, 255, 0.03)' 
          : 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 0.5;
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    });

    // Draw D3 Nodes
    nodes.forEach(n => {
      if (!visibleNodes.has(n.id)) return;

      const isMatch = $searchMatchingNodeIds.has(n.id);
      const isHovered = $hoveredNode && $hoveredNode.id === n.id;
      const isSel = $selectedNode && $selectedNode.id === n.id;
      const dist = nodeDistances.get(n.id);

      let baseRadius = n.radius || 8;
      let drawRadius = baseRadius;
      let color = '#3b82f6';
      if (n.actionability_tier === 'large_project') color = '#8b5cf6';
      if (n.actionability_tier === 'app_command') color = '#ec4899';
      if (isMatch) color = '#f59e0b';

      if (isSel) {
        color = '#38bdf8';
        drawRadius = baseRadius + 6;
        ctx.shadowColor = '#38bdf8';
        ctx.shadowBlur = 22;
        ctx.fillStyle = color;
      } else if (isSelectionActive && dist !== undefined) {
        const nodeOpacity = Math.max(0.14, 0.92 * Math.pow(0.72, dist - 1));
        const nodeRadiusScale = Math.max(0.65, Math.pow(0.92, dist - 1));
        drawRadius = baseRadius * nodeRadiusScale;
        
        ctx.fillStyle = `rgba(96, 165, 250, ${nodeOpacity})`;
        if (dist === 1) {
          ctx.shadowColor = '#60a5fa';
          ctx.shadowBlur = 10;
        } else if (dist === 2) {
          ctx.shadowColor = '#60a5fa';
          ctx.shadowBlur = 4;
        } else {
          ctx.shadowBlur = 0;
        }
      } else if (isSelectionActive) {
        ctx.fillStyle = 'rgba(100, 116, 139, 0.06)';
        ctx.shadowBlur = 0;
      } else if (isSubgraphActive && !isMatch) {
        ctx.fillStyle = 'rgba(100, 116, 139, 0.12)';
        ctx.shadowBlur = 0;
      } else {
        ctx.fillStyle = color;
        if (isHovered) {
          ctx.shadowColor = color;
          ctx.shadowBlur = 12;
        } else {
          ctx.shadowBlur = 0;
        }
      }

      ctx.beginPath();
      ctx.arc(n.x, n.y, drawRadius, 0, Math.PI * 2);
      ctx.fill();

      if (isSel) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.5;
        ctx.stroke();
      } else if (isHovered) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.0;
        ctx.stroke();
      }
    });

    ctx.restore();
  }

  function handleMouseMove(e) {
    if (isDraggingNode) return;

    const rect = canvasEl.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const wx = (mx - transform.x) / transform.k;
    const wy = (my - transform.y) / transform.k;

    const nodes = graphData.nodes || [];
    const hit = nodes.find(n => {
      if (typeof n.x !== 'number') return false;
      const dx = n.x - wx;
      const dy = n.y - wy;
      return (dx * dx + dy * dy) <= ((n.radius || 8) + 6) ** 2;
    });

    hoveredNode.set(hit || null);
  }

  function handleClick(e) {
    // Only handle Left Click (button === 0) for selection
    if (e.button !== 0) return;

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

    const now = Date.now();
    if (hit) {
      if (now - lastClickTime < 300) {
        // Double click -> open thread inspector drawer
        openThreadDrawer(hit.id);
      } else {
        // Single click -> select node for multi-hop graph traversal
        selectedNode.set(hit);
      }
    } else {
      selectedNode.set(null);
    }
    lastClickTime = now;
  }

  function handleContextMenu(e) {
    // Intercept right-click ONLY on the graph canvas
    e.preventDefault();
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

    contextMenuX = e.clientX;
    contextMenuY = e.clientY;
    contextMenuNode = hit || null;
    isContextMenuOpen = true;
  }

  function closeContextMenu() {
    isContextMenuOpen = false;
    contextMenuNode = null;
  }

  function togglePinNode(node) {
    if (!node) return;
    if (node.isPinned) {
      node.isPinned = false;
      node.fx = null;
      node.fy = null;
    } else {
      node.isPinned = true;
      node.fx = node.x;
      node.fy = node.y;
    }
    drawCanvas();
    closeContextMenu();
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
    closeContextMenu();
  }

  function copyThreadId(threadId) {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(threadId);
    }
    closeContextMenu();
  }
</script>

<div class="d3-wrapper">
  <canvas 
    id="constellationCanvas"
    bind:this={canvasEl}
    onmousemove={handleMouseMove}
    onclick={handleClick}
    oncontextmenu={handleContextMenu}
  ></canvas>

  {#if $hoveredNode}
    <div 
      class="tooltip"
      style="left: {transform.x + ($hoveredNode.x * transform.k) + 15}px; top: {transform.y + ($hoveredNode.y * transform.k) - 20}px;"
    >
      <div class="tooltip-title">{$hoveredNode.title || $hoveredNode.title_snippet}</div>
      <div class="tooltip-meta">Turns: {$hoveredNode.turn_count || 1} • Tier: {$hoveredNode.actionability_tier || 'standard'}</div>
    </div>
  {/if}

  {#if isContextMenuOpen}
    <div 
      class="context-menu"
      style="left: {contextMenuX}px; top: {contextMenuY}px;"
      onclick={(e) => e.stopPropagation()}
    >
      {#if contextMenuNode}
        <button class="menu-item" onclick={() => openThreadDrawer(contextMenuNode.id)}>
          📖 Inspect Full Thread
        </button>
        <button class="menu-item" onclick={() => togglePinNode(contextMenuNode)}>
          📌 {contextMenuNode.isPinned ? 'Unpin Node Position' : 'Pin Node Position'}
        </button>
        <button class="menu-item" onclick={() => selectedActionabilityTier.set(contextMenuNode.actionability_tier)}>
          🏷️ Filter by Tier ({contextMenuNode.actionability_tier || 'standard'})
        </button>
        <button class="menu-item" onclick={() => copyThreadId(contextMenuNode.id)}>
          📋 Copy Thread ID
        </button>
      {:else}
        <div class="menu-header">🌌 Graph Canvas Actions</div>
        <button class="menu-item" onclick={() => { resetCameraView(); closeContextMenu(); }}>
          🎯 Reset Camera & Zoom
        </button>
        <button class="menu-item" onclick={() => { hideOneOffChats.update(v => !v); closeContextMenu(); }}>
          ⚡ Toggle One-Off Chats ({#if $hideOneOffChats}Show{:else}Hide{/if})
        </button>
        <button class="menu-item" onclick={() => { hideAppCommands.update(v => !v); closeContextMenu(); }}>
          📱 Toggle App Commands ({#if $hideAppCommands}Show{:else}Hide{/if})
        </button>
      {/if}
    </div>
  {/if}

  <div class="d3-badge">🪐 D3.js Force Engine • Middle Click: Pan • Left Click: Drag & Select • Right Click: Menu</div>
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

  .tooltip {
    position: absolute;
    background: rgba(15, 23, 42, 0.92);
    border: 1px solid rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(12px);
    padding: 0.5rem 0.75rem;
    border-radius: 8px;
    color: #f8fafc;
    font-size: 0.8rem;
    pointer-events: none;
    z-index: 1000;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.5);
    max-width: 260px;
  }

  .tooltip-title {
    font-weight: 600;
    color: #38bdf8;
    margin-bottom: 0.2rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    line-height: 1.35;
  }

  .tooltip-meta {
    font-size: 0.7rem;
    color: #94a3b8;
  }

  .context-menu {
    position: fixed;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(16px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 10px;
    padding: 0.5rem;
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
    min-width: 210px;
    z-index: 1300;
    box-shadow: 0 10px 30px rgba(0, 0, 0, 0.7);
  }

  .menu-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #fbbf24;
    padding: 0.35rem 0.6rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    margin-bottom: 0.2rem;
  }

  .menu-item {
    background: none;
    border: none;
    color: #cbd5e1;
    text-align: left;
    padding: 0.4rem 0.6rem;
    border-radius: 6px;
    font-size: 0.8rem;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .menu-item:hover {
    background: rgba(59, 130, 246, 0.2);
    color: #ffffff;
  }
</style>
