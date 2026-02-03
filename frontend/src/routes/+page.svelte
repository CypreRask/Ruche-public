<script>
    import { onMount } from 'svelte';
    import { hiveData, initWebSocket, getConnectionLabel, getConnectionColor } from '$lib/stores/hive.svelte.js';
    import MetricCard from '$lib/components/MetricCard.svelte';
    import VideoFeed from '$lib/components/VideoFeed.svelte';
    import { Thermometer, Droplets, Scale, Sun, Activity } from 'lucide-svelte';
    import { formatSensorValue } from '$lib/utils/formatters.js';

    onMount(() => {
        initWebSocket();
    });

    function getTimeSinceUpdate(date) {
        const seconds = Math.floor((new Date() - date) / 1000);
        if (seconds < 10) return 'a l\'instant';
        if (seconds < 60) return `${seconds}s`;
        if (seconds < 3600) return `${Math.floor(seconds / 60)}min`;
        return `${Math.floor(seconds / 3600)}h`;
    }
</script>

<div class="space-y-6 max-w-7xl mx-auto">
    <!-- Welcome section -->
    <div class="flex flex-col lg:flex-row lg:items-center justify-between gap-4 slide-in">
        <div>
            <h2 class="text-3xl lg:text-4xl font-bold text-slate-800 dark:text-slate-100">
                Vue d'<span class="text-gradient">ensemble</span>
            </h2>
            <p class="text-slate-500 dark:text-slate-400 mt-1 flex items-center gap-2">
                <Activity size={16} class="text-amber-400" />
                {#if hiveData.connectionStatus === 'connected'}
                    <span class="text-slate-700 dark:text-slate-300">Derniere mise a jour <span class="text-amber-500 font-medium">{getTimeSinceUpdate(hiveData.lastUpdate)}</span></span>
                {:else if hiveData.connectionStatus === 'connecting'}
                    <span class="text-amber-500">Connexion au serveur...</span>
                {:else}
                    <span class="text-rose-500">Hors ligne - tentative de reconnexion</span>
                {/if}
            </p>
        </div>
        
        <!-- Quick status cards -->
        <div class="flex gap-3">
            <div class="glass-card px-4 py-2 flex items-center gap-3">
                <div class="relative">
                    <div class="w-2.5 h-2.5 rounded-full {getConnectionColor(hiveData.connectionStatus)}"></div>
                    <div class="absolute inset-0 w-2.5 h-2.5 rounded-full {getConnectionColor(hiveData.connectionStatus)} animate-ping"></div>
                </div>
                <div>
                    <p class="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400">Statut</p>
                    <p class="text-sm font-medium text-slate-800 dark:text-slate-200">{getConnectionLabel(hiveData.connectionStatus)}</p>
                </div>
            </div>
            
            <div class="glass-card px-4 py-2 flex items-center gap-3">
                <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-amber-100 to-amber-50 dark:from-amber-400/20 dark:to-amber-600/10 flex items-center justify-center border border-amber-200 dark:border-amber-500/20">
                    <span class="text-lg">🐝</span>
                </div>
                <div>
                    <p class="text-[10px] uppercase tracking-wider text-slate-500 dark:text-slate-400">Detections</p>
                    <p class="text-sm font-medium text-slate-800 dark:text-slate-200">{hiveData.detections.bees + hiveData.detections.hornets} insects</p>
                </div>
            </div>
        </div>
    </div>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
            title="Temperature"
            value={formatSensorValue(hiveData.temperature, 'temperature')}
            unit="°C"
            icon={Thermometer}
            color="rose"
            isStale={hiveData.connectionStatus !== 'connected' || hiveData.temperature === 0}
        />
        <MetricCard
            title="Humidite"
            value={formatSensorValue(hiveData.humidity, 'humidity')}
            unit="%"
            icon={Droplets}
            color="blue"
            isStale={hiveData.connectionStatus !== 'connected' || hiveData.humidity === 0}
        />
        <MetricCard
            title="Poids"
            value={formatSensorValue(hiveData.weight, 'weight')}
            unit="kg"
            icon={Scale}
            color="amber"
            isStale={hiveData.connectionStatus !== 'connected'}
        />
        <MetricCard
            title="Luminosite"
            value={formatSensorValue(hiveData.luminosity, 'luminosity')}
            unit="Lux"
            icon={Sun}
            color="green"
            isStale={hiveData.connectionStatus !== 'connected'}
        />
    </div>

    <!-- Video & AI Detection -->
    <VideoFeed />

    <!-- Screenshots -->
    <section class="space-y-3">
        <div class="flex flex-wrap items-center justify-between gap-2">
            <h3 class="text-lg font-semibold text-slate-800 dark:text-slate-100">Apercus</h3>
            <p class="text-xs uppercase tracking-wider text-slate-500 dark:text-slate-400">Images du dossier screenshots</p>
        </div>
        <div class="grid gap-4 md:grid-cols-2">
            <figure class="glass-card overflow-hidden">
                <img
                    src="/screenshots/dashboard.png"
                    alt="Apercu du dashboard SmartHive"
                    class="h-64 w-full object-cover"
                    loading="lazy"
                />
                <figcaption class="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">Dashboard</figcaption>
            </figure>
            <figure class="glass-card overflow-hidden">
                <img
                    src="/screenshots/ruche.jpeg"
                    alt="Apercu de la ruche connectee"
                    class="h-64 w-full object-cover"
                    loading="lazy"
                />
                <figcaption class="px-4 py-3 text-sm text-slate-600 dark:text-slate-300">Ruche connectee</figcaption>
            </figure>
        </div>
    </section>
</div>
