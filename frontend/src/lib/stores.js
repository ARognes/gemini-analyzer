import { writable } from 'svelte/store';

// Navigation state - Default to D3.js Engine
export const activeSubtab = writable('d3_constellation'); // 'd3_constellation', 'topic_clusters', 'mindmap', 'matrix'

// System Stats state
/** @type {import('svelte/store').Writable<any>} */
export const stats = writable({ total_chats: 0, voice_chats: 0, total_threads: 0 });

// Global Graph Filters
export const hideOneOffChats = writable(true);
export const hideAppCommands = writable(true);
export const selectedActionabilityTier = writable(''); // '', 'large_project', 'standard', 'one_off', 'app_command'
export const minTurnsFilter = writable(1);
export const maxTurnsFilter = writable(50);
export const correlationThresholdPct = writable(38);

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
