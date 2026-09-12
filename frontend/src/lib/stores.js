import { writable } from 'svelte/store';

// Navigation state - Default to D3.js Engine
export const activeSubtab = writable('d3_constellation'); // 'd3_constellation', 'topic_clusters', 'mindmap', 'matrix'

// System Stats state
/** @type {import('svelte/store').Writable<any>} */
export const stats = writable({ total_chats: 0, voice_chats: 0, total_threads: 0 });

// Global Graph Filters
export const hideOneOffChats = writable(false);
export const selectedActionabilityTier = writable(''); // '', 'large_project', 'standard', 'one_off'
export const minTurnsFilter = writable(1);
export const maxTurnsFilter = writable(100);
export const minEdgesFilter = writable(0);
export const maxEdgesFilter = writable(50);
export const correlationThresholdPct = writable(38);

// Graph Perspective Sub-Views
export const graphPerspective = writable('global'); // 'global' (Full Universe), 'high_yield' (Deep High-Turn Core), 'macro_domains' (Domain Clusters)
export const minYieldTurns = writable(5); // Minimum turn threshold for high-yield perspective
export const selectedMacroDomain = writable(''); // Filter by specific macro domain ('', 'software', 'hardware', 'ai_agents', etc.)
/** @type {import('svelte/store').Writable<Array<any>>} */
export const macroDomainsList = writable([]); // Dynamic list of 7 Macro Super-Groups

// Layering & Group Filters
export const showUnlinkedNodes = writable(true); // Toggle 0-edge nodes
export const showUngroupedNodes = writable(true); // Toggle standalone nodes with no group
export const allGroupsEnabled = writable(true); // Master toggle for all groups
/** @type {import('svelte/store').Writable<Set<string>>} */
export const selectedGroupTags = writable(new Set()); // Set of enabled group tag names (empty = all enabled)
/** @type {import('svelte/store').Writable<Array<{tag: string, count: number, color?: string}>>} */
export const availableGroupTags = writable([]); // Dynamic list of all multi-node groups
export const isLayerFiltersOpen = writable(false);

// Histogram Distribution Data
/** @type {import('svelte/store').Writable<Array<{bin: number, count: number}>>} */
export const degreeHistogramData = writable([]); // Array of { bin: degree, count: nNodes }
/** @type {import('svelte/store').Writable<Array<{bin: number, count: number}>>} */
export const turnsHistogramData = writable([]); // Array of { bin: turnCount, count: nNodes }

// Subgraph Search state
export const activeSearchQuery = writable('');
/** @type {import('svelte/store').Writable<any>} */
export const searchResultsData = writable(null); // { query, matching_nodes, matching_edges, threads }
/** @type {import('svelte/store').Writable<Set<any>>} */
export const searchMatchingNodeIds = writable(new Set());
/** @type {import('svelte/store').Writable<Set<any>>} */
export const searchPathEdges = writable(new Set());
export const isSearchDrawerOpen = writable(false);

// Interaction & Selection state
/** @type {import('svelte/store').Writable<any>} */
export const hoveredNode = writable(null);
/** @type {import('svelte/store').Writable<any>} */
export const selectedNode = writable(null);
/** @type {import('svelte/store').Writable<any>} */
export const activeThreadDrawerData = writable(null); // Full thread object when inspected
export const isThreadDrawerOpen = writable(false);

// Correlation Modal state
export const isCorrelationModalOpen = writable(false);
/** @type {import('svelte/store').Writable<any>} */
export const correlationModalData = writable(null);

