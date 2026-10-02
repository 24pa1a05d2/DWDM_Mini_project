/* Data Management & ETL Controller */

document.addEventListener('DOMContentLoaded', () => {
  const fileInput = document.getElementById('input-csv-file');
  const uploadBtn = document.getElementById('btn-upload-submit');
  const fileNameDisplay = document.getElementById('file-name-display');
  const formUpload = document.getElementById('form-upload-csv');
  const btnSample = document.getElementById('btn-run-sample');

  if (fileInput) {
    fileInput.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        const file = e.target.files[0];
        fileNameDisplay.textContent = `Selected: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
        uploadBtn.disabled = false;
      }
    });
  }

  if (formUpload) {
    formUpload.addEventListener('submit', async (e) => {
      e.preventDefault();
      if (!fileInput.files[0]) return;

      const formData = new FormData();
      formData.append('file', fileInput.files[0]);

      await executeETL('/api/etl/upload', { method: 'POST', body: formData });
    });
  }

  if (btnSample) {
    btnSample.addEventListener('click', async () => {
      await executeETL('/api/etl/run_sample', { method: 'POST' });
    });
  }
});

async function executeETL(url, fetchOptions = {}) {
  const logBox = document.getElementById('etl-log-box');
  const statusBadge = document.getElementById('etl-status-badge');

  statusBadge.className = 'badge bg-warning text-dark';
  statusBadge.textContent = 'Processing ETL...';

  logBox.textContent = `[ETL Extract] Reading dataset...\n[ETL Transform] Executing cleaning rules, deduplication & data validation...\n[ETL Load] Inserting records into Star Schema Data Warehouse...`;

  try {
    const res = await fetchAPI(url, fetchOptions);
    if (res.success) {
      statusBadge.className = 'badge bg-success';
      statusBadge.textContent = 'ETL Complete';

      const stats = res.stats;
      document.getElementById('stat-extracted').textContent = formatNumber(stats.extracted_count);
      document.getElementById('stat-duplicates').textContent = formatNumber(stats.removed_duplicates);
      document.getElementById('stat-invalid').textContent = formatNumber(stats.invalid_records_count + stats.missing_values_count);
      document.getElementById('stat-loaded').textContent = formatNumber(stats.loaded_count);
      document.getElementById('stat-time').textContent = `${stats.processing_time_ms} ms`;

      logBox.textContent = `[ETL Success] Processed in ${stats.processing_time_ms} ms\n- Extracted: ${stats.extracted_count} rows\n- Duplicates Removed: ${stats.removed_duplicates}\n- Invalid Records Dropped: ${stats.invalid_records_count + stats.missing_values_count}\n- Valid Records Loaded into FACT_SALES: ${stats.loaded_count}`;

      renderPreviewTable(res.preview);
      showToast('ETL Pipeline successfully cleaned and loaded dataset into Data Warehouse!', 'success');
    }
  } catch (err) {
    statusBadge.className = 'badge bg-danger';
    statusBadge.textContent = 'ETL Failed';
    logBox.textContent += `\n[ETL ERROR] ${err.message}`;
  }
}

function renderPreviewTable(records) {
  const tbody = document.querySelector('#table-clean-preview tbody');
  if (!records || records.length === 0) {
    tbody.innerHTML = `<tr><td colspan="10" class="text-center text-muted py-4">No records found.</td></tr>`;
    return;
  }

  tbody.innerHTML = records.map(r => `
    <tr>
      <td><span class="fw-bold text-indigo-300">${r.order_id || r['Invoice/Order ID']}</span></td>
      <td>${r.customer_id || r['Customer ID']}</td>
      <td>${r.customer_name || r['Customer Name'] || '-'}</td>
      <td>${r.product_name || r['Product Name']}</td>
      <td><span class="badge bg-dark border border-secondary">${r.category || r['Category']}</span></td>
      <td class="text-end fw-semibold">${r.quantity || r['Quantity']}</td>
      <td class="text-end">${formatCurrency(r.unit_price || r['Unit Price'])}</td>
      <td class="text-end fw-bold text-emerald-400">${formatCurrency(r.total_amount || r['Total Amount'])}</td>
      <td>${r.order_date || r['Order Date']}</td>
      <td><span class="badge bg-secondary">${r.region || r['Region']}</span></td>
    </tr>
  `).join('');
}
