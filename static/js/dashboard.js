/* Dashboard Charts & Filter Controller */

let charts = {};

document.addEventListener('DOMContentLoaded', () => {
  loadFilterOptions();
  loadDashboardData();

  document.getElementById('btn-apply-filters').addEventListener('click', () => {
    loadDashboardData();
  });

  document.getElementById('btn-reset-filters').addEventListener('click', () => {
    document.getElementById('filter-start-date').value = '';
    document.getElementById('filter-end-date').value = '';
    document.getElementById('filter-category').value = 'All';
    document.getElementById('filter-region').value = 'All';
    loadDashboardData();
  });
});

async function loadFilterOptions() {
  try {
    const res = await fetchAPI('/api/filters');
    if (res.success) {
      const catSelect = document.getElementById('filter-category');
      res.filters.categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        catSelect.appendChild(opt);
      });

      const regSelect = document.getElementById('filter-region');
      res.filters.regions.forEach(reg => {
        const opt = document.createElement('option');
        opt.value = reg;
        opt.textContent = reg;
        regSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error('Failed to load filter options', err);
  }
}

async function loadDashboardData() {
  const startDate = document.getElementById('filter-start-date').value;
  const endDate = document.getElementById('filter-end-date').value;
  const category = document.getElementById('filter-category').value;
  const region = document.getElementById('filter-region').value;

  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (category && category !== 'All') params.append('category', category);
  if (region && region !== 'All') params.append('region', region);

  try {
    const data = await fetchAPI(`/api/dashboard?${params.toString()}`);
    if (data.success) {
      updateKPIs(data.kpis);
      renderMonthlyTrendChart(data.charts.monthly_trend);
      renderCategorySalesChart(data.charts.category_sales);
      renderRegionSalesChart(data.charts.region_sales);
      renderTopProductsChart(data.charts.top_products);
      renderSegmentDistributionChart(data.charts.segment_distribution);
      renderRevenueDistributionChart(data.charts.revenue_distribution);
    }
  } catch (err) {
    console.error('Failed to load dashboard data', err);
  }
}

function updateKPIs(kpis) {
  document.getElementById('kpi-revenue').textContent = formatCurrency(kpis.total_revenue);
  document.getElementById('kpi-orders').textContent = formatNumber(kpis.total_orders);
  document.getElementById('kpi-customers').textContent = formatNumber(kpis.total_customers);
  document.getElementById('kpi-products').textContent = formatNumber(kpis.total_products);
  document.getElementById('kpi-aov').textContent = formatCurrency(kpis.avg_order_value);
}

function renderMonthlyTrendChart(data) {
  const ctx = document.getElementById('chart-monthly-trend').getContext('2d');
  if (charts.monthlyTrend) charts.monthlyTrend.destroy();

  const labels = data.map(d => d.label);
  const revenues = data.map(d => d.revenue);

  charts.monthlyTrend = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Monthly Revenue (₹)',
        data: revenues,
        borderColor: '#6366f1',
        backgroundColor: 'rgba(99, 102, 241, 0.15)',
        fill: true,
        tension: 0.35,
        borderWidth: 3,
        pointBackgroundColor: '#818cf8',
        pointRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (ctx) => `Revenue: ${formatCurrency(ctx.raw)}`
          }
        }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', callback: (v) => '₹' + (v/1000) + 'k' } }
      }
    }
  });
}

function renderCategorySalesChart(data) {
  const ctx = document.getElementById('chart-category-sales').getContext('2d');
  if (charts.categorySales) charts.categorySales.destroy();

  const labels = data.map(d => d.category);
  const revenues = data.map(d => d.revenue);
  const colors = ['#6366f1', '#10b981', '#f59e0b', '#ef4444', '#a855f7', '#06b6d4'];

  charts.categorySales = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: revenues,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#1e293b'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } },
        tooltip: { callbacks: { label: (ctx) => `Revenue: ${formatCurrency(ctx.raw)}` } }
      }
    }
  });
}

function renderRegionSalesChart(data) {
  const ctx = document.getElementById('chart-region-sales').getContext('2d');
  if (charts.regionSales) charts.regionSales.destroy();

  const labels = data.map(d => d.region);
  const revenues = data.map(d => d.revenue);

  charts.regionSales = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: revenues,
        backgroundColor: 'rgba(245, 158, 11, 0.8)',
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `Revenue: ${formatCurrency(ctx.raw)}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', callback: (v) => '₹' + (v/1000) + 'k' } }
      }
    }
  });
}

function renderTopProductsChart(data) {
  const ctx = document.getElementById('chart-top-products').getContext('2d');
  if (charts.topProducts) charts.topProducts.destroy();

  const labels = data.map(d => d.product_name.length > 22 ? d.product_name.substring(0, 22) + '...' : d.product_name);
  const revenues = data.map(d => d.revenue);

  charts.topProducts = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total Revenue (₹)',
        data: revenues,
        backgroundColor: 'rgba(6, 182, 212, 0.85)',
        borderRadius: 6
      }]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `Revenue: ${formatCurrency(ctx.raw)}` } }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', callback: (v) => '₹' + (v/1000) + 'k' } },
        y: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 11 } } }
      }
    }
  });
}

function renderSegmentDistributionChart(data) {
  const ctx = document.getElementById('chart-segment-distribution').getContext('2d');
  if (charts.segmentDistribution) charts.segmentDistribution.destroy();

  const labels = data.map(d => d.segment);
  const counts = data.map(d => d.count);
  const colors = data.map(d => d.color);

  charts.segmentDistribution = new Chart(ctx, {
    type: 'doughnut',
    data: {
      labels: labels,
      datasets: [{
        data: counts,
        backgroundColor: colors,
        borderWidth: 2,
        borderColor: '#1e293b'
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 11 } } },
        tooltip: { callbacks: { label: (ctx) => `Customers: ${formatNumber(ctx.raw)}` } }
      }
    }
  });
}

function renderRevenueDistributionChart(data) {
  const ctx = document.getElementById('chart-revenue-distribution').getContext('2d');
  if (charts.revenueDistribution) charts.revenueDistribution.destroy();

  const labels = data.map(d => d.segment);
  const revenues = data.map(d => d.revenue);
  const colors = data.map(d => d.color);

  charts.revenueDistribution = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Segment Total Revenue (₹)',
        data: revenues,
        backgroundColor: colors,
        borderRadius: 8
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `Revenue: ${formatCurrency(ctx.raw)}` } }
      },
      scales: {
        x: { grid: { display: false }, ticks: { color: '#94a3b8', font: { size: 10 } } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', callback: (v) => '₹' + (v/1000) + 'k' } }
      }
    }
  });
}
