<script>
  import { isThreadDrawerOpen, activeThreadDrawerData } from '../stores.js';

  let activeStreamId = $state(null);

  function closeDrawer() {
    isThreadDrawerOpen.set(false);
  }

  function scrollToTurn(turnNumber) {
    const el = document.getElementById(`turn-block-${turnNumber}`);
    if (el) {
      el.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }
  }

  function getGeminiResponseHtml(turn) {
    if (!turn) return '';
    let html = turn.response_html || turn.response_plain || turn.response_text || '';
    if (!html) return '';
    
    // Strip raw JSON tool metadata blobs if present
    html = html.replace(/\{"contentMetadata":[\s\S]*?\}/g, '').trim();
    return html;
  }
</script>

{#if $isThreadDrawerOpen && $activeThreadDrawerData}
  <div class="drawer-overlay" role="button" tabindex="0" onclick={closeDrawer} onkeydown={(e) => e.key === 'Escape' && closeDrawer()}></div>
  <aside class="thread-drawer" id="sideDrawer">
    <div class="drawer-header">
      <div class="header-title">
        <span>💬 Thread Inspector</span>
      </div>
      <button class="close-btn" onclick={closeDrawer}>✕</button>
    </div>

    <div class="thread-meta">
      <h3>{$activeThreadDrawerData.title || $activeThreadDrawerData.title_snippet}</h3>
      <div class="tags-row">
        {#if $activeThreadDrawerData.macro_domain}
          <span class="badge" style="background: rgba(56, 189, 248, 0.15); border-color: rgba(56, 189, 248, 0.4); color: #38bdf8;">
            {$activeThreadDrawerData.macro_domain_icon || '📂'} {$activeThreadDrawerData.macro_domain_label || $activeThreadDrawerData.macro_domain}
          </span>
        {/if}
        <span class="badge">{$activeThreadDrawerData.actionability_tier || 'standard'}</span>
        {#if $activeThreadDrawerData.connectedness !== undefined}
          <span class="badge" style="background: rgba(56, 189, 248, 0.15); border: 1px solid rgba(56, 189, 248, 0.4); color: #38bdf8;">
            ⚡ {$activeThreadDrawerData.connectedness}% ({$activeThreadDrawerData.connectedness_badge || 'Connected'})
          </span>
        {/if}
        {#if $activeThreadDrawerData.degree !== undefined && $activeThreadDrawerData.degree > 0}
          <span class="badge" style="background: rgba(168, 85, 247, 0.15); border: 1px solid rgba(168, 85, 247, 0.4); color: #c084fc;">
            🔗 {$activeThreadDrawerData.degree} Edges
          </span>
        {/if}
        <span class="meta-item">Turns: {$activeThreadDrawerData.turn_count || $activeThreadDrawerData.turns?.length || 1}</span>
      </div>
    </div>

    <!-- Executive Narrative & Conversation Harvesting Summary -->
    {#if $activeThreadDrawerData.executive_narrative}
      <div class="narrative-card">
        <div class="narrative-header">
          <span class="narrative-icon">🌾</span>
          <span class="narrative-title">Harvested Narrative Overview</span>
        </div>
        <p class="narrative-body">{$activeThreadDrawerData.executive_narrative}</p>
        {#if $activeThreadDrawerData.key_insights && $activeThreadDrawerData.key_insights.length > 0}
          <div class="narrative-insights">
            {#each $activeThreadDrawerData.key_insights as insight}
              <div class="insight-bullet">⚡ {insight}</div>
            {/each}
          </div>
        {/if}
      </div>
    {/if}

    <!-- Conversation Stream Sub-Division (Chapters) for Multi-Stream Threads -->
    {#if $activeThreadDrawerData.streams && $activeThreadDrawerData.streams.length > 1}
      <div class="streams-container">
        <div class="streams-header">
          <span>📚 Conversation Streams ({$activeThreadDrawerData.streams.length} Chapters)</span>
        </div>
        <div class="stream-pills">
          {#each $activeThreadDrawerData.streams as stream}
            <button 
              class="stream-pill"
              class:active={activeStreamId === stream.stream_id}
              onclick={() => {
                activeStreamId = stream.stream_id;
                scrollToTurn(stream.turn_range[0]);
              }}
            >
              <span class="pill-id">Ch. {stream.stream_id}</span>
              <span class="pill-range">Turns {stream.turn_range[0]}–{stream.turn_range[1]}</span>
              <span class="pill-title">{stream.title}</span>
            </button>
          {/each}
        </div>
      </div>
    {/if}

    <div class="drawer-content">
      {#if $activeThreadDrawerData.turns && $activeThreadDrawerData.turns.length > 0}
        {#each $activeThreadDrawerData.turns as turn, idx}
          <div class="turn-block" id="turn-block-{idx + 1}">
            <div class="turn-header">
              <span class="turn-num">Turn #{idx + 1}</span>
              {#if turn.was_audio_input}
                <span class="audio-badge">🎙️ Voice Input</span>
              {/if}
              <span class="turn-time">{turn.timestamp_iso || ''}</span>
            </div>

            <div class="prompt-box">
              <div class="speaker">User</div>
              <div class="text">{turn.prompt_text}</div>
            </div>

            {#if getGeminiResponseHtml(turn)}
              <div class="response-box">
                <div class="speaker">Gemini</div>
                <div class="text">
                  {@html getGeminiResponseHtml(turn)}
                </div>
              </div>
            {/if}
          </div>
        {/each}
      {:else}
        <div class="empty-state">No conversation turns found for this thread.</div>
      {/if}
    </div>
  </aside>
{/if}

<style>
  .drawer-overlay {
    position: fixed;
    inset: 0;
    background: rgba(0, 0, 0, 0.4);
    z-index: 1050;
  }

  .thread-drawer {
    position: fixed;
    top: 0;
    right: 0;
    width: 520px;
    height: 100vh;
    background: rgba(15, 23, 42, 0.95);
    backdrop-filter: blur(20px);
    border-left: 1px solid rgba(59, 130, 246, 0.3);
    z-index: 1100;
    display: flex;
    flex-direction: column;
    box-shadow: -10px 0 30px rgba(0, 0, 0, 0.6);
  }

  .drawer-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 1.25rem;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  }

  .header-title {
    font-weight: 700;
    color: #60a5fa;
    font-size: 1.05rem;
  }

  .close-btn {
    background: none;
    border: none;
    color: #94a3b8;
    font-size: 1.1rem;
    cursor: pointer;
  }

  .thread-meta {
    padding: 1rem 1.25rem;
    background: rgba(30, 41, 59, 0.5);
    border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  }

  .thread-meta h3 {
    margin: 0 0 0.5rem 0;
    font-size: 1rem;
    color: #f8fafc;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
    text-overflow: ellipsis;
    word-break: break-word;
    line-height: 1.35;
  }

  .tags-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #94a3b8;
  }

  .badge {
    background: rgba(59, 130, 246, 0.2);
    color: #60a5fa;
    border: 1px solid rgba(59, 130, 246, 0.3);
    padding: 0.15rem 0.4rem;
    border-radius: 4px;
  }

  .badge.tag {
    background: rgba(16, 185, 129, 0.2);
    color: #34d399;
    border-color: rgba(16, 185, 129, 0.3);
  }

  .narrative-card {
    margin: 0.75rem 1.25rem 0.25rem 1.25rem;
    background: linear-gradient(135deg, rgba(30, 58, 138, 0.25), rgba(15, 23, 42, 0.6));
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 10px;
    padding: 0.75rem 0.9rem;
  }

  .narrative-header {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-size: 0.78rem;
    font-weight: 700;
    color: #38bdf8;
    margin-bottom: 0.35rem;
  }

  .narrative-body {
    margin: 0 0 0.4rem 0;
    font-size: 0.8rem;
    line-height: 1.4;
    color: #e2e8f0;
  }

  .narrative-insights {
    display: flex;
    flex-direction: column;
    gap: 0.2rem;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    padding-top: 0.35rem;
  }

  .insight-bullet {
    font-size: 0.72rem;
    color: #94a3b8;
  }

  .streams-container {
    margin: 0.5rem 1.25rem 0 1.25rem;
    background: rgba(15, 23, 42, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 0.6rem 0.8rem;
  }

  .streams-header {
    font-size: 0.75rem;
    font-weight: 700;
    color: #fbbf24;
    margin-bottom: 0.45rem;
  }

  .stream-pills {
    display: flex;
    flex-direction: column;
    gap: 0.35rem;
    max-height: 140px;
    overflow-y: auto;
  }

  .stream-pill {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: rgba(30, 41, 59, 0.6);
    border: 1px solid rgba(255, 255, 255, 0.08);
    color: #cbd5e1;
    padding: 0.3rem 0.55rem;
    border-radius: 6px;
    font-size: 0.72rem;
    cursor: pointer;
    text-align: left;
    transition: all 0.15s ease;
  }

  .stream-pill:hover {
    background: rgba(56, 189, 248, 0.15);
    border-color: rgba(56, 189, 248, 0.4);
    color: #ffffff;
  }

  .stream-pill.active {
    background: rgba(245, 158, 11, 0.15);
    border-color: rgba(245, 158, 11, 0.5);
    color: #fbbf24;
    font-weight: 600;
  }

  .pill-id {
    font-weight: 700;
    color: #38bdf8;
  }

  .pill-range {
    color: #94a3b8;
    font-size: 0.68rem;
  }

  .pill-title {
    margin-left: auto;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
    max-width: 230px;
  }

  .drawer-content {
    flex: 1;
    overflow-y: auto;
    padding: 1.25rem;
    display: flex;
    flex-direction: column;
    gap: 1.25rem;
  }

  .turn-block {
    background: rgba(30, 41, 59, 0.5);
    border: 1px solid rgba(255, 255, 255, 0.06);
    border-radius: 10px;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .turn-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    font-size: 0.75rem;
    color: #64748b;
  }

  .turn-num {
    font-weight: 700;
    color: #cbd5e1;
  }

  .audio-badge {
    background: rgba(236, 72, 153, 0.2);
    color: #f472b6;
    padding: 0.1rem 0.35rem;
    border-radius: 4px;
  }

  .turn-time {
    margin-left: auto;
  }

  .prompt-box, .response-box {
    padding: 0.6rem 0.8rem;
    border-radius: 6px;
    font-size: 0.83rem;
  }

  .prompt-box {
    background: rgba(59, 130, 246, 0.1);
    border-left: 3px solid #3b82f6;
  }

  .response-box {
    background: rgba(30, 41, 59, 0.8);
    border-left: 3px solid #10b981;
  }

  .speaker {
    font-size: 0.7rem;
    font-weight: 700;
    text-transform: uppercase;
    margin-bottom: 0.2rem;
    color: #94a3b8;
  }

  .text {
    color: #e2e8f0;
    line-height: 1.45;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .response-box .text :global(p) {
    margin: 0 0 0.5rem 0;
  }

  .response-box .text :global(p:last-child) {
    margin-bottom: 0;
  }

  .response-box .text :global(strong) {
    color: #93c5fd;
  }

  .response-box .text :global(a) {
    color: #60a5fa;
    text-decoration: underline;
  }

  .response-box .text :global(code) {
    background: rgba(0, 0, 0, 0.4);
    padding: 0.15rem 0.35rem;
    border-radius: 4px;
    font-family: monospace;
    font-size: 0.8rem;
  }

  .empty-state {
    text-align: center;
    color: #64748b;
    margin-top: 3rem;
  }
</style>
