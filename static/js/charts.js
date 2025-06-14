
// charts.js - Fonctions pour créer et gérer les graphiques de l'application

// Palette de couleurs principale
const chartColors = [
    '#0d6efd', // primary
    '#198754', // success 
    '#0dcaf0', // info
    '#ffc107', // warning
    '#dc3545', // danger
    '#6c757d', // secondary
    '#5a23c8', // indigo
    '#fd7e14', // orange
    '#20c997', // teal
    '#d63384', // pink
];

// Palette étendue pour les grands ensembles de données
function generateExtendedColors(count) {
    if (count <= chartColors.length) {
        return chartColors.slice(0, count);
    }
    
    const colors = [...chartColors];
    
    // Créer des variantes plus claires et plus foncées
    for (let i = 0; i < chartColors.length && colors.length < count; i++) {
        // Version plus claire (en augmentant la luminosité)
        colors.push(lightenColor(chartColors[i], 20));
        
        // Version plus foncée (en diminuant la luminosité)
        if (colors.length < count) {
            colors.push(darkenColor(chartColors[i], 20));
        }
    }
    
    // Si on a encore besoin de plus de couleurs, on génère aléatoirement
    while (colors.length < count) {
        colors.push(getRandomColor());
    }
    
    return colors;
}

// Éclaircir une couleur
function lightenColor(color, percent) {
    const num = parseInt(color.replace('#', ''), 16);
    const amt = Math.round(2.55 * percent);
    const R = (num >> 16) + amt;
    const G = (num >> 8 & 0x00FF) + amt;
    const B = (num & 0x0000FF) + amt;
    
    return '#' + (
        0x1000000 + 
        (R < 255 ? (R < 1 ? 0 : R) : 255) * 0x10000 + 
        (G < 255 ? (G < 1 ? 0 : G) : 255) * 0x100 + 
        (B < 255 ? (B < 1 ? 0 : B) : 255)
    ).toString(16).slice(1);
}

// Assombrir une couleur
function darkenColor(color, percent) {
    return lightenColor(color, -percent);
}

// Générer une couleur aléatoire
function getRandomColor() {
    return '#' + Math.floor(Math.random() * 16777215).toString(16).padStart(6, '0');
}

// Configuration globale pour Chart.js
function setGlobalChartOptions() {
    Chart.defaults.font.family = "'Roboto', 'Helvetica Neue', 'Arial', sans-serif";
    Chart.defaults.font.size = 12;
    Chart.defaults.color = '#6c757d';
    Chart.defaults.plugins.legend.position = 'top';
    Chart.defaults.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.7)';
    Chart.defaults.plugins.tooltip.titleFont = { weight: 'bold' };
    Chart.defaults.plugins.tooltip.bodySpacing = 4;
    Chart.defaults.plugins.tooltip.padding = 12;
    Chart.defaults.plugins.tooltip.cornerRadius = 4;
    Chart.defaults.responsive = true;
    Chart.defaults.maintainAspectRatio = false;
}

// ------- FONCTIONS DE CRÉATION DE GRAPHIQUES -------

// Créer un graphique en camembert
function createPieChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    const colors = generateExtendedColors(data.labels.length);
    
    const defaultOptions = {
        plugins: {
            legend: {
                position: 'right',
                labels: {
                    boxWidth: 12,
                    padding: 15
                }
            },
            tooltip: {
                callbacks: {
                    label: function(context) {
                        const label = context.label || '';
                        const value = context.raw || 0;
                        const total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        const percentage = Math.round((value / total) * 100);
                        return `${label}: ${value} (${percentage}%)`;
                    }
                }
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'pie',
        data: {
            labels: data.labels,
            datasets: [{
                data: data.values,
                backgroundColor: colors,
                borderWidth: 1,
                borderColor: '#fff'
            }]
        },
        options: mergedOptions
    });
}

