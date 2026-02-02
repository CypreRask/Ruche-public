<script>
    import { onMount, tick } from 'svelte';
    import { hiveData } from '$lib/stores/hive.svelte.js';
    import { BarChart3, TrendingUp, Calendar, Activity, Download, Trash2 } from 'lucide-svelte';
    import Chart from 'chart.js/auto';

    let canvas = $state(null);
    let chart = $state(null);
    let historyData = $state([]);
    let isLoading = $state(true);
    let stats = $state({
        tempAvg: 0,
        tempMin: 0,
        tempMax: 0,
        weightAvg: 0,
        totalRecords: 0,
        last24h: 0
    });

    onMount(async () => {
        await loadData();
    });

    async function loadData() {
        isLoading = true;
        try {
            const res = await fetch('http://localhost:2000/api/history');
            const data = await res.json();
            
            historyData = data;
            calculateStats(data);
            
            await tick();
            
            if (canvas && data.length > 0) {
                initChart(data);
            }
        } catch (e) {
            console.error("Failed to load data", e);
        }
        isLoading = false;
    }

    function calculateStats(data) {
        if (data.length === 0) return;
        
        const temps = data.map(d => parseFloat(d.temperature)).filter(v => !isNaN(v));
        const weights = data.map(d => parseFloat(d.mass)).filter(v => !isNaN(v));
        
        stats = {
            tempAvg: temps.length ? (temps.reduce((a, b) => a + b, 0) / temps.length).toFixed(1) : 0,
            tempMin: temps.length ? Math.min(...temps).toFixed(1) : 0,
            tempMax: temps.length ? Math.max(...temps).toFixed(1) : 0,
            weightAvg: weights.length ? (weights.reduce((a, b) => a + b, 0) / weights.length).toFixed(1) : 0,
            totalRecords: data.length,
            last24h: data.filter(d => {
                const recordTime = new Date(d.timestamp);
                const hoursAgo = (Date.now() - recordTime) / (1000 * 60 * 60);
                return hoursAgo <= 24;
            }).length
        };
    }

    function initChart(data) {
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        if (!ctx) return;
        
        if (chart) chart.destroy();

        const recentData = data.slice(-100);

        chart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: recentData.map(d => new Date(d.timestamp).toLocaleString([], { 
                    month: 'short', 
                    day: 'numeric', 
                    hour: '2-digit', 
                    minute: '2-digit' 
                })),
                datasets: [
                    {
                        label: 'Temperature (°C)',
                        data: recentData.map(d => parseFloat(d.temperature) || 0),
                        borderColor: '#F43F5E',
                        backgroundColor: 'rgba(244, 63, 94, 0.1)',
                        tension: 0.4,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        borderWidth: 2,
                        fill: true
                    },
                    {
                        label: 'Poids (kg)',
                        data: recentData.map(d => parseFloat(d.mass) || 0),
                        borderColor: '#F59E0B',
                        backgroundColor: 'rgba(245, 158, 11, 0.1)',
                        tension: 0.4,
                        yAxisID: 'y1',
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        borderWidth: 2,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        position: 'top',
                        align: 'end',
                        labels: {
                            usePointStyle: true,
                            boxWidth: 8,
                            font: { size: 11 }
                        }
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { maxTicksLimit: 8, font: { size: 10 } }
                    },
                    y: {
                        position: 'left',
                        grid: { color: 'rgba(148, 163, 184, 0.1)' },
                        ticks: { font: { size: 10 } },
                        title: { display: true, text: 'Temperature (°C)' }
                    },
                    y1: {
                        position: 'right',
                        grid: { display: false },
                        ticks: { font: { size: 10 } },
                        title: { display: true, text: 'Poids (kg)' }
                    }
                }
            }
        });
    }

    function exportCSV() {
        if (historyData.length === 0) return;
        
        const headers = ['timestamp', 'temperature', 'humidity', 'mass', 'luminosity', 'bee_count', 'hornet_count'];
        const csvContent = [
            headers.join(','),
            ...historyData.map(row => headers.map(h => row[h] ?? '').join(','))
        ].join('\n');
        
        const blob = new Blob([csvContent], { type: 'text/csv' });
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `smarthive_data_${new Date().toISOString().split('T')[0]}.csv`;
        a.click();
    }
</script>

