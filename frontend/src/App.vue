<template>
  <div id="automiro">
    <nav class="topbar">
      <router-link to="/" class="logo">AutoMiro</router-link>
      <router-link to="/project/new" class="new-btn">+ New Research</router-link>
    </nav>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
#automiro { min-height: 100vh; display: flex; flex-direction: column; }

.topbar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 2rem; height: 56px;
  background: #0d0d14; border-bottom: 1px solid #1e1e2e;
  position: sticky; top: 0; z-index: 100;
}

.logo {
  font-size: 1.2rem; font-weight: 700; color: #a78bfa;
  text-decoration: none; letter-spacing: 0.04em;
}

.new-btn {
  padding: 0.4rem 1rem; background: #7c3aed; color: #fff;
  border-radius: 6px; text-decoration: none; font-size: 0.85rem;
  font-weight: 600; transition: background 0.15s;
}
.new-btn:hover { background: #6d28d9; }

main { flex: 1; padding: 2rem; max-width: 1200px; margin: 0 auto; width: 100%; }
</style>