// Créer un graphique en beignet (donut)
function createDoughnutChart(elementId, data, options = {}) {
    const defaultOptions = {
        cutout: '60%',
        circumference: 360,
        plugins: {
            legend: {
                position: 'right'
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    const chart = createPieChart(elementId, data, mergedOptions);
    chart.config.type = 'doughnut';
    
    return chart;
}

// Créer un graphique en barres
function createBarChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    const colors = generateExtendedColors(data.datasets.length);
    
    // Appliquer les couleurs aux datasets
    data.datasets.forEach((dataset, index) => {
        dataset.backgroundColor = dataset.backgroundColor || colors[index % colors.length];
    });
    
    const defaultOptions = {
        plugins: {
            legend: {
                display: data.datasets.length > 1
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    borderDash: [2, 4]
                }
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'bar',
        data: data,
        options: mergedOptions
    });
}

// Créer un graphique en ligne
function createLineChart(elementId, data, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    const colors = generateExtendedColors(data.datasets.length);
    
    // Appliquer les couleurs aux datasets
    data.datasets.forEach((dataset, index) => {
        dataset.borderColor = dataset.borderColor || colors[index % colors.length];
        dataset.backgroundColor = dataset.backgroundColor || lightenColor(colors[index % colors.length], 40);
        dataset.tension = dataset.tension || 0.1; // Légère courbe
    });
    
    const defaultOptions = {
        plugins: {
            legend: {
                display: data.datasets.length > 1
            }
        },
        scales: {
            x: {
                grid: {
                    display: false
                }
            },
            y: {
                beginAtZero: true,
                grid: {
                    borderDash: [2, 4]
                }
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    return new Chart(ctx, {
        type: 'line',
        data: data,
        options: mergedOptions
    });
}

// ------- GESTIONNAIRES D'ÉVÉNEMENTS ET FONCTIONS UTILITAIRES -------

// Recalculer les dimensions des graphiques lors du redimensionnement
window.resizeCharts = function() {
    if (window.chartInstances && window.chartInstances.length) {
        window.chartInstances.forEach(chart => {
            if (chart) {
                chart.resize();
            }
        });
    }
};

// Exporter un graphique en image
function exportChartAsImage(chart, filename = 'chart.png') {
    const link = document.createElement('a');
    link.href = chart.toBase64Image();
    link.download = filename;
    link.click();
}

// Formatter les étiquettes des axes avec des unités monétaires
function formatCurrencyAxisLabels(value) {
    if (value >= 1000000) {
        return (value / 1000000).toFixed(1) + ' M';
    } else if (value >= 1000) {
        return (value / 1000).toFixed(0) + ' k';
    }
    return value;
}

// Initialiser tous les graphiques sur la page
function initDashboardCharts() {
    // Stocker les instances pour pouvoir les mettre à jour
    window.chartInstances = [];
    setGlobalChartOptions();
    
    // Les fonctions spécifiques pour chaque page seront définies dans leur propre script
    // Exemple : initCategoriesChart(), initValuesChart(), etc.
}

// ------- FONCTIONS SPÉCIFIQUES POUR LE TABLEAU DE BORD -------

// Initialiser le graphique de répartition par catégorie
function initCategoriesChart(elementId, data) {
    return createPieChart(elementId, {
        labels: data.labels,
        values: data.values
    }, {
        plugins: {
            title: {
                display: true,
                text: 'Répartition des biens par catégorie'
            }
        }
    });
}

// Initialiser le graphique de répartition par entité
function initEntitesChart(elementId, data) {
    return createDoughnutChart(elementId, {
        labels: data.labels,
        values: data.values
    }, {
        plugins: {
            title: {
                display: true,
                text: 'Répartition des biens par entité'
            }
        }
    });
}

// Initialiser le graphique de répartition géographique
function initCommunesChart(elementId, data) {
    return createDoughnutChart(elementId, {
        labels: data.labels,
        values: data.values
    }, {
        plugins: {
            title: {
                display: true,
                text: 'Répartition géographique des biens'
            }
        }
    });
}

// Initialiser le graphique d'évolution des valeurs
function initValuesHistoryChart(elementId, data) {
    return createLineChart(elementId, {
        labels: data.dates,
        datasets: [{
            label: 'Valeur totale',
            data: data.values,
            fill: true,
            borderWidth: 2,
            pointRadius: 4,
            pointHoverRadius: 6
        }]
    }, {
        plugins: {
            title: {
                display: true,
                text: 'Évolution de la valeur patrimoniale'
            }
        },
        scales: {
            y: {
                ticks: {
                    callback: function(value) {
                        return formatCurrencyAxisLabels(value) + ' FCFA';
                    }
                }
            }
        }
    });
}

// Initialiser le graphique de comparaison des acquisitions par année
function initAcquisitionsChart(elementId, data) {
    return createBarChart(elementId, {
        labels: data.years,
        datasets: [{
            label: 'Nombre d\'acquisitions',
            data: data.counts,
            barPercentage: 0.6,
            categoryPercentage: 0.7
        }]
    }, {
        plugins: {
            title: {
                display: true,
                text: 'Acquisitions par année'
            }
        }
    });
}

// Initialiser le graphique de comparaison des valeurs par province
function initProvincesChart(elementId, data) {
    const colors = generateExtendedColors(data.labels.length);
    
    return createBarChart(elementId, {
        labels: data.labels,
        datasets: [{
            label: 'Valeur totale',
            data: data.values,
            backgroundColor: colors,
            borderWidth: 0
        }]
    }, {
        indexAxis: 'y', // Barres horizontales
        plugins: {
            title: {
                display: true,
                text: 'Valeur patrimoniale par province'
            }
        },
        scales: {
            x: {
                ticks: {
                    callback: function(value) {
                        return formatCurrencyAxisLabels(value) + ' FCFA';
                    }
                }
            }
        }
    });
}

// Initialiser un graphique de jauge pour les indicateurs
function createGaugeChart(elementId, value, maxValue, title, options = {}) {
    const ctx = document.getElementById(elementId).getContext('2d');
    
    // Calculer le pourcentage et déterminer la couleur
    const percentage = (value / maxValue) * 100;
    let color = '#4CAF50'; // Vert par défaut
    
    if (percentage < 25) {
        color = '#FF5722'; // Rouge/orange pour les valeurs basses
    } else if (percentage < 50) {
        color = '#FF9800'; // Orange pour les valeurs moyennes
    } else if (percentage < 75) {
        color = '#8BC34A'; // Vert clair pour les bonnes valeurs
    }
    
    const defaultOptions = {
        circumference: 180,
        rotation: 270,
        cutout: '70%',
        plugins: {
            legend: {
                display: false
            },
            tooltip: {
                displayColors: false,
                callbacks: {
                    label: function(context) {
                        return `${value} / ${maxValue} (${percentage.toFixed(1)}%)`;
                    }
                }
            }
        }
    };
    
    const mergedOptions = { ...defaultOptions, ...options };
    
    const chart = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: ['Valeur', 'Reste'],
            datasets: [{
                data: [value, maxValue - value],
                backgroundColor: [color, '#E0E0E0'],
                borderWidth: 0
            }]
        },
        options: mergedOptions
    });
    
    // Ajouter le texte au centre de la jauge
    if (document.getElementById(`${elementId}-text`)) {
        document.getElementById(`${elementId}-text`).innerHTML = `
            <div class="text-center">
                <h4 class="mb-0">${value}</h4>
                <p class="text-muted mb-0">${title}</p>
            </div>
        `;
    }
    
    return chart;
}

// ------- EXPORT DES DONNÉES ET GRAPHIQUES -------

// Exporter les données d'un graphique en CSV
function exportChartDataToCSV(chart, filename = 'chart-data.csv') {
    const labels = chart.data.labels;
    const datasets = chart.data.datasets;
    
    let csvContent = 'data:text/csv;charset=utf-8,';
    
    // En-têtes
    let headers = ['Label'];
    datasets.forEach(dataset => {
        headers.push(dataset.label || 'Série');
    });
    
    csvContent += headers.join(',') + '\r\n';
    
    // Données
    labels.forEach((label, i) => {
        let row = [label];
        datasets.forEach(dataset => {
            row.push(dataset.data[i]);
        });
        csvContent += row.join(',') + '\r\n';
    });
    
    // Créer un lien de téléchargement
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Imprimer tous les graphiques
function printCharts() {
    window.print();
}

// ------- INITIALISATION DES GRAPHIQUES -------

// Initialiser tous les graphiques sur une page
document.addEventListener('DOMContentLoaded', function() {
    // Vérifier si on est sur une page qui contient des graphiques
    if (document.querySelector('[data-chart-type]')) {
        setGlobalChartOptions();
        window.chartInstances = [];
        
        // Parcourir tous les conteneurs de graphiques
        document.querySelectorAll('[data-chart-type]').forEach(container => {
            const chartType = container.dataset.chartType;
            const chartId = container.id;
            const dataSource = container.dataset.source;
            let chartData;
            
            // Récupérer les données soit depuis un attribut data, soit depuis une variable globale
            if (dataSource && window[dataSource]) {
                chartData = window[dataSource];
            } else if (container.dataset.labels && container.dataset.values) {
                chartData = {
                    labels: JSON.parse(container.dataset.labels),
                    values: JSON.parse(container.dataset.values)
                };
            }
            
            if (chartData) {
                let chart;
                
                // Créer le graphique selon le type
                switch (chartType) {
                    case 'pie':
                        chart = createPieChart(chartId, chartData, JSON.parse(container.dataset.options || '{}'));
                        break;
                    case 'doughnut':
                        chart = createDoughnutChart(chartId, chartData, JSON.parse(container.dataset.options || '{}'));
                        break;
                    case 'bar':
                        chart = createBarChart(chartId, chartData, JSON.parse(container.dataset.options || '{}'));
                        break;
                    case 'line':
                        chart = createLineChart(chartId, chartData, JSON.parse(container.dataset.options || '{}'));
                        break;
                    case 'gauge':
                        chart = createGaugeChart(
                            chartId, 
                            parseFloat(container.dataset.value), 
                            parseFloat(container.dataset.maxValue), 
                            container.dataset.title || '',
                            JSON.parse(container.dataset.options || '{}')
                        );
                        break;
                }
                
                if (chart) {
                    window.chartInstances.push(chart);
                }
            }
        });
        
        // Ajouter les gestionnaires d'événements pour les boutons d'export
        document.querySelectorAll('[data-chart-export]').forEach(button => {
            button.addEventListener('click', function() {
                const chartId = this.dataset.target;
                const exportType = this.dataset.chartExport;
                const chart = window.chartInstances.find(
                    chart => chart.canvas.id === chartId
                );
                
                if (chart) {
                    if (exportType === 'image') {
                        exportChartAsImage(chart, `${chartId}.png`);
                    } else if (exportType === 'csv') {
                        exportChartDataToCSV(chart, `${chartId}.csv`);
                    } else if (exportType === 'print') {
                        printCharts();
                    }
                }
            });
        });
    }
});

// Fonction pour mettre à jour un graphique avec de nouvelles données
function updateChart(chartId, newData, animationDuration = 500) {
    const chart = window.chartInstances.find(chart => chart.canvas.id === chartId);
    
    if (chart) {
        if (newData.labels) {
            chart.data.labels = newData.labels;
        }
        
        if (newData.datasets) {
            chart.data.datasets = newData.datasets;
        } else if (newData.values) {
            chart.data.datasets[0].data = newData.values;
        }
        
        chart.update({
            duration: animationDuration,
            easing: 'easeOutQuad'
        });
    }
}