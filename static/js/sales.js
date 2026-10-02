/* Sales Analysis Controller */

let trendChart = null;
let currentSalesData = null;
let currentGranularity = 'monthly';

document.addEventListener('DOMContentLoaded', () => {
  loadSalesFilters();
  loadSalesData();

  document.getElementById('btn-sales-apply').addEventListener('click', () => {
    loadSalesData();
  });

  const trendTabBtns = document.querySelectorAll('#trend-tabs button');
  trendTabBtns.forEach(btn => {
    btn.addEventListener('click', (e) => {
      trendTabBtns.forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');
      currentGranularity = e.target.dataset.granularity;
      if (currentSalesData) {
        renderTrendChart(currentSalesData.trends[currentGranularity]);
      }
    });
  });
});

async function loadSalesFilters() {
  try {
    const res = await fetchAPI('/api/filters');
    if (res.success) {
      const catSelect = document.getElementById('sales-filter-category');
      res.filters.categories.forEach(cat => {
        const opt = document.createElement('option');
        opt.value = cat;
        opt.textContent = cat;
        catSelect.appendChild(opt);
      });

      const regSelect = document.getElementById('sales-filter-region');
      res.filters.regions.forEach(reg => {
        const opt = document.createElement('option');
        opt.value = reg;
        opt.textContent = reg;
        regSelect.appendChild(opt);
      });

      const prodSelect = document.getElementById('sales-filter-product');
      res.filters.products.forEach(p => {
        const opt = document.createElement('option');
        opt.value = p.product_id;
        opt.textContent = p.product_name;
        prodSelect.appendChild(opt);
      });
    }
  } catch (err) {
    console.error('Error loading sales filters', err);
  }
}

async function loadSalesData() {
  const startDate = document.getElementById('sales-filter-start').value;
  const endDate = document.getElementById('sales-filter-end').value;
  const category = document.getElementById('sales-filter-category').value;
  const region = document.getElementById('sales-filter-region').value;
  const productId = document.getElementById('sales-filter-product').value;

  const params = new URLSearchParams();
  if (startDate) params.append('start_date', startDate);
  if (endDate) params.append('end_date', endDate);
  if (category && category !== 'All') params.append('category', category);
  if (region && region !== 'All') params.append('region', region);
  if (productId && productId !== 'All') params.append('product_id', productId);

  try {
    const res = await fetchAPI(`/api/sales?${params.toString()}`);
    if (res.success) {
      currentSalesData = res.data;
      updateSalesKPIs(res.data.kpis);
      renderTrendChart(res.data.trends[currentGranularity]);
      renderTopRevenueProducts(res.data.top_products_revenue);
      renderTopQuantityProducts(res.data.top_products_quantity);
      renderCategoryTable(res.data.category_sales);
      renderRegionTable(res.data.region_sales);
    }
  } catch (err) {
    console.error('Failed to load sales data', err);
  }
}

function updateSalesKPIs(kpis) {
  document.getElementById('sales-kpi-revenue').textContent = formatCurrency(kpis.total_revenue);
  document.getElementById('sales-kpi-orders').textContent = formatNumber(kpis.total_orders);
  document.getElementById('sales-kpi-quantity').textContent = formatNumber(kpis.total_quantity);
  document.getElementById('sales-kpi-aov').textContent = formatCurrency(kpis.avg_order_value);
}

function renderTrendChart(trendData) {
  const ctx = document.getElementById('chart-sales-trend').getContext('2d');
  if (trendChart) trendChart.destroy();

  if (!trendData || trendData.length === 0) return;

  const labels = trendData.map(d => d.date || d.label || d.year);
  const revenues = trendData.map(d => d.revenue);

  trendChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'Revenue (₹)',
        data: revenues,
        borderColor: '#4f46e5',
        backgroundColor: 'rgba(79, 70, 229, 0.15)',
        fill: true,
        tension: 0.3,
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
        tooltip: { callbacks: { label: (ctx) => `Revenue: ${formatCurrency(ctx.raw)}` } }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', callback: (v) => '₹' + (v/1000) + 'k' } }
      }
    }
  });
}

function renderTopRevenueProducts(products) {
  const tbody = document.querySelector('#table-top-rev-products tbody');
  tbody.innerHTML = products.map((p, i) => `
    <tr>
      <td class="fw-bold text-muted">${i + 1}</td>
      <td class="fw-semibold">${p.product_name}</td>
      <td><span class="badge bg-dark border border-secondary">${p.category}</span></td>
      <td class="text-end fw-semibold">${formatNumber(p.quantity)}</td>
      <td class="text-end fw-bold text-emerald-400">${formatCurrency(p.revenue)}</td>
    </tr>
  `).join('');
}

function renderTopQuantityProducts(products) {
  const tbody = document.querySelector('#table-top-qty-products tbody');
  tbody.innerHTML = products.map((p, i) => `
    <tr>
      <td class="fw-bold text-muted">${i + 1}</td>
      <td class="fw-semibold">${p.product_name}</td>
      <td><span class="badge bg-dark border border-secondary">${p.category}</span></td>
      <td class="text-end fw-bold text-cyan-400">${formatNumber(p.quantity)}</td>
      <td class="text-end">${formatCurrency(p.revenue)}</td>
    </tr>
  `).join('');
}

function renderCategoryTable(categories) {
  const tbody = document.querySelector('#table-categories-perf tbody');
  tbody.innerHTML = categories.map(c => `
    <tr>
      <td class="fw-bold">${c.category}</td>
      <td class="text-end">${formatNumber(c.orders)}</td>
      <td class="text-end">${formatNumber(c.quantity)}</td>
      <td class="text-end fw-bold text-indigo-300">${formatCurrency(c.revenue)}</td>
    </tr>
  `).join('');
}

function renderRegionTable(regions) {
  const tbody = document.querySelector('#table-regions-perf tbody');
  tbody.innerHTML = regions.map(r => `
    <tr>
      <td class="fw-bold">${r.region}</td>
      <td class="text-end">${formatNumber(r.orders)}</td>
      <td class="text-end">${formatNumber(r.quantity)}</td>
      <td class="text-end fw-bold text-amber-400">${formatCurrency(r.revenue)}</td>
    </tr>
  `).join('');
}
