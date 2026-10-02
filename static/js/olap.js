/* OLAP Operations Controller */

let olapChart = null;
let currentOp = 'rollup';

document.addEventListener('DOMContentLoaded', () => {
  loadSliceOptions();

  // Tab switcher
  document.querySelectorAll('#olap-tabs button').forEach(btn => {
    btn.addEventListener('click', (e) => {
      document.querySelectorAll('#olap-tabs button').forEach(b => b.classList.remove('active'));
      e.target.classList.add('active');

      currentOp = e.target.dataset.op;

      // Show/hide control panels
      document.querySelectorAll('.olap-control-panel').forEach(p => p.classList.add('d-none'));
      document.getElementById(`olap-ctrl-${currentOp}`).classList.remove('d-none');

      runCurrentOLAP();
    });
  });

  document.getElementById('btn-run-rollup').addEventListener('click', runRollUp);
  document.getElementById('btn-run-drilldown').addEventListener('click', runDrillDown);
  document.getElementById('btn-run-slice').addEventListener('click', runSlice);
  document.getElementById('btn-run-dice').addEventListener('click', runDice);

  document.getElementById('slice-dimension').addEventListener('change', loadSliceOptions);

  runRollUp();
});

async function loadSliceOptions() {
  const dim = document.getElementById('slice-dimension').value;
  try {
    const res = await fetchAPI('/api/filters');
    if (res.success) {
      const sliceValSelect = document.getElementById('slice-value');
      sliceValSelect.innerHTML = '';

      let items = dim === 'category' ? res.filters.categories : res.filters.regions;

      items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item;
        sliceValSelect.appendChild(opt);
      });

      // Populate dice multi-selects if empty
      const catBox = document.getElementById('dice-categories-box');
      if (catBox && catBox.children.length === 0) {
        catBox.innerHTML = res.filters.categories.map((c, i) => `
          <div class="form-check">
            <input class="form-check-input dice-cat-check" type="checkbox" value="${c}" id="dcat_${i}" ${i < 3 ? 'checked' : ''}>
            <label class="form-check-label small" for="dcat_${i}">${c}</label>
          </div>
        `).join('');
      }

      const regBox = document.getElementById('dice-regions-box');
      if (regBox && regBox.children.length === 0) {
        regBox.innerHTML = res.filters.regions.map((r, i) => `
          <div class="form-check">
            <input class="form-check-input dice-reg-check" type="checkbox" value="${r}" id="dreg_${i}" ${i < 3 ? 'checked' : ''}>
            <label class="form-check-label small" for="dreg_${i}">${r}</label>
          </div>
        `).join('');
      }
    }
  } catch (err) {
    console.error('Error loading slice options', err);
  }
}

function runCurrentOLAP() {
  if (currentOp === 'rollup') runRollUp();
  else if (currentOp === 'drilldown') runDrillDown();
  else if (currentOp === 'slice') runSlice();
  else if (currentOp === 'dice') runDice();
}

async function runRollUp() {
  const level = document.getElementById('rollup-level').value;
  const year = document.getElementById('rollup-year').value;

  try {
    const res = await fetchAPI(`/api/olap?operation=rollup&level=${level}&year=${year}`);
    if (res.success) {
      renderOLAPResults(res.result, 'time_dimension');
    }
  } catch (err) {
    console.error('Error executing Roll-Up', err);
  }
}

async function runDrillDown() {
  const year = document.getElementById('drill-year').value;
  const quarter = document.getElementById('drill-quarter').value;
  const month = document.getElementById('drill-month').value;

  try {
    const res = await fetchAPI(`/api/olap?operation=drilldown&year=${year}&quarter=${quarter}&month=${month}`);
    if (res.success) {
      renderOLAPResults(res.result, 'time_breakdown');
    }
  } catch (err) {
    console.error('Error executing Drill-Down', err);
  }
}

async function runSlice() {
  const dim = document.getElementById('slice-dimension').value;
  const val = document.getElementById('slice-value').value;

  try {
    const res = await fetchAPI(`/api/olap?operation=slice&dimension=${dim}&value=${encodeURIComponent(val)}`);
    if (res.success) {
      renderOLAPResults(res.result, 'month_name');
    }
  } catch (err) {
    console.error('Error executing Slice', err);
  }
}

async function runDice() {
  const cats = Array.from(document.querySelectorAll('.dice-cat-check:checked')).map(c => c.value);
  const regs = Array.from(document.querySelectorAll('.dice-reg-check:checked')).map(r => r.value);
  const yrs = Array.from(document.querySelectorAll('.dice-year-check:checked')).map(y => y.value);

  const params = new URLSearchParams();
  params.append('operation', 'dice');
  cats.forEach(c => params.append('categories', c));
  regs.forEach(r => params.append('regions', r));
  yrs.forEach(y => params.append('years', y));

  try {
    const res = await fetchAPI(`/api/olap?${params.toString()}`);
    if (res.success) {
      renderOLAPResults(res.result, 'category');
    }
  } catch (err) {
    console.error('Error executing Dice', err);
  }
}

function renderOLAPResults(olapRes, primaryDimensionKey) {
  document.getElementById('olap-viva-title').textContent = `DWDM Viva Explanation: ${olapRes.operation} Operation`;
  document.getElementById('olap-viva-desc').textContent = olapRes.viva_description;
  document.getElementById('olap-sql-box').textContent = olapRes.sql_executed;

  const records = olapRes.records;
  if (!records || records.length === 0) {
    document.querySelector('#table-olap-result tbody').innerHTML = `<tr><td colspan="4" class="text-center text-muted py-4">No data returned for selected OLAP parameters.</td></tr>`;
    if (olapChart) olapChart.destroy();
    return;
  }

  // Render Table
  const tbody = document.querySelector('#table-olap-result tbody');
  tbody.innerHTML = records.map(r => {
    const label = r[primaryDimensionKey] || r.category || r.time_dimension || r.time_breakdown || 'Item';
    return `
      <tr>
        <td class="fw-semibold text-white">${label}</td>
        <td class="text-end">${formatNumber(r.total_orders)}</td>
        <td class="text-end">${formatNumber(r.total_units_sold)}</td>
        <td class="text-end fw-bold text-emerald-400">${formatCurrency(r.total_revenue)}</td>
      </tr>
    `;
  }).join('');

  // Render Chart
  const ctx = document.getElementById('chart-olap-result').getContext('2d');
  if (olapChart) olapChart.destroy();

  const labels = records.map(r => r[primaryDimensionKey] || r.category || r.time_dimension || r.time_breakdown || 'Item');
  const revenues = records.map(r => r.total_revenue);

  olapChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: labels,
      datasets: [{
        label: 'Total Revenue (₹)',
        data: revenues,
        backgroundColor: 'rgba(16, 185, 129, 0.8)',
        borderRadius: 6
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
