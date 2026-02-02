<script>
  import '../app.css';
  import Sidebar from '$lib/components/Sidebar.svelte';
  import Header from '$lib/components/Header.svelte';
  import MobileNav from '$lib/components/MobileNav.svelte';
  import { onMount } from 'svelte';

  let { children } = $props();
  let loaded = $state(false);

  onMount(() => {
    // Initialiser le theme depuis localStorage ou preferer le dark
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    }
    loaded = true;
  });
</script>

<div class="min-h-screen bg-slate-50 dark:bg-dark-900 text-slate-900 dark:text-slate-100 transition-colors duration-300">
  <!-- Background effects -->
  <div class="fixed inset-0 pointer-events-none">
    <div class="absolute top-0 left-1/4 w-96 h-96 bg-amber-500/10 dark:bg-amber-500/5 rounded-full blur-3xl transition-opacity"></div>
    <div class="absolute bottom-0 right-1/4 w-96 h-96 bg-blue-500/10 dark:bg-blue-500/5 rounded-full blur-3xl transition-opacity"></div>
  </div>

  <!-- Sidebar -->
  <Sidebar />
  
  <!-- Mobile nav -->
  <MobileNav />
  
  <!-- Main content -->
  <div class="flex flex-col lg:pl-64 min-h-screen relative">
    <Header />
    <main class="flex-1 p-4 lg:p-8 pb-24 lg:pb-8 {loaded ? 'animate-in' : 'opacity-0'}">
      {@render children()}
    </main>
  </div>
</div>
