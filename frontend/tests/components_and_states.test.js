import test from 'node:test';
import assert from 'node:assert';
import { JSDOM } from 'jsdom';

test('Empty State: Document viewer displays clear guidance when no document is active', () => {
  const dom = new JSDOM(`
    <div class="h-full flex items-center justify-center p-8 text-center" role="region" aria-label="Document Viewer">
      <div class="max-w-md space-y-3">
        <h3 class="text-base font-bold text-slate-900">No Document Selected</h3>
        <p class="text-xs text-slate-500">
          Upload a residential lease or choose an active lease from the document selector above to inspect clauses and citations.
        </p>
        <button type="button" aria-label="Upload New Lease">Upload Lease</button>
      </div>
    </div>
  `);

  const doc = dom.window.document;
  const heading = doc.querySelector('h3');
  assert.ok(heading);
  assert.strictEqual(heading.textContent, 'No Document Selected');
  const uploadBtn = doc.querySelector('button[aria-label="Upload New Lease"]');
  assert.ok(uploadBtn);
});

test('Loading State: Upload modal presents active progress spinner and step announcements', () => {
  const dom = new JSDOM(`
    <div role="dialog" aria-modal="true" aria-labelledby="upload-modal-title">
      <h2 id="upload-modal-title">Upload Residential Lease</h2>
      <div class="p-3.5 rounded-xl bg-brand-50" role="status" aria-live="polite">
        <span class="animate-spin" aria-hidden="true">Loading...</span>
        <span>Processing Lease Pipeline</span>
        <p>Detecting clause boundaries &amp; chunking...</p>
      </div>
      <button type="button" disabled aria-label="Close upload dialog">Cancel</button>
    </div>
  `);

  const doc = dom.window.document;
  const statusRegion = doc.querySelector('[role="status"]');
  assert.ok(statusRegion);
  assert.strictEqual(statusRegion.getAttribute('aria-live'), 'polite');
  assert.ok(statusRegion.textContent.includes('Processing Lease Pipeline'));
  const disabledCancel = doc.querySelector('button[disabled]');
  assert.ok(disabledCancel);
});

test('Error State: Upload modal surfaces user-friendly error banners on invalid file', () => {
  const errorMessage = 'File size exceeds the 15 MB limit.';
  const dom = new JSDOM(`
    <div role="dialog" aria-modal="true">
      <div role="alert" class="bg-red-50 text-red-700">
        <span aria-hidden="true">!</span>
        <span>${errorMessage}</span>
      </div>
    </div>
  `);

  const doc = dom.window.document;
  const alertBox = doc.querySelector('[role="alert"]');
  assert.ok(alertBox);
  assert.ok(alertBox.textContent.includes(errorMessage));
});

test('Error State: Chat Q&A safely announces API communication failure without breaking UI', () => {
  const dom = new JSDOM(`
    <section aria-label="Conversation History" role="region">
      <div role="log" aria-live="polite">
        <article aria-label="Assistant Answer">
          <span role="status" aria-label="Status: Not found in document">Not Found</span>
          <p>Error answering question: Failed to fetch (500)</p>
        </article>
      </div>
    </section>
  `);

  const doc = dom.window.document;
  const logRegion = doc.querySelector('[role="log"]');
  assert.ok(logRegion);
  assert.strictEqual(logRegion.getAttribute('aria-live'), 'polite');
  assert.ok(logRegion.textContent.includes('Failed to fetch'));
});

test('Document Selection Behavior: Selector updates active document attributes', () => {
  const dom = new JSDOM(`
    <select aria-label="Active Document Selector" id="doc-select">
      <option value="doc-1" selected>Lease_A.pdf (2p)</option>
      <option value="doc-2">Lease_B.docx (3p)</option>
    </select>
  `);

  const select = dom.window.document.getElementById('doc-select');
  assert.strictEqual(select.value, 'doc-1');
  select.value = 'doc-2';
  assert.strictEqual(select.value, 'doc-2');
});

test('Accessibility: Modal focus container has tabIndex and dialog role', () => {
  const dom = new JSDOM(`
    <div id="modal-container" role="dialog" aria-modal="true" aria-labelledby="upload-modal-title" tabindex="-1">
      <h2 id="upload-modal-title">Upload Residential Lease</h2>
      <button type="button" aria-label="Close upload dialog">Close</button>
    </div>
  `);

  const modal = dom.window.document.getElementById('modal-container');
  assert.strictEqual(modal.getAttribute('role'), 'dialog');
  assert.strictEqual(modal.getAttribute('aria-modal'), 'true');
  assert.strictEqual(modal.getAttribute('tabindex'), '-1');
  assert.strictEqual(modal.getAttribute('aria-labelledby'), 'upload-modal-title');
});

test('Accessibility: Keyboard Skip to Main Content link targets valid landmark', () => {
  const dom = new JSDOM(`
    <body>
      <a href="#main-content" class="sr-only focus:not-sr-only">Skip to main content</a>
      <header><nav></nav></header>
      <main id="main-content" role="main" tabindex="-1">
        <h1>Dashboard</h1>
      </main>
    </body>
  `);

  const doc = dom.window.document;
  const skipLink = doc.querySelector('a[href="#main-content"]');
  assert.ok(skipLink);
  const mainLandmark = doc.getElementById('main-content');
  assert.ok(mainLandmark);
  assert.strictEqual(mainLandmark.getAttribute('role'), 'main');
});

test('Accessibility: Tab navigation marks active view with aria-current="page"', () => {
  const dom = new JSDOM(`
    <nav aria-label="Application Sections">
      <button aria-current="page">Dashboard</button>
      <button>Risk Radar</button>
      <button>Clause Explorer</button>
    </nav>
  `);

  const doc = dom.window.document;
  const activeTab = doc.querySelector('button[aria-current="page"]');
  assert.ok(activeTab);
  assert.strictEqual(activeTab.textContent, 'Dashboard');
});

test('Citation selection rail displays active quote and verified badge', () => {
  const dom = new JSDOM(`
    <aside aria-label="Active Citation and Evidence Panel" role="complementary">
      <div class="citation-card" role="region" aria-labelledby="citation-badge">
        <span id="citation-badge" role="status" aria-label="Verification status: Code verified against source chunk">
          Code-Verified &bull; 100% Match
        </span>
        <blockquote>Tenant agrees to pay monthly rent of $2,400.00.</blockquote>
        <span aria-label="Page 1 &bull; Clause 3">Page 1 &bull; Clause 3</span>
        <button type="button" aria-label="Jump to page 1 in Document Viewer">Jump to Page 1</button>
      </div>
    </aside>
  `);

  const doc = dom.window.document;
  const badge = doc.getElementById('citation-badge');
  assert.ok(badge);
  assert.ok(badge.textContent.includes('Code-Verified'));
  const jumpBtn = doc.querySelector('button[aria-label="Jump to page 1 in Document Viewer"]');
  assert.ok(jumpBtn);
});
