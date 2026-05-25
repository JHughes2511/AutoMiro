<template>
  <div class="dashboard">
    <div class="header">
      <h1>Research Projects</h1>
      <p class="subtitle">Your autonomous research think tank</p>
    </div>

    <div v-if="loading" class="loading">Loading projects...</div>

    <div v-else-if="projects.length === 0" class="empty">
      <div class="empty-icon">⬡</div>
      <p>No research projects yet.</p>
      <router-link to="/project/new" class="start-btn">Start your first brief</router-link>
    </div>

    <div v-else class="project-grid">
      <ProjectCard
        v-for="p in projects"
        :key="p.project_id"
        :project="p"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { projects as api } from '../api/index.js'
import ProjectCard from '../components/ProjectCard.vue'

const projects = ref([])
const loading = ref(true)

onMounted(async () => {
  try {
    const res = await api.list()
    projects.value = res.data
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.dashboard { }
.header { margin-bottom: 2rem; }
h1 { font-size: 2rem; font-weight: 700; color: #e8e8f0; }
.subtitle { color: #6b6b80; margin-top: 0.4rem; }

.loading { color: #6b6b80; text-align: center; padding: 4rem; }

.empty { text-align: center; padding: 6rem 2rem; color: #6b6b80; }
.empty-icon { font-size: 3rem; margin-bottom: 1rem; opacity: 0.3; }
.empty p { margin-bottom: 1.5rem; font-size: 1.1rem; }
.start-btn {
  padding: 0.7rem 1.5rem; background: #7c3aed; color: #fff;
  border-radius: 8px; text-decoration: none; font-weight: 600;
}

.project-grid {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
  gap: 1.5rem;
}
</style>
