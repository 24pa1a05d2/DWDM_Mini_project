/* K-Means Customer Segmentation Controller */

let elbowChart = null;
let scatterChart = null;
let currentSegmentationData = null;

document.addEventListener('DOMContentLoaded', () => {
  loadSegmentationData();

  document.getElementById('btn-recluster').addEventListener('click', () => {
    loadSegmentationData();
  });
});

async function loadSegmentationData() {
  const k = document.getElementById('select-k-clusters').value;

  try {
    const res = await fetchAPI(`/api/segmentation?clusters=${k}`);
    if (res.success) {
      currentSegmentationData = res.data;
      renderElbowChart(res.data.elbow_curve, parseInt(k));
      renderScatterChart(res.data.scatter_data);
      renderSegmentCards(res.data.cluster_summary);
    }
  } catch (err) {
    console.error('Failed to load segmentation data', err);
  }
}

function renderElbowChart(elbowData, currentK) {
  const ctx = document.getElementById('chart-elbow-curve').getContext('2d');
  if (elbowChart) elbowChart.destroy();

  const labels = elbowData.map(d => `K=${d.k}`);
  const wcssValues = elbowData.map(d => d.wcss);

  const pointColors = elbowData.map(d => d.k === currentK ? '#ef4444' : '#f59e0b');
  const pointRadii = elbowData.map(d => d.k === currentK ? 8 : 4);

  elbowChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: labels,
      datasets: [{
        label: 'WCSS (Inertia)',
        data: wcssValues,
        borderColor: '#f59e0b',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        fill: true,
        tension: 0.2,
        pointBackgroundColor: pointColors,
        pointRadius: pointRadii
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: (ctx) => `WCSS: ${ctx.raw}` } }
      },
      scales: {
        x: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        y: { grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } }
      }
    }
  });
}

function renderScatterChart(scatterDatasets) {
  const ctx = document.getElementById('chart-clusters-scatter').getContext('2d');
  if (scatterChart) scatterChart.destroy();

  const chartDatasets = scatterDatasets.map(s => ({
    label: s.label,
    data: s.points,
    backgroundColor: s.color,
    pointRadius: 5,
    pointHoverRadius: 8
  }));

  scatterChart = new Chart(ctx, {
    type: 'scatter',
    data: { datasets: chartDatasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { position: 'bottom', labels: { color: '#94a3b8', font: { size: 10 } } },
        tooltip: {
          callbacks: {
            label: (ctx) => {
              const pt = ctx.raw;
              return `${pt.customer_name} (${pt.customer_id}): Recency ${pt.x} days, Spend ${formatCurrency(pt.y)}`;
            }
          }
        }
      },
      scales: {
        x: { title: { display: true, text: 'Recency (Days since last order)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8' } },
        y: { title: { display: true, text: 'Monetary Spend (₹)', color: '#94a3b8' }, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#94a3b8', callback: (v) => '₹' + (v/1000) + 'k' } }
      }
    }
  });
}

function renderSegmentCards(clusterSummary) {
  const container = document.getElementById('segment-cards-container');
  container.innerHTML = clusterSummary.map(c => `
    <div class="col-lg-6 col-xl-3">
      <div class="glass-card h-100 d-flex flex-column" style="border-top: 4px solid ${c.color};">
        <div class="d-flex align-items-center justify-content-between mb-2">
          <span class="badge" style="background-color: ${c.color}25; color: ${c.color}; border: 1px solid ${c.color}60;">
            Cluster ${c.cluster_id + 1}
          </span>
          <span class="fs-7 fw-bold text-muted">${c.percentage}% of total</span>
        </div>

        <h4 class="fw-bold fs-6 mb-1 text-white">${c.segment_name}</h4>
        <p class="text-muted small mb-3 flex-grow-1" style="font-size: 0.78rem;">${c.description}</p>

        <div class="bg-dark/40 rounded-3 p-3 mb-3 border border-secondary/20">
          <div class="d-flex justify-content-between mb-1 small">
            <span class="text-muted">Customers:</span>
            <span class="fw-bold text-white">${formatNumber(c.customer_count)}</span>
          </div>
          <div class="d-flex justify-content-between mb-1 small">
            <span class="text-muted">Avg Spend:</span>
            <span class="fw-bold text-emerald-400">${formatCurrency(c.avg_monetary)}</span>
          </div>
          <div class="d-flex justify-content-between mb-1 small">
            <span class="text-muted">Avg Orders:</span>
            <span class="fw-bold text-white">${c.avg_frequency}</span>
          </div>
          <div class="d-flex justify-content-between small">
            <span class="text-muted">Avg Recency:</span>
            <span class="fw-bold text-info">${c.avg_recency} days</span>
          </div>
        </div>

        <button class="btn btn-sm btn-outline-secondary w-100" onclick="openSegmentModal(${c.cluster_id}, '${c.segment_name}')">
          <i class="bi bi-people me-1"></i> View ${c.customer_count} Customers
        </button>
      </div>
    </div>
  `).join('');
}

function openSegmentModal(clusterId, segmentName) {
  if (!currentSegmentationData) return;

  const segmentCustomers = currentSegmentationData.customers.filter(c => c.cluster === clusterId);
  document.getElementById('modal-segment-title').textContent = `${segmentName} (Cluster ${clusterId + 1})`;

  const tbody = document.querySelector('#table-modal-customers tbody');
  tbody.innerHTML = segmentCustomers.map(c => `
    <tr>
      <td class="fw-bold text-indigo-300">${c.customer_id}</td>
      <td class="fw-semibold">${c.customer_name}</td>
      <td class="text-info">${c.recency} days</td>
      <td class="fw-semibold">${c.frequency}</td>
      <td class="text-end fw-bold text-emerald-400">${formatCurrency(c.monetary)}</td>
      <td class="text-center font-monospace"><span class="badge bg-dark border border-secondary">${c.rfm_score_str}</span></td>
    </tr>
  `).join('');

  const modal = new bootstrap.Modal(document.getElementById('modal-segment-customers'));
  modal.show();
}
