<script>
  import { isThreadDrawerOpen, activeThreadDrawerData } from '../stores.js';

  function closeDrawer() {
    isThreadDrawerOpen.set(false);
  }
</script>

{#if $isThreadDrawerOpen && $activeThreadDrawerData}
  <div class="drawer-overlay" onclick={closeDrawer}></div>
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
        <span class="badge">{$activeThreadDrawerData.actionability_tier || 'standard'}</span>
        {#if $activeThreadDrawerData.primary_tag}
          <span class="badge tag">#{$activeThreadDrawerData.primary_tag}</span>
        {/if}
        <span class="meta-item">Turns: {$activeThreadDrawerData.turn_count || 1}</span>
      </div>
    </div>

    <div class="drawer-content">
      {#if $activeThreadDrawerData.turns && $activeThreadDrawerData.turns.length > 0}
        {#each $activeThreadDrawerData.turns as turn, idx}
          <div class="turn-block">
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

            {#if turn.response_plain}
              <div class="response-box">
                <div class="speaker">Gemini</div>
                <div class="text">{turn.response_plain}</div>
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
  }

  .empty-state {
    text-align: center;
    color: #64748b;
    margin-top: 3rem;
  }
</style>
