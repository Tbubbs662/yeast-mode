// Dashboard "Brewing activity": batches per month for the last 12 months.
// Data comes from the page as JSON (json_script); colors come from the theme.
(function () {
    const canvas = document.getElementById('activity-chart');
    const source = document.getElementById('activity-data');
    if (!canvas || !source || typeof Chart === 'undefined') return;

    const data = JSON.parse(source.textContent);
    const css = getComputedStyle(document.documentElement);
    const token = function (name) { return css.getPropertyValue(name).trim(); };

    Chart.defaults.font.family = getComputedStyle(document.body).fontFamily;

    new Chart(canvas, {
        type: 'bar',
        data: {
            labels: data.labels,
            datasets: [{
                label: 'Batches',
                data: data.counts,
                backgroundColor: token('--ym-accent'),
                hoverBackgroundColor: token('--ym-accent-hover'),
                maxBarThickness: 24,
                borderRadius: 4,
                borderSkipped: 'start',   // rounded top, square on the baseline
                minBarLength: 0,
            }],
        },
        options: {
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false }, // hover anywhere in a month's column
            plugins: {
                legend: { display: false },   // one series; the card title names it
                tooltip: {
                    backgroundColor: token('--ym-surface-2'),
                    borderColor: token('--ym-border'),
                    borderWidth: 1,
                    titleColor: token('--ym-text'),
                    bodyColor: token('--ym-text'),
                    padding: 10,
                    displayColors: false,
                    callbacks: {
                        title: function (items) { return data.titles[items[0].dataIndex]; },
                        label: function (item) {
                            const n = item.parsed.y;
                            return n + (n === 1 ? ' batch' : ' batches');
                        },
                    },
                },
            },
            scales: {
                x: {
                    grid: { display: false },
                    border: { color: token('--ym-border') },
                    ticks: { color: token('--ym-muted'), maxRotation: 0, autoSkip: true },
                },
                y: {
                    beginAtZero: true,
                    border: { display: false },
                    grid: { color: token('--ym-border') },
                    ticks: { color: token('--ym-muted'), precision: 0, maxTicksLimit: 5 },
                },
            },
        },
    });
})();
