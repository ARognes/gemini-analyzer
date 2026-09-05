import { n as onDestroy } from "../../chunks/index-server.js";
import { S as escape_html, T as writable, c as stringify, i as ensure_array_like, l as unsubscribe_stores, n as attr_style, s as store_get, t as attr_class, x as attr } from "../../chunks/server.js";
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
var hideOneOffChats = writable(true);
var hideAppCommands = writable(true);
var selectedActionabilityTier = writable("");
var minTurnsFilter = writable(1);
var maxTurnsFilter = writable(50);
var correlationThresholdPct = writable(38);
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
		$$renderer.push(`<div class="filter-bar svelte-m9tjun"><div class="filter-group svelte-m9tjun"><span class="group-label svelte-m9tjun">Actionability:</span> <button${attr_class("pill-btn svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) === "" })}>All Tiers</button> <button${attr_class("pill-btn tier-project svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) === "large_project" })}>🚀 Large Projects</button> <button${attr_class("pill-btn tier-standard svelte-m9tjun", void 0, { "active": store_get($$store_subs ??= {}, "$selectedActionabilityTier", selectedActionabilityTier) === "standard" })}>💬 Standard Threads</button></div> <div class="filter-group svelte-m9tjun"><span class="group-label svelte-m9tjun">Pre-Filters:</span> <button id="btnToggleOneOffs"${attr_class("toggle-pill svelte-m9tjun", void 0, { "active": !store_get($$store_subs ??= {}, "$hideOneOffChats", hideOneOffChats) })}>⚡ One-Off Chats: <span class="state svelte-m9tjun">`);
		if (store_get($$store_subs ??= {}, "$hideOneOffChats", hideOneOffChats)) $$renderer.push(`<!--[0-->HIDDEN`);
		else $$renderer.push(`<!--[-1-->SHOWING`);
		$$renderer.push(`<!--]--></span></button> <button id="btnToggleAppCmds"${attr_class("toggle-pill svelte-m9tjun", void 0, { "active": !store_get($$store_subs ??= {}, "$hideAppCommands", hideAppCommands) })}>📱 App Commands: <span class="state svelte-m9tjun">`);
		if (store_get($$store_subs ??= {}, "$hideAppCommands", hideAppCommands)) $$renderer.push(`<!--[0-->HIDDEN`);
		else $$renderer.push(`<!--[-1-->SHOWING`);
		$$renderer.push(`<!--]--></span></button></div> <div class="filter-group slider-group svelte-m9tjun"><span class="group-label svelte-m9tjun">Turns (${escape_html(store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter))} - ${escape_html(store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter))}):</span> <input type="range" id="minTurnsSlider" min="1" max="50"${attr("value", store_get($$store_subs ??= {}, "$minTurnsFilter", minTurnsFilter))} class="svelte-m9tjun"/> <input type="range" id="maxTurnsSlider" min="1" max="50"${attr("value", store_get($$store_subs ??= {}, "$maxTurnsFilter", maxTurnsFilter))} class="svelte-m9tjun"/></div> <div class="filter-group svelte-m9tjun"><button class="corr-btn svelte-m9tjun">📊 Similarity Cutoff: <span class="val svelte-m9tjun">${escape_html(store_get($$store_subs ??= {}, "$correlationThresholdPct", correlationThresholdPct))}%</span></button></div></div>`);
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
					if (turn.response_plain) $$renderer.push(`<!--[0--><div class="response-box svelte-1q68yr"><div class="speaker svelte-1q68yr">Gemini</div> <div class="text svelte-1q68yr">${escape_html(turn.response_plain)}</div></div>`);
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
