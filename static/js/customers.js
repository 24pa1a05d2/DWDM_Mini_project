/* Customer RFM Controller */

let rfmCustomers = [];

document.addEventListener('DOMContentLoaded', () => {
  loadRFMData();

  document.getElementById('rfm-search').addEventListener('input', filterAndRenderRFM);
  document.getElementById('rfm-sort-by').addEventListener('change', filterAndRenderRFM);
});

async function loadRFMData() {
  try {
    const res = await fetchAPI('/api/rfm');
    if (res.success) {
      rfmCustomers = res.customers;
      updateRFMKPIs(res.summary);
      filterAndRenderRFM();
    }
  } catch (err) {
    console.error('Failed to load RFM data', err);
  }
}

function updateRFMKPIs(summary) {
  document.getElementById('rfm-kpi-total').textContent = formatNumber(summary.total_customers);
  document.getElementById('rfm-kpi-recency').textContent = `${summary.avg_recency} Days`;
  document.getElementById('rfm-kpi-frequency').textContent = `${summary.avg_frequency} Orders`;
  document.getElementById('rfm-kpi-monetary').textContent = formatCurrency(summary.avg_monetary);
}

function filterAndRenderRFM() {
  const searchTerm = document.getElementById('rfm-search').value.toLowerCase();
  const sortBy = document.getElementById('rfm-sort-by').value;

  let filtered = rfmCustomers.filter(c =>
    c.customer_id.toLowerCase().includes(searchTerm) ||
    c.customer_name.toLowerCase().includes(searchTerm) ||
    (c.customer_location && c.customer_location.toLowerCase().includes(searchTerm))
  );

  filtered.sort((a, b) => {
    if (sortBy === 'recency') return a.recency - b.recency; // Lower is better
    if (sortBy === 'frequency') return b.frequency - a.frequency;
    if (sortBy === 'monetary') return b.monetary - a.monetary;
    return b.rfm_total_score - a.rfm_total_score;
  });

  const tbody = document.querySelector('#table-rfm-customers tbody');

  if (filtered.length === 0) {
    tbody.innerHTML = `<tr><td colspan="9" class="text-center text-muted py-4">No matching customers found.</td></tr>`;
    return;
  }

  tbody.innerHTML = filtered.map(c => `
    <tr>
      <td><span class="fw-bold text-indigo-300">${c.customer_id}</span></td>
      <td class="fw-semibold">${c.customer_name}</td>
      <td>${c.customer_location || '-'}</td>
      <td>${c.last_purchase_date}</td>
      <td class="text-end fw-semibold text-info">${c.recency} days</td>
      <td class="text-end fw-semibold">${c.frequency}</td>
      <td class="text-end fw-bold text-emerald-400">${formatCurrency(c.monetary)}</td>
      <td class="text-center">
        <span class="badge bg-dark border border-secondary text-indigo-300 font-monospace">${c.r_score}-${c.f_score}-${c.m_score}</span>
      </td>
      <td class="text-center">
        <span class="badge ${c.rfm_total_score >= 12 ? 'bg-success' : c.rfm_total_score >= 8 ? 'bg-primary' : 'bg-secondary'} px-3">
          Score ${c.rfm_total_score}
        </span>
      </td>
    </tr>
  `).join('');
}
