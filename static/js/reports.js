/* Reports & Insights Controller */

document.addEventListener('DOMContentLoaded', () => {
  loadInsights();
});

async function loadInsights() {
  try {
    const res = await fetchAPI('/api/insights');
    if (res.success) {
      renderAnalyticalFindings(res.insights.findings);
      renderRecommendations(res.insights.recommendations);
      renderExecutiveSummary(res.insights.kpis, res.insights.rfm_summary);
    }
  } catch (err) {
    console.error('Failed to load insights', err);
  }
}

function renderAnalyticalFindings(findings) {
  const container = document.getElementById('findings-container');
  if (!findings || findings.length === 0) {
    container.innerHTML = `<div class="col-12"><div class="alert alert-dark">No analytical findings generated yet. Load dataset into Data Warehouse first.</div></div>`;
    return;
  }

  container.innerHTML = findings.map(f => `
    <div class="col-lg-6 col-xl-4">
      <div class="glass-card h-100">
        <div class="d-flex align-items-center justify-content-between mb-3">
          <div class="d-flex align-items-center gap-2">
            <i class="${f.icon} text-indigo-400 fs-5"></i>
            <span class="fw-bold fs-7 text-uppercase tracking-wider text-muted">${f.category}</span>
          </div>
          <span class="badge bg-indigo-500/20 text-indigo-300 border border-indigo-500/30">${f.badge}</span>
        </div>
        <h4 class="fw-bold fs-6 text-white mb-2">${f.title}</h4>
        <p class="text-secondary small mb-0 lh-relaxed" style="font-size: 0.85rem;">${f.detail}</p>
      </div>
    </div>
  `).join('');
}

function renderRecommendations(recommendations) {
  const tbody = document.querySelector('#table-recommendations tbody');
  if (!recommendations || recommendations.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="text-center text-muted py-3">No recommendations available.</td></tr>`;
    return;
  }

  tbody.innerHTML = recommendations.map(r => `
    <tr>
      <td class="fw-bold text-indigo-300">${r.target}</td>
      <td class="fw-semibold text-secondary">${r.action}</td>
      <td class="text-center">
        <span class="badge ${r.priority === 'Urgent' ? 'bg-danger' : r.priority === 'High' ? 'bg-warning text-dark' : 'bg-primary'} px-3">
          ${r.priority}
        </span>
      </td>
    </tr>
  `).join('');
}

function renderExecutiveSummary(kpis, rfmSummary) {
  const tbody = document.querySelector('#table-summary-report tbody');
  tbody.innerHTML = `
    <tr>
      <td class="fw-bold text-white">Total Gross Sales Revenue</td>
      <td class="fw-bold text-emerald-400">${formatCurrency(kpis.total_revenue)}</td>
      <td class="text-muted">Primary top-line financial metric recorded in FACT_SALES.</td>
    </tr>
    <tr>
      <td class="fw-bold text-white">Total Completed Orders</td>
      <td class="fw-bold text-white">${formatNumber(kpis.total_orders)}</td>
      <td class="text-muted">Count of unique order transactions in Data Warehouse.</td>
    </tr>
    <tr>
      <td class="fw-bold text-white">Average Order Value (AOV)</td>
      <td class="fw-bold text-indigo-300">${formatCurrency(kpis.avg_order_value)}</td>
      <td class="text-muted">Average monetary transaction size per order.</td>
    </tr>
    <tr>
      <td class="fw-bold text-white">Total Unique Customer Base</td>
      <td class="fw-bold text-white">${formatNumber(rfmSummary.total_customers)}</td>
      <td class="text-muted">Dimension count of distinct purchasing customers.</td>
    </tr>
    <tr>
      <td class="fw-bold text-white">Average Purchase Frequency</td>
      <td class="fw-bold text-info">${rfmSummary.avg_frequency} orders/customer</td>
      <td class="text-muted">RFM Frequency metric across customer base.</td>
    </tr>
    <tr>
      <td class="fw-bold text-white">Average Customer Recency</td>
      <td class="fw-bold text-warning">${rfmSummary.avg_recency} days</td>
      <td class="text-muted">RFM Recency metric indicating days since last purchase.</td>
    </tr>
  `;
}
