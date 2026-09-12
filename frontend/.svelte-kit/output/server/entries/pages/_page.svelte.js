import { n as onDestroy } from "../../chunks/index-server.js";
import { C as escape_html, E as writable, S as attr, c as stringify, d as html, i as ensure_array_like, l as unsubscribe_stores, n as attr_style, r as derived, s as store_get, t as attr_class } from "../../chunks/server.js";
import "../../chunks/index-server2.js";
import * as d3 from "d3";
//#region src/lib/stores.js
var activeSubtab = writable("d3_constellation");
/** @type {import('svelte/store').Writable<any>} */
var stats = writable({
	total_chats: 0,
	voice_chats: 0,
	total_threads: 0
});
var hideOneOffChats = writable(false);
var hideAppCommands = writable(false);
var selectedActionabilityTier = writable("");
var minTurnsFilter = writable(1);
var maxTurnsFilter = writable(100);
var minEdgesFilter = writable(0);
var maxEdgesFilter = writable(50);
var correlationThresholdPct = writable(38);
var showUnlinkedNodes = writable(true);
var showUngroupedNodes = writable(true);
var allGroupsEnabled = writable(true);
/** @type {import('svelte/store').Writable<Set<string>>} */
var selectedGroupTags = writable(/* @__PURE__ */ new Set());
/** @type {import('svelte/store').Writable<Array<{tag: string, count: number, color?: string}>>} */
var availableGroupTags = writable([]);
var isLayerFiltersOpen = writable(false);
/** @type {import('svelte/store').Writable<Array<{bin: number, count: number}>>} */
var degreeHistogramData = writable([]);
/** @type {import('svelte/store').Writable<Array<{bin: number, count: number}>>} */
var turnsHistogramData = writable([]);
var activeSearchQuery = writable("");
/** @type {import('svelte/store').Writable<any>} */
var searchResultsData = writable(null);
writable(/* @__PURE__ */ new Set());
writable(/* @__PURE__ */ new Set());
var isSearchDrawerOpen = writable(false);
/** @type {import('svelte/store').Writable<any>} */
var hoveredNode = writable(null);
writable(null);
/** @type {import('svelte/store').Writable<any>} */
var activeThreadDrawerData = writable(null);
var isThreadDrawerOpen = writable(false);
var isCorrelationModalOpen = writable(false);
writable(null);
//#endregion
//#region src/lib/components/Header.svelte
function Header($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		$$renderer.push(`<header class="navbar svelte-1elxaub"><div class="brand svelte-1elxaub"><span class="icon svelte-1elxaub">🌌</span> <span class="title">Gemini Constellation</span> <span class="badge svelte-1elxaub">v2.0 Svelte</span></div> <div class="stats-row svelte-1elxaub"><div class="stat-pill svelte-1elxaub"><span class="val svelte-1elxaub">${escape_html(store_get($$store_subs ??= {}, "$stats", stats).total_chats.toLocaleString())}</span> <span class="lbl svelte-1elxaub">Chats</span></div> <div class="stat-pill svelte-1elxaub"><span class="val svelte-1elxaub">${escape_html(store_get($$store_subs ??= {}, "$stats", stats).voice_chats.toLocaleString())}</span> <span class="lbl svelte-1elxaub">Voice Inputs</span></div> <div class="stat-pill accent svelte-1elxaub"><span class="val svelte-1elxaub">${escape_html(store_get($$store_subs ??= {}, "$stats", stats).total_threads.toLocaleString())}</span> <span class="lbl svelte-1elxaub">Thread Clusters</span></div></div> <div class="search-container svelte-1elxaub"><span class="search-icon svelte-1elxaub">🔍</span> <input type="text" id="canvasSearch" placeholder="Search interwoven topics (e.g., 'jam', 'lock picking')..."${attr("value", "")} class="svelte-1elxaub"/> `);
		$$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--></div> <div class="subtabs svelte-1elxaub"><button${attr_class("subtab-btn svelte-1elxaub", void 0, { "active": store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "d3_constellation" })} id="subtabD3">🌌 Graph</button> <button${attr_class("subtab-btn svelte-1elxaub", void 0, { "active": store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "mindmap" })} id="subtabMindmap">🌳 Mindmap Tree</button> <button${attr_class("subtab-btn svelte-1elxaub", void 0, { "active": store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "matrix" })} id="subtabMatrix">📊 Similarity Matrix</button></div></header>`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
//#region src/lib/components/FilterBar.svelte
function FilterBar($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		let groupSearchQuery = "";
		let filteredGroupTags = derived(() => (store_get($$store_subs ??= {}, "$availableGroupTags", availableGroupTags) || []).filter((g) => true));
		let activeFiltersCount = derived(() => (store_get($$store_subs ??= {}, "$hideOneOffChats", hideOneOffChats) ? 1 : 0) + (store_get($$store_subs ??= {}, "$hideAppCommands", hideAppCommands) ? 1 : 0) + (store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) ? 1 : 0) + (store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter) > 1 || store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter) < 100 ? 1 : 0) + (store_get($$store_subs ??= {}, "$minEdgesFilter", minEdgesFilter) > 0 || store_get($$store_subs ??= {}, "$maxEdgesFilter", maxEdgesFilter) < 50 ? 1 : 0) + (!store_get($$store_subs ??= {}, "$showUnlinkedNodes", showUnlinkedNodes) ? 1 : 0) + (!store_get($$store_subs ??= {}, "$showUngroupedNodes", showUngroupedNodes) ? 1 : 0) + (!store_get($$store_subs ??= {}, "$allGroupsEnabled", allGroupsEnabled) ? 1 : 0));
		$$renderer.push(`<div class="filter-system svelte-m9tjun"><div class="filter-bar svelte-m9tjun"><button${attr_class("layer-toggle-btn svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$isLayerFiltersOpen", isLayerFiltersOpen) })}><span class="icon">🎛️</span> <span class="label">Layering Filters &amp; Scales</span> `);
		if (activeFiltersCount() > 0) $$renderer.push(`<!--[0--><span class="filter-count-badge svelte-m9tjun">${escape_html(activeFiltersCount())}</span>`);
		else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--> <span class="chevron svelte-m9tjun">${escape_html(store_get($$store_subs ??= {}, "$isLayerFiltersOpen", isLayerFiltersOpen) ? "▲" : "▼")}</span></button> <div class="filter-group svelte-m9tjun"><span class="group-label svelte-m9tjun">Tier:</span> <button${attr_class("pill-btn svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) === "" })}>All</button> <button${attr_class("pill-btn tier-project svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) === "large_project" })}>🚀 Projects</button> <button${attr_class("pill-btn tier-standard svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) === "standard" })}>💬 Threads</button></div> <div class="filter-group svelte-m9tjun"><span class="group-label svelte-m9tjun">Quick:</span> <button${attr_class("toggle-pill svelte-m9tjun", void 0, { "active": !store_get($$store_subs ??= {}, "$showUnlinkedNodes", showUnlinkedNodes) })} title="Toggle visibility of chats with 0 edge connections">🔗 Unlinked: <span class="state svelte-m9tjun">`);
		if (store_get($$store_subs ??= {}, "$showUnlinkedNodes", showUnlinkedNodes)) $$renderer.push(`<!--[0-->SHOWN`);
		else $$renderer.push(`<!--[-1-->HIDDEN`);
		$$renderer.push(`<!--]--></span></button> <button${attr_class("toggle-pill svelte-m9tjun", void 0, { "active": !store_get($$store_subs ??= {}, "$showUngroupedNodes", showUngroupedNodes) })} title="Toggle visibility of chats with no group">🏷️ Ungrouped: <span class="state svelte-m9tjun">`);
		if (store_get($$store_subs ??= {}, "$showUngroupedNodes", showUngroupedNodes)) $$renderer.push(`<!--[0-->SHOWN`);
		else $$renderer.push(`<!--[-1-->HIDDEN`);
		$$renderer.push(`<!--]--></span></button></div> <div class="filter-group right-group svelte-m9tjun"><button class="corr-btn svelte-m9tjun">📊 Similarity: <span class="val svelte-m9tjun">${escape_html(store_get($$store_subs ??= {}, "$correlationThresholdPct", correlationThresholdPct))}%</span></button> `);
		if (activeFiltersCount() > 0) $$renderer.push(`<!--[0--><button class="reset-btn svelte-m9tjun" title="Reset all filters">↺ Reset</button>`);
		else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--></div></div> `);
		if (store_get($$store_subs ??= {}, "$isLayerFiltersOpen", isLayerFiltersOpen)) {
			$$renderer.push(`<!--[0--><div class="layer-panel svelte-m9tjun"><div class="panel-section svelte-m9tjun"><div class="section-header svelte-m9tjun"><div class="title-with-badge svelte-m9tjun"><span class="section-icon svelte-m9tjun">🔗</span> <span class="section-title svelte-m9tjun">Edge Connections Range</span> <span class="range-badge svelte-m9tjun">${escape_html(store_get($$store_subs ??= {}, "$minEdgesFilter", minEdgesFilter))} – ${escape_html(store_get($$store_subs ??= {}, "$maxEdgesFilter", maxEdgesFilter))} edges</span></div> <button class="mini-reset svelte-m9tjun">Reset</button></div> <div class="histogram-box svelte-m9tjun"><svg class="hist-svg svelte-m9tjun" viewBox="0 0 300 45" preserveAspectRatio="none">`);
			if (store_get($$store_subs ??= {}, "$degreeHistogramData", degreeHistogramData) && store_get($$store_subs ??= {}, "$degreeHistogramData", degreeHistogramData).length > 0) {
				$$renderer.push("<!--[0-->");
				const maxCount = Math.max(...store_get($$store_subs ??= {}, "$degreeHistogramData", degreeHistogramData).map((d) => d.count), 1);
				$$renderer.push(`<!--[-->`);
				const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$degreeHistogramData", degreeHistogramData));
				for (let idx = 0, $$length = each_array.length; idx < $$length; idx++) {
					let d = each_array[idx];
					const barH = Math.max(2, d.count / maxCount * 40);
					const inRange = d.bin >= store_get($$store_subs ??= {}, "$minEdgesFilter", minEdgesFilter) && d.bin <= store_get($$store_subs ??= {}, "$maxEdgesFilter", maxEdgesFilter);
					$$renderer.push(`<rect${attr("x", idx * (300 / store_get($$store_subs ??= {}, "$degreeHistogramData", degreeHistogramData).length))}${attr("y", 45 - barH)}${attr("width", Math.max(1.5, 300 / store_get($$store_subs ??= {}, "$degreeHistogramData", degreeHistogramData).length - 1))}${attr("height", barH)}${attr("fill", inRange ? "#38bdf8" : "rgba(100, 116, 139, 0.25)")} rx="1"></rect>`);
				}
				$$renderer.push(`<!--]-->`);
			} else $$renderer.push("<!--[-1-->");
			$$renderer.push(`<!--]--></svg> <div class="slider-dual svelte-m9tjun"><div class="slider-row svelte-m9tjun"><span class="slider-lbl svelte-m9tjun">Min (${escape_html(store_get($$store_subs ??= {}, "$minEdgesFilter", minEdgesFilter))}):</span> <input type="range" min="0" max="50"${attr("value", store_get($$store_subs ??= {}, "$minEdgesFilter", minEdgesFilter))} class="svelte-m9tjun"/></div> <div class="slider-row svelte-m9tjun"><span class="slider-lbl svelte-m9tjun">Max (${escape_html(store_get($$store_subs ??= {}, "$maxEdgesFilter", maxEdgesFilter))}):</span> <input type="range" min="0" max="50"${attr("value", store_get($$store_subs ??= {}, "$maxEdgesFilter", maxEdgesFilter))} class="svelte-m9tjun"/></div></div></div></div> <div class="panel-section svelte-m9tjun"><div class="section-header svelte-m9tjun"><div class="title-with-badge svelte-m9tjun"><span class="section-icon svelte-m9tjun">💬</span> <span class="section-title svelte-m9tjun">Chat Turn Depth Range</span> <span class="range-badge svelte-m9tjun">${escape_html(store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter))} – ${escape_html(store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter))} turns</span></div> <button class="mini-reset svelte-m9tjun">Reset</button></div> <div class="histogram-box svelte-m9tjun"><svg class="hist-svg svelte-m9tjun" viewBox="0 0 300 45" preserveAspectRatio="none">`);
			if (store_get($$store_subs ??= {}, "$turnsHistogramData", turnsHistogramData) && store_get($$store_subs ??= {}, "$turnsHistogramData", turnsHistogramData).length > 0) {
				$$renderer.push("<!--[0-->");
				const maxCount = Math.max(...store_get($$store_subs ??= {}, "$turnsHistogramData", turnsHistogramData).map((d) => d.count), 1);
				$$renderer.push(`<!--[-->`);
				const each_array_1 = ensure_array_like(store_get($$store_subs ??= {}, "$turnsHistogramData", turnsHistogramData));
				for (let idx = 0, $$length = each_array_1.length; idx < $$length; idx++) {
					let d = each_array_1[idx];
					const barH = Math.max(2, d.count / maxCount * 40);
					const inRange = d.bin >= store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter) && d.bin <= store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter);
					$$renderer.push(`<rect${attr("x", idx * (300 / store_get($$store_subs ??= {}, "$turnsHistogramData", turnsHistogramData).length))}${attr("y", 45 - barH)}${attr("width", Math.max(1.5, 300 / store_get($$store_subs ??= {}, "$turnsHistogramData", turnsHistogramData).length - 1))}${attr("height", barH)}${attr("fill", inRange ? "#818cf8" : "rgba(100, 116, 139, 0.25)")} rx="1"></rect>`);
				}
				$$renderer.push(`<!--]-->`);
			} else $$renderer.push("<!--[-1-->");
			$$renderer.push(`<!--]--></svg> <div class="slider-dual svelte-m9tjun"><div class="slider-row svelte-m9tjun"><span class="slider-lbl svelte-m9tjun">Min (${escape_html(store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter))}):</span> <input type="range" min="1" max="100"${attr("value", store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter))} class="svelte-m9tjun"/></div> <div class="slider-row svelte-m9tjun"><span class="slider-lbl svelte-m9tjun">Max (${escape_html(store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter))}):</span> <input type="range" min="1" max="100"${attr("value", store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter))} class="svelte-m9tjun"/></div></div></div></div> <div class="panel-section group-section svelte-m9tjun"><div class="section-header svelte-m9tjun"><div class="title-with-badge svelte-m9tjun"><span class="section-icon svelte-m9tjun">🏷️</span> <span class="section-title svelte-m9tjun">Group Filters (${escape_html(store_get($$store_subs ??= {}, "$availableGroupTags", availableGroupTags).length)} Groups)</span></div> <div class="group-quick-actions svelte-m9tjun"><button${attr_class("action-btn svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$allGroupsEnabled", allGroupsEnabled) })}>All Groups</button> <button class="action-btn svelte-m9tjun">Deselect All</button> <button${attr_class("action-btn svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$showUngroupedNodes", showUngroupedNodes) })}>${escape_html(store_get($$store_subs ??= {}, "$showUngroupedNodes", showUngroupedNodes) ? "✓ Ungrouped" : "✕ Ungrouped")}</button></div></div> <input type="text" class="group-search svelte-m9tjun" placeholder="Filter group list by keyword..."${attr("value", groupSearchQuery)}/> <div class="group-chips-container svelte-m9tjun"><!--[-->`);
			const each_array_2 = ensure_array_like(filteredGroupTags());
			for (let $$index_2 = 0, $$length = each_array_2.length; $$index_2 < $$length; $$index_2++) {
				let g = each_array_2[$$index_2];
				const isSelected = store_get($$store_subs ??= {}, "$allGroupsEnabled", allGroupsEnabled) || store_get($$store_subs ??= {}, "$selectedGroupTags", selectedGroupTags).has(g.tag);
				$$renderer.push(`<button${attr_class("group-chip svelte-m9tjun", void 0, { "selected": isSelected })}><span class="chip-dot svelte-m9tjun"></span> <span class="chip-tag">${escape_html(g.tag)}</span> <span class="chip-count svelte-m9tjun">${escape_html(g.count)}</span></button>`);
			}
			$$renderer.push(`<!--]--></div></div></div>`);
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--></div>`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
//#region src/lib/components/D3Constellation.svelte
function D3Constellation($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		let loadProgress = 0;
		let loadMessage = "Fetching graph dataset...";
		let transform = d3.zoomIdentity;
		let isContextMenuOpen = false;
		let contextMenuX = 0;
		let contextMenuY = 0;
		let contextMenuNode = null;
		onDestroy(() => {
			window.removeEventListener("resize", resizeCanvas);
			window.removeEventListener("click", closeContextMenu);
		});
		function resizeCanvas() {}
		function closeContextMenu() {
			isContextMenuOpen = false;
			contextMenuNode = null;
		}
		$$renderer.push(`<div class="d3-wrapper svelte-vzurtw"><canvas id="constellationCanvas" class="svelte-vzurtw"></canvas> `);
		$$renderer.push(`<!--[0--><div${attr_class("loading-overlay svelte-vzurtw", void 0, { "fade-out": false })}><div class="spinner svelte-vzurtw"></div> <div class="loading-text svelte-vzurtw">🌌 Loading Constellation Graph...</div> <div class="loading-subtext svelte-vzurtw">${escape_html(loadMessage)}</div> <div class="progress-bar-container svelte-vzurtw"><div class="progress-bar-fill svelte-vzurtw"${attr_style(`width: ${stringify(loadProgress)}%;`)}></div></div> <div class="progress-percentage svelte-vzurtw">${escape_html(loadProgress)}%</div></div>`);
		$$renderer.push(`<!--]--> `);
		if (store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode)) $$renderer.push(`<!--[0--><div class="tooltip svelte-vzurtw"${attr_style(`left: ${stringify(transform.x + store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode).x * transform.k + 15)}px; top: ${stringify(transform.y + store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode).y * transform.k - 20)}px;`)}><div class="tooltip-title svelte-vzurtw">${escape_html(store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode).title || store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode).title_snippet)}</div> <div class="tooltip-meta svelte-vzurtw">Turns: ${escape_html(store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode).turn_count || 1)} • Tier: ${escape_html(store_get($$store_subs ??= {}, "$hoveredNode", hoveredNode).actionability_tier || "standard")}</div></div>`);
		else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--> `);
		if (isContextMenuOpen) {
			$$renderer.push(`<!--[0--><div class="context-menu svelte-vzurtw"${attr_style(`left: ${stringify(contextMenuX)}px; top: ${stringify(contextMenuY)}px;`)}>`);
			if (contextMenuNode) $$renderer.push(`<!--[0--><button class="menu-item svelte-vzurtw">📖 Inspect Full Thread</button> <button class="menu-item svelte-vzurtw">📌 ${escape_html(contextMenuNode.isPinned ? "Unpin Node Position" : "Pin Node Position")}</button> <button class="menu-item svelte-vzurtw">🏷️ Filter by Tier (${escape_html(contextMenuNode.actionability_tier || "standard")})</button> <button class="menu-item svelte-vzurtw">📋 Copy Thread ID</button>`);
			else {
				$$renderer.push(`<!--[-1--><div class="menu-header svelte-vzurtw">🌌 Graph Canvas Actions</div> <button class="menu-item svelte-vzurtw">🎯 Reset Camera &amp; Zoom</button> <button class="menu-item svelte-vzurtw">⚡ Toggle One-Off Chats (`);
				if (store_get($$store_subs ??= {}, "$hideOneOffChats", hideOneOffChats)) $$renderer.push(`<!--[0-->Show`);
				else $$renderer.push(`<!--[-1-->Hide`);
				$$renderer.push(`<!--]-->)</button> <button class="menu-item svelte-vzurtw">📱 Toggle App Commands (`);
				if (store_get($$store_subs ??= {}, "$hideAppCommands", hideAppCommands)) $$renderer.push(`<!--[0-->Show`);
				else $$renderer.push(`<!--[-1-->Hide`);
				$$renderer.push(`<!--]-->)</button>`);
			}
			$$renderer.push(`<!--]--></div>`);
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--> <div class="d3-badge svelte-vzurtw">🌌 Constellation Graph • Middle Click: Pan • Left Click: Drag &amp; Select • Right Click: Menu</div></div>`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
//#region src/lib/components/SubgraphDrawer.svelte
function SubgraphDrawer($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		if (store_get($$store_subs ??= {}, "$isSearchDrawerOpen", isSearchDrawerOpen) && store_get($$store_subs ??= {}, "$searchResultsData", searchResultsData)) {
			$$renderer.push(`<!--[0--><div class="drawer-overlay svelte-16ri759"></div> <aside class="subgraph-drawer svelte-16ri759" id="queryResultsDrawer"><div class="drawer-header svelte-16ri759"><div class="header-title svelte-16ri759"><span class="gold-icon">🔍</span> <span>Subgraph: "${escape_html(store_get($$store_subs ??= {}, "$activeSearchQuery", activeSearchQuery))}"</span></div> <button class="close-btn svelte-16ri759">✕</button></div> <div class="drawer-meta svelte-16ri759"><span>Found <strong>${escape_html(store_get($$store_subs ??= {}, "$searchResultsData", searchResultsData).threads ? store_get($$store_subs ??= {}, "$searchResultsData", searchResultsData).threads.length : 0)}</strong> matching threads</span> <div class="export-actions svelte-16ri759"><button class="export-btn md svelte-16ri759">📥 Export MD</button> <button class="export-btn json svelte-16ri759">📥 Export JSON</button></div></div> <div class="drawer-content svelte-16ri759">`);
			if (store_get($$store_subs ??= {}, "$searchResultsData", searchResultsData).threads && store_get($$store_subs ??= {}, "$searchResultsData", searchResultsData).threads.length > 0) {
				$$renderer.push(`<!--[0--><!--[-->`);
				const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$searchResultsData", searchResultsData).threads);
				for (let $$index_1 = 0, $$length = each_array.length; $$index_1 < $$length; $$index_1++) {
					let thread = each_array[$$index_1];
					$$renderer.push(`<div class="thread-card svelte-16ri759"><div class="card-header svelte-16ri759"><span class="thread-title svelte-16ri759">${escape_html(thread.title || thread.title_snippet)}</span> <span class="tier-tag svelte-16ri759">${escape_html(thread.actionability_tier || "standard")}</span></div> <div class="card-sub svelte-16ri759"><span>#${escape_html(thread.primary_tag || "general")}</span> <span>• ${escape_html(thread.turn_count)} turns</span></div> `);
					if (thread.matched_snippets && thread.matched_snippets.length > 0) {
						$$renderer.push(`<!--[0--><div class="snippets-container svelte-16ri759"><!--[-->`);
						const each_array_1 = ensure_array_like(thread.matched_snippets);
						for (let $$index = 0, $$length = each_array_1.length; $$index < $$length; $$index++) {
							let snippet = each_array_1[$$index];
							$$renderer.push(`<div class="snippet-box svelte-16ri759"><div class="snip-prompt svelte-16ri759"><strong>Prompt:</strong> ${escape_html(snippet.prompt_text)}</div> `);
							if (snippet.response_plain) $$renderer.push(`<!--[0--><div class="snip-response svelte-16ri759"><strong>Response:</strong> ${escape_html(snippet.response_plain.slice(0, 180))}...</div>`);
							else $$renderer.push("<!--[-1-->");
							$$renderer.push(`<!--]--></div>`);
						}
						$$renderer.push(`<!--]--></div>`);
					} else $$renderer.push("<!--[-1-->");
					$$renderer.push(`<!--]--></div>`);
				}
				$$renderer.push(`<!--]-->`);
			} else $$renderer.push(`<!--[-1--><div class="empty-state svelte-16ri759">No matching interwoven threads found for "${escape_html(store_get($$store_subs ??= {}, "$activeSearchQuery", activeSearchQuery))}".</div>`);
			$$renderer.push(`<!--]--></div></aside>`);
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]-->`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
//#region src/lib/components/ThreadDrawer.svelte
function ThreadDrawer($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		function getGeminiResponseHtml(turn) {
			if (!turn) return "";
			let html = turn.response_html || turn.response_plain || turn.response_text || "";
			if (!html) return "";
			html = html.replace(/\{"contentMetadata":[\s\S]*?\}/g, "").trim();
			return html;
		}
		if (store_get($$store_subs ??= {}, "$isThreadDrawerOpen", isThreadDrawerOpen) && store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData)) {
			$$renderer.push(`<!--[0--><div class="drawer-overlay svelte-1q68yr"></div> <aside class="thread-drawer svelte-1q68yr" id="sideDrawer"><div class="drawer-header svelte-1q68yr"><div class="header-title svelte-1q68yr"><span>💬 Thread Inspector</span></div> <button class="close-btn svelte-1q68yr">✕</button></div> <div class="thread-meta svelte-1q68yr"><h3 class="svelte-1q68yr">${escape_html(store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).title || store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).title_snippet)}</h3> <div class="tags-row svelte-1q68yr"><span class="badge svelte-1q68yr">${escape_html(store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).actionability_tier || "standard")}</span> `);
			if (store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).primary_tag) $$renderer.push(`<!--[0--><span class="badge tag svelte-1q68yr">#${escape_html(store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).primary_tag)}</span>`);
			else $$renderer.push("<!--[-1-->");
			$$renderer.push(`<!--]--> <span class="meta-item">Turns: ${escape_html(store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).turn_count || 1)}</span></div></div> <div class="drawer-content svelte-1q68yr">`);
			if (store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).turns && store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).turns.length > 0) {
				$$renderer.push(`<!--[0--><!--[-->`);
				const each_array = ensure_array_like(store_get($$store_subs ??= {}, "$activeThreadDrawerData", activeThreadDrawerData).turns);
				for (let idx = 0, $$length = each_array.length; idx < $$length; idx++) {
					let turn = each_array[idx];
					$$renderer.push(`<div class="turn-block svelte-1q68yr"><div class="turn-header svelte-1q68yr"><span class="turn-num svelte-1q68yr">Turn #${escape_html(idx + 1)}</span> `);
					if (turn.was_audio_input) $$renderer.push(`<!--[0--><span class="audio-badge svelte-1q68yr">🎙️ Voice Input</span>`);
					else $$renderer.push("<!--[-1-->");
					$$renderer.push(`<!--]--> <span class="turn-time svelte-1q68yr">${escape_html(turn.timestamp_iso || "")}</span></div> <div class="prompt-box svelte-1q68yr"><div class="speaker svelte-1q68yr">User</div> <div class="text svelte-1q68yr">${escape_html(turn.prompt_text)}</div></div> `);
					if (getGeminiResponseHtml(turn)) $$renderer.push(`<!--[0--><div class="response-box svelte-1q68yr"><div class="speaker svelte-1q68yr">Gemini</div> <div class="text svelte-1q68yr">${html(getGeminiResponseHtml(turn))}</div></div>`);
					else $$renderer.push("<!--[-1-->");
					$$renderer.push(`<!--]--></div>`);
				}
				$$renderer.push(`<!--]-->`);
			} else $$renderer.push(`<!--[-1--><div class="empty-state svelte-1q68yr">No conversation turns found for this thread.</div>`);
			$$renderer.push(`<!--]--></div></aside>`);
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]-->`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
//#region src/lib/components/CorrelationModal.svelte
function CorrelationModal($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		let sliderVal = 38;
		if (store_get($$store_subs ??= {}, "$isCorrelationModalOpen", isCorrelationModalOpen)) {
			$$renderer.push(`<!--[0--><div class="modal-backdrop svelte-7y3gvf"><div class="modal-box svelte-7y3gvf" id="correlationModal" style="display: flex;"><div class="modal-header svelte-7y3gvf"><h3 class="svelte-7y3gvf">📊 Similarity Spectrum &amp; Correlation Histogram</h3> <button class="close-btn svelte-7y3gvf">✕</button></div> <div class="modal-body svelte-7y3gvf"><div class="slider-row svelte-7y3gvf"><label for="corrSlider">Cutoff Threshold:</label> <input type="range" id="corrSlider" min="15" max="95" step="5"${attr("value", sliderVal)} class="svelte-7y3gvf"/> <span id="corrSliderValDisplay" class="slider-val svelte-7y3gvf">${escape_html(sliderVal)}%</span></div> `);
			$$renderer.push(`<!--[-1--><div class="loading svelte-7y3gvf">Loading similarity spectrum data...</div>`);
			$$renderer.push(`<!--]--></div></div></div>`);
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]-->`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
//#region src/lib/components/MindmapTree.svelte
function MindmapTree($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		$$renderer.push(`<div class="mindmap-container svelte-1wfmwou">`);
		$$renderer.push(`<!--[-1--><div class="loading svelte-1wfmwou">Loading mindmap taxonomy tree...</div>`);
		$$renderer.push(`<!--]--></div>`);
	});
}
//#endregion
//#region src/lib/components/DomainMatrix.svelte
function DomainMatrix($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		$$renderer.push(`<div class="matrix-container svelte-kzajtv">`);
		$$renderer.push(`<!--[-1--><div class="loading svelte-kzajtv">Loading domain similarity matrix...</div>`);
		$$renderer.push(`<!--]--></div>`);
	});
}
//#endregion
//#region src/routes/+page.svelte
function _page($$renderer, $$props) {
	$$renderer.component(($$renderer) => {
		var $$store_subs;
		$$renderer.push(`<div class="app-layout svelte-1uha8ag">`);
		Header($$renderer, {});
		$$renderer.push(`<!----> `);
		if (store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "d3_constellation") {
			$$renderer.push("<!--[0-->");
			FilterBar($$renderer, {});
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--> <main class="main-viewport svelte-1uha8ag">`);
		if (store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "d3_constellation") {
			$$renderer.push("<!--[0-->");
			D3Constellation($$renderer, {});
		} else if (store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "mindmap") {
			$$renderer.push("<!--[1-->");
			MindmapTree($$renderer, {});
		} else if (store_get($$store_subs ??= {}, "$activeSubtab", activeSubtab) === "matrix") {
			$$renderer.push("<!--[2-->");
			DomainMatrix($$renderer, {});
		} else $$renderer.push("<!--[-1-->");
		$$renderer.push(`<!--]--></main> `);
		SubgraphDrawer($$renderer, {});
		$$renderer.push(`<!----> `);
		ThreadDrawer($$renderer, {});
		$$renderer.push(`<!----> `);
		CorrelationModal($$renderer, {});
		$$renderer.push(`<!----></div>`);
		if ($$store_subs) unsubscribe_stores($$store_subs);
	});
}
//#endregion
export { _page as default };
