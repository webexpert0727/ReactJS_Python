export function formatPackaging(packaging) {
  if (packaging === 'WB') return 'Whole Beans';
  else if (packaging === 'DR') return 'Drip Bags';
  else if (packaging === 'GR') return 'Ground';
  else if (packaging === 'SP') return 'Shotpod';
  else if (packaging === 'BO') return 'Bottled 6 x (330ml)';
  return packaging;
}

export function formatStatus(status) {
  if (status === 'AC') return 'Active';
  else if (status === 'SH') return 'Shipped';
  else if (status === 'CA') return 'Cancelled';
  else if (status === 'ER') return 'Error';
  else if (status === 'PA') return 'Paused';
  else if (status === 'DE') return 'Declined';
  return status;
}

export function printPDF(pdfdoc, resp) {
  console.log('printPDF:', resp);
  const file = new Blob([resp.data], { type: 'application/pdf' });
  const link = window.URL.createObjectURL(file);
  const iframe = document.createElement('iframe');
  iframe.style.display = 'none';
  iframe.src = link;
  pdfdoc.append(iframe);
  iframe.focus();
  iframe.contentWindow.print();
}

export function downloadPDF(resp) {
  console.log('downloadPDF:', resp);
  const file = new Blob([resp.data], { type: 'application/pdf' });
  const filename = /filename=(.*)/.exec(resp.headers['content-disposition'])[1];
  console.log('filename:', filename);
  const link = document.createElement('a');
  link.href = window.URL.createObjectURL(file);
  link.download = filename;
  link.click();
  window.URL.revokeObjectURL(link);
}

export function getBeanStatus(stocklevel, threshold) {
  if (stocklevel > 1.5 * threshold) return 'green';
  else if (stocklevel > threshold) return 'orange';
  return 'red';
}
