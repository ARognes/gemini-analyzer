<script>
  import { onMount, onDestroy } from 'svelte';
  import { 
    hideOneOffChats, 
    hideAppCommands, 
    selectedActionabilityTier, 
    minTurnsFilter, 
    maxTurnsFilter,
    hoveredNode,
    selectedNode,
    activeSearchQuery,
    searchMatchingNodeIds,
    searchPathEdges,
    isThreadDrawerOpen,
    activeThreadDrawerData
  } from '../stores.js';
  import { fetchCanvasData, fetchStitchedThread } from '../api.js';

  let canvasEl;
  let ctx;
  let animFrameId;

  let graphData = $state({ nodes: [], relations: [] });
  let isLoaded = $state(false);

  // Pan & Zoom viewport state
  let panX = $state(0);
  let panY = $state(0);
  let scale = $state(1.0);
  let isDraggingCanvas = false;
  let dragStartX = 0;
  let dragStartY = 0;

  let draggedNode = null;
  let lastClickTime = 0;
  let clickTimeout = null;

  let jellyTime = 0;

  // Reactivity to graph stores
  $effect(() => {
    // Redraw whenever stores update
    if (isLoaded && ctx) {
      drawCanvas();
    }
  });

  onMount(async () => {
    ctx = canvasEl.getContext('2d');
    resizeCanvas();
    window.addEventListener('resize', resizeCanvas);

    try {
      const data = await fetchCanvasData('chat');
      graphData = data;
      layoutConstellation();
      runWarmupPhysicsSimulation(40);
      isLoaded = true;
      requestAnimationFrame(physicsStep);
    } catch (err) {
      console.error('Failed to load canvas data:', err);
    }
  });

  onDestroy(() => {
    if (animFrameId) cancelAnimationFrame(animFrameId);
    window.removeEventListener('resize', resizeCanvas);
  });

  function resizeCanvas() {
    if (!canvasEl) return;
    canvasEl.width = canvasEl.clientWidth || window.innerWidth;
    canvasEl.height = canvasEl.clientHeight || window.innerHeight;
    if (isLoaded) drawCanvas();
  }

  function layoutConstellation() {
    const nodes = graphData.nodes || [];
    const numNodes = nodes.length;
    if (numNodes === 0) return;

    // Cluster nodes by data_tag / category into sector angles
    const clusters = {};
    nodes.forEach(n => {
      const tag = n.data_tag || n.category || 'outliers';
      if (!clusters[tag]) clusters[tag] = [];
      clusters[tag].push(n);
    });

    const tags = Object.keys(clusters);
    const numClusters = tags.length;
    const centerCanvasX = 1600;
    const centerCanvasY = 1100;
    const mainRadius = 850;

    tags.forEach((tag, idx) => {
      const angle = (idx / numClusters) * Math.PI * 2;
      const sectorCenterX = centerCanvasX + Math.cos(angle) * mainRadius;
      const sectorCenterY = centerCanvasY + Math.sin(angle) * mainRadius;

      const clusterNodes = clusters[tag];
      const goldenAngle = 2.399963229728653;
      clusterNodes.forEach((n, nIdx) => {
        const r = 35 * Math.sqrt(nIdx + 1);
        const theta = nIdx * goldenAngle;
        n.worldX = sectorCenterX + r * Math.cos(theta);
        n.worldY = sectorCenterY + r * Math.sin(theta);
        n.targetX = n.worldX;
        n.targetY = n.worldY;
        n.vx = 0;
        n.vy = 0;
        n.radius = Math.max(7, Math.min(18, 5 + (n.turn_count || 1) * 0.8));
      });
    });

    // Center camera viewport
    panX = (canvasEl.width / 2) - (centerCanvasX * scale);
    panY = (canvasEl.height / 2) - (centerCanvasY * scale);
  }

  function runWarmupPhysicsSimulation(steps = 40) {
    const nodes = graphData.nodes || [];
    const relations = graphData.relations || [];
    if (nodes.length === 0) return;

    const activeNodes = nodes.filter(n => typeof n.worldX === 'number');
    const nodeMap = {};
    activeNodes.forEach(n => {
      nodeMap[n.id] = n;
      if (typeof n.vx !== 'number') { n.vx = 0; n.vy = 0; }
    });

    const cellSize = 140;

    for (let k = 0; k < steps; k++) {
      const grid = {};
      activeNodes.forEach(n => {
        const gx = Math.floor(n.worldX / cellSize);
        const gy = Math.floor(n.worldY / cellSize);
        const key = `${gx}:${gy}`;
        if (!grid[key]) grid[key] = [];
        grid[key].push(n);
      });

      activeNodes.forEach(n1 => {
        const gx = Math.floor(n1.worldX / cellSize);
        const gy = Math.floor(n1.worldY / cellSize);

        for (let dgx = -1; dgx <= 1; dgx++) {
          for (let dgy = -1; dgy <= 1; dgy++) {
            const cellNodes = grid[`${gx + dgx}:${gy + dgy}`];
            if (!cellNodes) continue;

            for (let i = 0; i < cellNodes.length; i++) {
              const n2 = cellNodes[i];
              if (n1.id >= n2.id) continue;

              const dx = n2.worldX - n1.worldX;
              const dy = n2.worldY - n1.worldY;
              const distSq = dx * dx + dy * dy;
              const minDist = 110;

              if (distSq > 0 && distSq < (minDist * minDist)) {
                const dist = Math.sqrt(distSq) || 1;
                const overlap = minDist - dist;
                const repelForce = overlap * 0.45;

                const fx = (dx / dist) * repelForce;
                const fy = (dy / dist) * repelForce;

                if (!n1.isPinned) { n1.vx -= fx; n1.vy -= fy; }
                if (!n2.isPinned) { n2.vx += fx; n2.vy += fy; }
              }
            }
          }
        }
      });

      relations.forEach(rel => {
        if (rel.similarity_score >= 0.25) {
          const source = nodeMap[rel.source_key];
          const target = nodeMap[rel.target_key];
          if (source && target) {
            const dx = target.worldX - source.worldX;
            const dy = target.worldY - source.worldY;
            const dist = Math.sqrt(dx * dx + dy * dy) || 1;

            const restLength = Math.max(70, 150 * (1.0 - rel.similarity_score * 0.5));
            const delta = dist - restLength;
            const springForce = delta * 0.18;

            const fx = (dx / dist) * springForce;
            const fy = (dy / dist) * springForce;

            if (!source.isPinned) { source.vx += fx; source.vy += fy; }
            if (!target.isPinned) { target.vx -= fx; target.vy -= fy; }
          }
        }
      });

      activeNodes.forEach(n => {
        if (!n.isPinned) {
          n.worldX += n.vx;
          n.worldY += n.vy;
          n.vx *= 0.65;
          n.vy *= 0.65;
        }
      });
    }
  }

  function physicsStep() {
    jellyTime += 0.03;
    const nodes = graphData.nodes || [];
    const relations = graphData.relations || [];

    if (nodes.length > 0) {
      const activeSimNodes = nodes.filter(n => typeof n.worldX === 'number');
      const cellSize = 160;
      const grid = {};
      const neighborCounts = {};

      activeSimNodes.forEach(n => {
        neighborCounts[n.id] = 0;
        const gx = Math.floor(n.worldX / cellSize);
        const gy = Math.floor(n.worldY / cellSize);
        const key = `${gx}:${gy}`;
        if (!grid[key]) grid[key] = [];
        grid[key].push(n);
      });

      activeSimNodes.forEach(n1 => {
        const gx = Math.floor(n1.worldX / cellSize);
        const gy = Math.floor(n1.worldY / cellSize);

        for (let dgx = -1; dgx <= 1; dgx++) {
          for (let dgy = -1; dgy <= 1; dgy++) {
            const cellNodes = grid[`${gx + dgx}:${gy + dgy}`];
            if (!cellNodes) continue;

            for (let i = 0; i < cellNodes.length; i++) {
              const n2 = cellNodes[i];
              if (n1.id >= n2.id) continue;

              const dx = n2.worldX - n1.worldX;
              const dy = n2.worldY - n1.worldY;
              if (dx * dx + dy * dy < 25600) {
                neighborCounts[n1.id]++;
                neighborCounts[n2.id]++;
              }
            }
          }
        }
      });

      activeSimNodes.forEach(n1 => {
        const gx = Math.floor(n1.worldX / cellSize);
        const gy = Math.floor(n1.worldY / cellSize);
        const r1 = n1.radius || 8;
        const density1 = neighborCounts[n1.id] || 0;

        for (let dgx = -1; dgx <= 1; dgx++) {
          for (let dgy = -1; dgy <= 1; dgy++) {
            const cellNodes = grid[`${gx + dgx}:${gy + dgy}`];
            if (!cellNodes) continue;

            for (let i = 0; i < cellNodes.length; i++) {
              const n2 = cellNodes[i];
              if (n1.id >= n2.id) continue;

              const r2 = n2.radius || 8;
              const density2 = neighborCounts[n2.id] || 0;
              const dx = n2.worldX - n1.worldX;
              const dy = n2.worldY - n1.worldY;
              const distSq = dx * dx + dy * dy;

              const maxDensity = Math.max(density1, density2);
              const densityCushion = Math.min(65, maxDensity * 8.5);
              const minDist = r1 + r2 + 45 + densityCushion;

              if (distSq > 0 && distSq < (minDist * minDist)) {
                const dist = Math.sqrt(distSq) || 1;
                const overlap = minDist - dist;
                const repelForce = overlap * (0.28 + Math.min(0.4, maxDensity * 0.05));

                const fx = (dx / dist) * repelForce;
                const fy = (dy / dist) * repelForce;

                if (!n1.isPinned) { n1.vx -= fx; n1.vy -= fy; }
                if (!n2.isPinned) { n2.vx += fx; n2.vy += fy; }
              }
            }
          }
        }
      });

      nodes.forEach(n => {
        if (typeof n.worldX === 'number' && !n.isPinned) {
          const waveX = Math.sin(jellyTime + (n.worldY * 0.006)) * 0.08;
          const waveY = Math.cos(jellyTime * 0.85 + (n.worldX * 0.006)) * 0.08;
          n.vx += waveX;
          n.vy += waveY;

          n.vx *= 0.70;
          n.vy *= 0.70;

          n.worldX += n.vx;
          n.worldY += n.vy;
        }
      });
    }

    drawCanvas();
    animFrameId = requestAnimationFrame(physicsStep);
  }

  function drawCanvas() {
    if (!ctx || !canvasEl) return;
    const w = canvasEl.width;
    const h = canvasEl.height;

    ctx.clearRect(0, 0, w, h);
    ctx.save();
    ctx.translate(panX, panY);
    ctx.scale(scale, scale);

    const nodes = graphData.nodes || [];
    const relations = graphData.relations || [];

    const nodeMap = {};
    const visibleNodes = new Set();

    nodes.forEach(n => {
      if (typeof n.worldX !== 'number') return;
      if ($hideOneOffChats && (n.actionability_tier === 'one_off' || n.turn_count <= 1)) return;
      if ($hideAppCommands && n.actionability_tier === 'app_command') return;
      if ($selectedActionabilityTier && n.actionability_tier !== $selectedActionabilityTier) return;
      if (n.turn_count < $minTurnsFilter || n.turn_count > $maxTurnsFilter) return;

      nodeMap[n.id] = n;
      visibleNodes.add(n.id);
    });

    const isSubgraphActive = $searchMatchingNodeIds.size > 0;

    // Draw Edges
    relations.forEach(rel => {
      if (!visibleNodes.has(rel.source_key) || !visibleNodes.has(rel.target_key)) return;

      const src = nodeMap[rel.source_key];
      const tgt = nodeMap[rel.target_key];
      if (!src || !tgt) return;

      const isPathEdge = $searchPathEdges.has(rel.id);
      const isSelected = $selectedNode && ($selectedNode.id === src.id || $selectedNode.id === tgt.id);

      ctx.beginPath();
      ctx.moveTo(src.worldX, src.worldY);
      ctx.lineTo(tgt.worldX, tgt.worldY);

      if (isPathEdge) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 3.5;
        ctx.shadowColor = '#f59e0b';
        ctx.shadowBlur = 18;
      } else if (isSelected) {
        ctx.strokeStyle = '#60a5fa';
        ctx.lineWidth = 2.5;
        ctx.shadowBlur = 0;
      } else {
        ctx.strokeStyle = isSubgraphActive ? 'rgba(255, 255, 255, 0.04)' : 'rgba(255, 255, 255, 0.12)';
        ctx.lineWidth = 1.0;
        ctx.shadowBlur = 0;
      }
      ctx.stroke();
      ctx.shadowBlur = 0;
    });

    // Draw Nodes
    nodes.forEach(n => {
      if (!visibleNodes.has(n.id)) return;

      const isMatch = $searchMatchingNodeIds.has(n.id);
      const isHovered = $hoveredNode && $hoveredNode.id === n.id;
      const isSel = $selectedNode && $selectedNode.id === n.id;

      ctx.beginPath();
      ctx.arc(n.worldX, n.worldY, n.radius || 8, 0, Math.PI * 2);

      let color = '#3b82f6';
      if (n.actionability_tier === 'large_project') color = '#8b5cf6';
      if (n.actionability_tier === 'app_command') color = '#ec4899';

      if (isMatch) color = '#f59e0b';
      if (isSel) color = '#38bdf8';

      ctx.fillStyle = isSubgraphActive && !isMatch ? 'rgba(100, 116, 139, 0.25)' : color;
      ctx.fill();

      if (isMatch) {
        ctx.strokeStyle = '#f59e0b';
        ctx.lineWidth = 3.0;
        ctx.stroke();
      } else if (isHovered || isSel) {
        ctx.strokeStyle = '#ffffff';
        ctx.lineWidth = 2.0;
        ctx.stroke();
      }
    });

    ctx.restore();
  }

  function screenToWorld(sx, sy) {
    return {
      x: (sx - panX) / scale,
      y: (sy - panY) / scale
    };
  }

  function handleMouseDown(e) {
    const rect = canvasEl.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;
    const world = screenToWorld(mx, my);

    // Check hit test
    const nodes = graphData.nodes || [];
    const hit = nodes.find(n => {
      if (typeof n.worldX !== 'number') return false;
      const dx = n.worldX - world.x;
      const dy = n.worldY - world.y;
      return (dx * dx + dy * dy) <= ((n.radius || 8) + 6) ** 2;
    });

    if (hit) {
      draggedNode = hit;
      draggedNode.isPinned = true;

      // Handle single / double click logic
      const now = Date.now();
      if (now - lastClickTime < 300) {
        // Double click -> open thread inspector drawer
        if (clickTimeout) clearTimeout(clickTimeout);
        openThreadDrawer(hit.id);
      } else {
        // Single click -> highlight node
        clickTimeout = setTimeout(() => {
          selectedNode.set(hit);
        }, 250);
      }
      lastClickTime = now;
    } else {
      isDraggingCanvas = true;
      dragStartX = e.clientX - panX;
      dragStartY = e.clientY - panY;
    }
  }

  function handleMouseMove(e) {
    const rect = canvasEl.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    if (draggedNode) {
      const world = screenToWorld(mx, my);
      draggedNode.worldX = world.x;
      draggedNode.worldY = world.y;
      drawCanvas();
      return;
    }

    if (isDraggingCanvas) {
      panX = e.clientX - dragStartX;
      panY = e.clientY - dragStartY;
      drawCanvas();
      return;
    }

    // Hover hit test
    const world = screenToWorld(mx, my);
    const nodes = graphData.nodes || [];
    const hit = nodes.find(n => {
      if (typeof n.worldX !== 'number') return false;
      const dx = n.worldX - world.x;
      const dy = n.worldY - world.y;
      return (dx * dx + dy * dy) <= ((n.radius || 8) + 6) ** 2;
    });

    hoveredNode.set(hit || null);
  }

  function handleMouseUp() {
    if (draggedNode) {
      draggedNode.isPinned = false;
      draggedNode = null;
    }
    isDraggingCanvas = false;
  }

  function handleWheel(e) {
    e.preventDefault();
    const zoomFactor = e.deltaY < 0 ? 1.12 : 0.88;
    const rect = canvasEl.getBoundingClientRect();
    const mx = e.clientX - rect.left;
    const my = e.clientY - rect.top;

    const mouseWorldBefore = screenToWorld(mx, my);
    scale *= zoomFactor;
    scale = Math.max(0.15, Math.min(5.0, scale));

    panX = mx - (mouseWorldBefore.x * scale);
    panY = my - (mouseWorldBefore.y * scale);
    drawCanvas();
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

<div class="canvas-wrapper">
  <canvas 
    id="constellationCanvas"
    bind:this={canvasEl}
    onmousedown={handleMouseDown}
    onmousemove={handleMouseMove}
    onmouseup={handleMouseUp}
    onwheel={handleWheel}
  ></canvas>

  {#if $hoveredNode}
    <div 
      class="tooltip"
      style="left: {panX + ($hoveredNode.worldX * scale) + 15}px; top: {panY + ($hoveredNode.worldY * scale) - 20}px;"
    >
      <div class="tooltip-title">{$hoveredNode.title || $hoveredNode.title_snippet}</div>
      <div class="tooltip-meta">Turns: {$hoveredNode.turn_count || 1} • Tier: {$hoveredNode.actionability_tier || 'standard'}</div>
    </div>
  {/if}
</div>

<style>
  .canvas-wrapper {
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
  }

  .tooltip-meta {
    font-size: 0.7rem;
    color: #94a3b8;
  }
</style>