<div class="space-y-6 max-w-7xl mx-auto">
    <!-- Header -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        <div>
            <h2 class="text-3xl font-bold text-slate-800 dark:text-white">
                Donnees & <span class="text-gradient">Analytics</span>
            </h2>
            <p class="text-slate-500 dark:text-slate-400 mt-1">
                Historique complet et statistiques de la ruche
            </p>
        </div>
        
        <div class="flex gap-3">
            <button 
                onclick={exportCSV}
                class="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-100 dark:bg-white/5 border border-slate-200 dark:border-white/10 text-slate-700 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-white/10 transition-all"
                disabled={historyData.length === 0}
            >
                <Download size={18} />
                <span class="hidden sm:inline">Exporter CSV</span>
            </button>
        </div>
    </div>

    <!-- Stats Grid -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="glass-card p-5">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-rose-100 dark:bg-rose-500/20 flex items-center justify-center">
                    <TrendingUp size={20} class="text-rose-600 dark:text-rose-400" />
                </div>
                <span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Temp. Moyenne</span>
            </div>
            <p class="text-2xl font-bold text-slate-800 dark:text-white">{stats.tempAvg}°C</p>
            <p class="text-xs text-slate-500 mt-1">Min: {stats.tempMin}°C / Max: {stats.tempMax}°C</p>
        </div>

        <div class="glass-card p-5">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-amber-100 dark:bg-amber-500/20 flex items-center justify-center">
                    <Activity size={20} class="text-amber-600 dark:text-amber-400" />
                </div>
                <span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Poids Moyen</span>
            </div>
            <p class="text-2xl font-bold text-slate-800 dark:text-white">{stats.weightAvg} kg</p>
            <p class="text-xs text-slate-500 mt-1">Masse de la ruche</p>
        </div>

        <div class="glass-card p-5">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-blue-100 dark:bg-blue-500/20 flex items-center justify-center">
                    <Calendar size={20} class="text-blue-600 dark:text-blue-400" />
                </div>
                <span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Total Enregistrements</span>
            </div>
            <p class="text-2xl font-bold text-slate-800 dark:text-white">{stats.totalRecords}</p>
            <p class="text-xs text-slate-500 mt-1">{stats.last24h} dans les 24h</p>
        </div>

        <div class="glass-card p-5">
            <div class="flex items-center gap-3 mb-3">
                <div class="w-10 h-10 rounded-xl bg-green-100 dark:bg-green-500/20 flex items-center justify-center">
                    <BarChart3 size={20} class="text-green-600 dark:text-green-400" />
                </div>
                <span class="text-xs font-medium uppercase tracking-wider text-slate-500 dark:text-slate-400">Detections Actuelles</span>
            </div>
            <p class="text-2xl font-bold text-slate-800 dark:text-white">
                {hiveData.detections.bees + hiveData.detections.hornets}
            </p>
            <p class="text-xs text-slate-500 mt-1">{hiveData.detections.bees} abeilles / {hiveData.detections.hornets} frelons</p>
        </div>
    </div>

    <!-- Main Chart -->
    <div class="glass-card overflow-hidden">
        <div class="p-5 border-b border-slate-200 dark:border-white/5">
            <h3 class="text-lg font-semibold text-slate-800 dark:text-white">Evolution Temporelle</h3>
            <p class="text-sm text-slate-500 dark:text-slate-400">Temperature et poids sur les 100 derniers enregistrements</p>
        </div>
        <div class="p-5">
            <div class="h-80 lg:h-96">
                {#if isLoading}
                    <div class="h-full flex items-center justify-center">
                        <div class="animate-spin w-8 h-8 border-2 border-amber-500 border-t-transparent rounded-full"></div>
                    </div>
                {:else if historyData.length > 0}
                    <canvas bind:this={canvas}></canvas>
                {:else}
                    <div class="h-full flex flex-col items-center justify-center text-slate-400 dark:text-slate-500">
                        <BarChart3 size={48} class="opacity-30 mb-4" />
                        <span>Aucune donnee disponible</span>
                    </div>
                {/if}
            </div>
        </div>
    </div>

    <!-- Recent Data Table -->
    <div class="glass-card overflow-hidden">
        <div class="p-5 border-b border-slate-200 dark:border-white/5">
            <h3 class="text-lg font-semibold text-slate-800 dark:text-white">Dernieres Mesures</h3>
        </div>
        <div class="overflow-x-auto">
            <table class="w-full text-sm">
                <thead class="bg-slate-50 dark:bg-white/5 text-slate-600 dark:text-slate-400">
                    <tr>
                        <th class="px-4 py-3 text-left font-medium">Date</th>
                        <th class="px-4 py-3 text-left font-medium">Temperature</th>
                        <th class="px-4 py-3 text-left font-medium">Humidite</th>
                        <th class="px-4 py-3 text-left font-medium">Poids</th>
                        <th class="px-4 py-3 text-left font-medium">Luminosite</th>
                        <th class="px-4 py-3 text-left font-medium">Abeilles</th>
                        <th class="px-4 py-3 text-left font-medium">Frelons</th>
                    </tr>
                </thead>
                <tbody class="divide-y divide-slate-200 dark:divide-white/5">
                    {#each historyData.slice(-10).reverse() as row}
                        <tr class="hover:bg-slate-50 dark:hover:bg-white/5 transition-colors">
                            <td class="px-4 py-3 text-slate-700 dark:text-slate-300">
                                {new Date(row.timestamp).toLocaleString()}
                            </td>
                            <td class="px-4 py-3">
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-rose-100 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400">
                                    {parseFloat(row.temperature).toFixed(1)}°C
                                </span>
                            </td>
                            <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{row.humidity}%</td>
                            <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{parseFloat(row.mass).toFixed(1)} kg</td>
                            <td class="px-4 py-3 text-slate-600 dark:text-slate-400">{row.luminosity}</td>
                            <td class="px-4 py-3">
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-amber-100 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400">
                                    {row.bee_count}
                                </span>
                            </td>
                            <td class="px-4 py-3">
                                <span class="inline-flex items-center px-2 py-1 rounded-full text-xs font-medium {parseInt(row.hornet_count) > 0 ? 'bg-rose-100 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400' : 'bg-slate-100 dark:bg-slate-700 text-slate-600 dark:text-slate-400'}">
                                    {row.hornet_count}
                                </span>
                            </td>
                        </tr>
                    {/each}
                </tbody>
            </table>
        </div>
    </div>
</div>
