<template>
  <div class="ticker-card">
    <div class="ticker-row">
      <span class="ticker-sym">{{ ticker.ticker }}</span>
      <span class="conf">{{ Math.round((ticker.confidence || 0) * 100) }}%</span>
    </div>
    <div class="ticker-name">{{ ticker.name }}</div>
    <div class="thesis">{{ ticker.thesis }}</div>
    <div class="risk" v-if="ticker.key_risk">⚠ {{ ticker.key_risk }}</div>
    <div class="support">{{ ticker.domain_support?.join(' · ') }}</div>
  </div>
</template>

<script setup>
defineProps({ ticker: Object })
</script>

<style scoped>
.ticker-card {
  background: #0d0d14; border: 1px solid #1e1e2e; border-radius: 8px;
  padding: 0.85rem; min-width: 200px; max-width: 260px;
}
.ticker-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.2rem; }
.ticker-sym { font-weight: 700; color: #a78bfa; font-size: 1rem; }
.conf { font-size: 0.75rem; color: #34d399; font-weight: 600; }
.ticker-name { font-size: 0.75rem; color: #6b6b80; margin-bottom: 0.5rem; }
.thesis { font-size: 0.8rem; color: #c8c8e0; line-height: 1.4; margin-bottom: 0.4rem; }
.risk { font-size: 0.75rem; color: #fbbf24; margin-bottom: 0.3rem; }
.support { font-size: 0.7rem; color: #5555688; }
</style>
