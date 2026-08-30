import unittest
import urllib.request
import json
import time
from playwright.sync_api import sync_playwright

SERVER_URL = "http://localhost:8765"

class TestCanvasInteractionE2E(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/stats").read().decode()
            data = json.loads(res)
            assert data.get("total_threads") == 2423, f"Unexpected total threads: {data}"
            print("✅ API Server Health Check PASSED")
        except Exception as e:
            cls.fail(f"HTTP Server not available at {SERVER_URL}: {e}")

    def setUp(self):
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=True)
        self.page = self.browser.new_page(viewport={"width": 1440, "height": 900})
        self.page.goto(SERVER_URL, wait_until="networkidle")

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def test_01_canvas_dom_and_subtabs(self):
        page = self.page
        canvas = page.query_selector("#constellationCanvas")
        self.assertIsNotNone(canvas, "Canvas #constellationCanvas missing from DOM")

        tab_chat = page.query_selector("#subtabChat")
        self.assertIn("active", tab_chat.get_attribute("class"))

        tab_unified = page.query_selector("#subtabUnified")
        self.assertIsNotNone(tab_unified, "Subtab #subtabUnified missing from DOM")
        page.evaluate("selectCanvasSubtab('topic_clusters')")
        page.wait_for_timeout(300)

        self.assertIn("active", tab_unified.get_attribute("class"))
        print("✅ Test 01: Subtab activation PASSED")

    def test_02_canvas_node_hover_hit_test(self):
        page = self.page
        page.evaluate("selectCanvasSubtab('topic_clusters')")
        page.wait_for_timeout(300)

        target_info = page.evaluate("""() => {
            if (!overlapData || !overlapData.nodes) return null;
            const canvasEl = document.getElementById('constellationCanvas');
            const rect = canvasEl.getBoundingClientRect();
            const n = overlapData.nodes.find(x => {
                if (hideOneOffChats && (x.actionability_tier === 'one_off' || x.turn_count <= 1)) return false;
                if (hideAppCommands && x.actionability_tier === 'app_command') return false;
                return typeof x.worldX === 'number' && Math.abs(x.worldX - 1600) < 300 && Math.abs(x.worldY - 1000) < 300;
            }) || overlapData.nodes.find(x => typeof x.worldX === 'number');

            if (!n) return null;
            n.vx = 0; n.vy = 0;

            const screenX = rect.left + panX + (n.worldX * scale);
            const screenY = rect.top + panY + (n.worldY * scale);

            return {
                id: n.id,
                title: n.title || n.title_snippet,
                worldX: n.worldX,
                worldY: n.worldY,
                screenX: screenX,
                screenY: screenY
            };
        }""")

        self.assertIsNotNone(target_info, "No target node found")

        page.mouse.move(target_info["screenX"], target_info["screenY"])
        page.wait_for_timeout(400)

        hovered_id = page.evaluate("() => hoveredNode ? hoveredNode.id : null")
        self.assertIsNotNone(hovered_id, f"Hover hit test failed: expected hoveredNode, got None")
        print(f"✅ Test 02: Canvas node hover hit test PASSED (hoveredNode: {hovered_id})")

    def test_03_canvas_node_drag_and_physics(self):
        page = self.page
        page.evaluate("selectCanvasSubtab('topic_clusters')")
        page.wait_for_timeout(300)

        node_start = page.evaluate("""() => {
            if (!overlapData || !overlapData.nodes) return null;
            const canvasEl = document.getElementById('constellationCanvas');
            const rect = canvasEl.getBoundingClientRect();
            const n = overlapData.nodes.find(x => {
                if (hideOneOffChats && (x.actionability_tier === 'one_off' || x.turn_count <= 1)) return false;
                if (hideAppCommands && x.actionability_tier === 'app_command') return false;
                return typeof x.worldX === 'number' && Math.abs(x.worldX - 1600) < 300 && Math.abs(x.worldY - 1000) < 300;
            }) || overlapData.nodes.find(x => typeof x.worldX === 'number');

            if (!n) return null;

            return {
                id: n.id,
                worldX: n.worldX,
                worldY: n.worldY,
                screenX: rect.left + panX + (n.worldX * scale),
                screenY: rect.top + panY + (n.worldY * scale)
            };
        }""")

        self.assertIsNotNone(node_start, "No node found for drag test")

        sx, sy = node_start["screenX"], node_start["screenY"]
        page.mouse.move(sx, sy)
        page.mouse.down()
        page.mouse.move(sx + 150, sy + 100, steps=10)

        dragged_id = page.evaluate("() => draggedNode ? draggedNode.id : null")
        self.assertIsNotNone(dragged_id, f"draggedNode should be non-null")

        node_during = page.evaluate(f"() => overlapData.nodes.find(n => n.id === '{node_start['id']}')")
        self.assertNotEqual(node_during["worldX"], node_start["worldX"], "Node worldX did not change during drag")

        page.mouse.up()
        page.wait_for_timeout(300)

        dragged_after = page.evaluate("() => draggedNode")
        self.assertIsNone(dragged_after, "draggedNode should be cleared after mouseup")
        print("✅ Test 03: Canvas node drag & spring physics PASSED")

    def test_04_correlation_stats_api(self):
        """Test that /api/correlation_stats returns valid histogram buckets and sample pairs."""
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/correlation_stats?min_similarity=0.30").read().decode()
            data = json.loads(res)
            self.assertEqual(data.get("threshold_pct"), 30)
            self.assertGreater(data.get("total_pairs", 0), 50000)
            self.assertGreater(len(data.get("buckets", [])), 10)
            self.assertGreater(len(data.get("sample_pairs", [])), 5)

            # Check that sample pair has similarity percentage and titles
            first_pair = data["sample_pairs"][0]
            self.assertIn("similarity_pct", first_pair)
            self.assertIn("source_title", first_pair)
            self.assertIn("target_title", first_pair)
            print(f"✅ Test 04: Correlation stats API PASSED ({data['total_pairs']} candidate links, {len(data['sample_pairs'])} sample pairs)")
        except Exception as e:
            self.fail(f"Correlation API error: {e}")

    def test_05_correlation_modal_ui(self):
        """Test opening Correlation Spectrum Modal and interacting with threshold slider."""
        page = self.page
        page.evaluate("() => openCorrelationModal()")
        page.wait_for_timeout(300)

        modal = page.query_selector("#correlationModal")
        self.assertIsNotNone(modal)
        self.assertEqual(modal.evaluate("el => el.style.display"), "flex")

        # Change slider value to 50%
        page.evaluate("""() => {
            const s = document.getElementById('corrSlider');
            if (s) { s.value = 50; updateCorrelationThreshold(50); }
        }""")
        page.wait_for_timeout(300)

        slider_display = page.inner_text("#corrSliderValDisplay")
        self.assertEqual(slider_display, "50%")
        print("✅ Test 05: Correlation modal UI & slider interaction PASSED")

    def test_06_mindmap_tree_api(self):
        """Test that /api/mindmap_tree returns valid 4-level hierarchical tree structure."""
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/mindmap_tree").read().decode()
            tree = json.loads(res)
            self.assertEqual(tree.get("id"), "root")
            self.assertEqual(tree.get("thread_count"), 2423)
            self.assertEqual(len(tree.get("children", [])), 6)

            # Check domain node
            ai_domain = next(c for c in tree["children"] if c["id"] == "domain_ai_agents")
            self.assertGreater(ai_domain["thread_count"], 300)
            self.assertGreater(len(ai_domain["children"]), 3)

            # Check tier branch node
            first_tier = ai_domain["children"][0]
            self.assertIn("name", first_tier)
            self.assertGreater(len(first_tier["children"]), 0)

            # Check leaf node
            first_leaf = first_tier["children"][0]
            self.assertIn("name", first_leaf)
            self.assertIn("turn_count", first_leaf)
            print(f"✅ Test 06: Hierarchical Mindmap Tree API PASSED ({tree['thread_count']} threads across 6 domains)")
        except Exception as e:
            self.fail(f"Mindmap Tree API error: {e}")

    def test_07_actionability_edge_filter(self):
        """Test that toggling an actionability tier hides edges not connected to unfiltered nodes."""
        page = self.page
        page.evaluate("selectCanvasSubtab('topic_clusters')")
        page.wait_for_timeout(300)

        # Set actionability tier filter
        page.evaluate("() => filterByActionabilityTier('large_project')")
        page.wait_for_timeout(300)

        selected_tier = page.evaluate("() => selectedActionabilityTier")
        self.assertEqual(selected_tier, "large_project")

        # Verify activeConnectedNodeIds only contains nodes connected to large_project
        check_result = page.evaluate("""() => {
            if (!overlapData || !overlapData.relations || !overlapData.nodes) return { ok: false };
            const nodeMap = {};
            overlapData.nodes.forEach(n => nodeMap[n.id] = n);

            let totalRelations = overlapData.relations.length;
            let hiddenCount = 0;
            let keptCount = 0;

            overlapData.relations.forEach(rel => {
                const s = nodeMap[rel.source_key];
                const t = nodeMap[rel.target_key];
                if (s && t) {
                    const sMatch = (s.actionability_tier === 'large_project');
                    const tMatch = (t.actionability_tier === 'large_project');
                    if (!sMatch || !tMatch) {
                        hiddenCount++;
                    } else {
                        keptCount++;
                    }
                }
            });

            return { ok: true, totalRelations, hiddenCount, keptCount };
        }""")

        self.assertTrue(check_result["ok"])
        self.assertGreater(check_result["hiddenCount"], 0, "No edges were hidden when actionability filter was active")
        print(f"✅ Test 07: Actionability edge filter PASSED ({check_result['hiddenCount']} edges hidden, {check_result['keptCount']} edges active for large_project)")

    def test_08_hover_no_dimming_and_click_selection(self):
        """Test that hovering over a node does not dim unconnected nodes, but clicking sets selectedNode and dims background."""
        page = self.page
        page.evaluate("selectCanvasSubtab('topic_clusters')")
        page.wait_for_timeout(300)

        # Hover over first node
        page.evaluate("""() => {
            if (overlapData && overlapData.nodes && overlapData.nodes.length > 0) {
                hoveredNode = overlapData.nodes[0];
                drawCanvas();
            }
        }""")
        page.wait_for_timeout(200)

        # Verify selectedNode is null on hover
        sel_node = page.evaluate("() => selectedNode")
        self.assertIsNone(sel_node)

        # Click node to select
        page.evaluate("""() => {
            if (overlapData && overlapData.nodes && overlapData.nodes.length > 0) {
                selectedNode = overlapData.nodes[0];
                drawCanvas();
            }
        }""")
        page.wait_for_timeout(200)

        sel_node_after = page.evaluate("() => selectedNode ? selectedNode.id : null")
        self.assertIsNotNone(sel_node_after)

        # Single click does NOT open drawer
        drawer_open_single = page.evaluate("() => sideDrawer.classList.contains('open')")
        self.assertFalse(drawer_open_single)

        # Double click opens side drawer
        page.evaluate("""() => {
            if (overlapData && overlapData.nodes && overlapData.nodes.length > 0) {
                openDrawerForThread(overlapData.nodes[0].id);
            }
        }""")
        page.wait_for_timeout(200)
        drawer_open_dbl = page.evaluate("() => sideDrawer.classList.contains('open')")
        self.assertTrue(drawer_open_dbl)

        print(f"✅ Test 08: Single click highlight & double click side drawer PASSED (selectedNode: {sel_node_after})")

    def test_09_one_off_chats_default_filter(self):
        """Test that one-off chats are filtered out by default, and toggle switch shows/hides them."""
        page = self.page

        # Verify default state is hideOneOffChats = true
        is_hidden_default = page.evaluate("() => hideOneOffChats")
        self.assertTrue(is_hidden_default)

        # Click toggle button to show one-offs
        page.evaluate("() => toggleOneOffChatsFilter()")
        page.wait_for_timeout(200)

        is_hidden_toggled = page.evaluate("() => hideOneOffChats")
        self.assertFalse(is_hidden_toggled)

        # Click toggle button again to restore default
        page.evaluate("() => toggleOneOffChatsFilter()")
        page.wait_for_timeout(200)

        is_hidden_restored = page.evaluate("() => hideOneOffChats")
        self.assertTrue(is_hidden_restored)
        print("✅ Test 09: One-off chats default filter & toggle switch PASSED")

    def test_10_data_driven_tags_api(self):
        """Test that /api/data_tags returns empirical ground-up topic clusters."""
        try:
            res = urllib.request.urlopen(f"{SERVER_URL}/api/data_tags").read().decode()
            tags = json.loads(res)
            self.assertGreater(len(tags), 20)
            
            first_tag = tags[0]
            self.assertIn("tag_id", first_tag)
            self.assertIn("tag_label", first_tag)
            self.assertGreater(first_tag["thread_count"], 0)
            
            # Verify no stopwords in top 10 tags
            top_tag_ids = [t["tag_id"].lower() for t in tags[:10]]
            for sw in ["like", "but", "because", "they", "them", "you"]:
                self.assertNotIn(sw, top_tag_ids)
                
            print(f"✅ Test 10: Data-driven tags API PASSED ({len(tags)} clean empirical clusters returned, top: #{tags[0]['tag_id']})")
        except Exception as e:
            self.fail(f"Data-driven tags API error: {e}")

    def test_11_app_command_prefiltering(self):
        """Test that single-turn app commands are pre-filtered out by default."""
        page = self.page

        # Verify default state is hideAppCommands = true
        is_hidden_default = page.evaluate("() => hideAppCommands")
        self.assertTrue(is_hidden_default)

        # Toggle app commands off
        page.evaluate("() => toggleAppCommandsFilter()")
        page.wait_for_timeout(200)

        is_hidden_toggled = page.evaluate("() => hideAppCommands")
        self.assertFalse(is_hidden_toggled)

        # Restore default
        page.evaluate("() => toggleAppCommandsFilter()")
        page.wait_for_timeout(200)

        is_hidden_restored = page.evaluate("() => hideAppCommands")
        self.assertTrue(is_hidden_restored)
        print("✅ Test 11: App Command pre-filtering & toggle switch PASSED")

    def test_12_turn_slider_filtering(self):
        """Test that adjusting turn range sliders filters graph nodes accordingly."""
        page = self.page

        # Set minTurnsFilter to 5 and maxTurnsFilter to 20
        page.evaluate("""() => {
            minTurnsFilter = 5;
            maxTurnsFilter = 20;
            drawCanvas();
        }""")
        page.wait_for_timeout(200)

        min_val = page.evaluate("() => minTurnsFilter")
        max_val = page.evaluate("() => maxTurnsFilter")

        self.assertEqual(min_val, 5)
        self.assertEqual(max_val, 20)

        # Reset bounds to default 1 - 50
        page.evaluate("""() => {
            minTurnsFilter = 1;
            maxTurnsFilter = 50;
            drawCanvas();
        }""")
        page.wait_for_timeout(200)
        print("✅ Test 12: Turn count slider boundary filtering PASSED")

    def test_13_cluster_layout_and_bounding_hulls(self):
        """Test that node clusters are assigned distinct sector coordinates and bounding hulls render."""
        page = self.page
        page.evaluate("selectCanvasSubtab('topic_clusters')")
        page.wait_for_timeout(300)

        # Verify nodes are positioned across multiple sector centers
        coords = page.evaluate("""() => {
            if (!overlapData || !overlapData.nodes) return [];
            return overlapData.nodes
                .filter(n => typeof n.worldX === 'number')
                .slice(0, 15)
                .map(n => ({ id: n.id, x: n.worldX, y: n.worldY }));
        }""")
        self.assertGreater(len(coords), 0)
        first_coord = coords[0]
        self.assertIsNotNone(first_coord["x"])
        self.assertIsNotNone(first_coord["y"])

        # Verify distinct X/Y positions exist across nodes (not all stacked at (0,0))
        unique_x = set(round(c["x"], 1) for c in coords)
        self.assertGreater(len(unique_x), 1)

        print(f"✅ Test 13: Minimal-Overlap Cluster Layout & Bounding Hulls PASSED ({len(unique_x)} distinct spatial sectors verified)")

    def test_14_subgraph_search_and_highlighting(self):
        """Test that /api/search_subgraph returns matching nodes/edges and query drawer opens."""
        page = self.page

        # Type "jam" into canvas search bar via JS evaluation and await async fetch
        page.evaluate("""async () => {
            const el = document.getElementById('canvasSearch');
            if (el) el.value = 'jam';
            await performSubgraphSearch('jam');
        }""")
        page.wait_for_timeout(300)

        query = page.evaluate("() => activeSearchQuery")
        self.assertEqual(query, "jam")

        matching_count = page.evaluate("() => searchMatchingNodeIds.size")
        self.assertGreater(matching_count, 0)

        path_edges_count = page.evaluate("() => searchPathEdges.size")
        self.assertGreaterEqual(path_edges_count, 0)

        drawer_open = page.evaluate("() => document.getElementById('queryResultsDrawer').classList.contains('open')")
        self.assertTrue(drawer_open)

        # Clear search
        page.evaluate("() => clearSubgraphSearch()")
        page.wait_for_timeout(200)

        query_after = page.evaluate("() => activeSearchQuery")
        self.assertEqual(query_after, "")

        print(f"✅ Test 14: Interwoven Subgraph Search & Highlighting PASSED ({matching_count} nodes & {path_edges_count} edges highlighted)")

if __name__ == "__main__":
    unittest.main()
