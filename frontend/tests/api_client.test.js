import test from 'node:test';
import assert from 'node:assert';

// Mock localStorage for Node test runner
const storage = new Map();
globalThis.localStorage = {
  getItem: (key) => storage.get(key) || null,
  setItem: (key, val) => storage.set(key, String(val)),
  removeItem: (key) => storage.delete(key),
  clear: () => storage.clear(),
};

// Import client functions
const {
  API_BASE_URL,
  getAuthToken,
  setAuthToken,
  checkHealth,
  checkGeminiHealth,
  uploadDocument,
  getDocuments,
  getDocument,
  getDocumentChunks,
  getClauses,
  getFindings,
  askQuestion,
  compareLeases,
  getComparison,
  submitSituation,
  getActionPlan,
  getLawyerQuestions,
  getExportPdfUrl,
} = await import('../src/api/client.ts');

test('API_BASE_URL is sanitized without trailing slash', () => {
  assert.ok(API_BASE_URL);
  assert.strictEqual(API_BASE_URL.endsWith('/'), false);
});

test('auth token management stores and retrieves token', () => {
  setAuthToken('jwt_test_token_12345');
  assert.strictEqual(getAuthToken(), 'jwt_test_token_12345');

  setAuthToken(null);
  assert.strictEqual(getAuthToken(), null);
});

test('checkHealth returns status when API responds 200', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/health`);
    return {
      ok: true,
      json: async () => ({ status: 'ok', service: 'clauselens-backend', version: '0.1.0' }),
    };
  };

  try {
    const res = await checkHealth();
    assert.strictEqual(res.status, 'ok');
    assert.strictEqual(res.service, 'clauselens-backend');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('checkHealth throws error with status text on 500 failure', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 500,
    statusText: 'Internal Server Error',
    json: async () => ({ detail: 'Service database connection failed.' }),
  });

  try {
    await assert.rejects(
      async () => await checkHealth(),
      /Service database connection failed/
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('checkGeminiHealth returns model status and latency', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/health/gemini`);
    return {
      ok: true,
      json: async () => ({ status: 'ok', latency_ms: 45, flash_model: 'gemini-3.8-flash' }),
    };
  };

  try {
    const res = await checkGeminiHealth();
    assert.strictEqual(res.status, 'ok');
    assert.strictEqual(res.flash_model, 'gemini-3.8-flash');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('uploadDocument sends multipart form data with auth headers', async () => {
  setAuthToken('token_upload_test');
  const originalFetch = globalThis.fetch;

  let capturedHeaders = null;
  let capturedBody = null;

  globalThis.fetch = async (url, options) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents`);
    assert.strictEqual(options.method, 'POST');
    capturedHeaders = options.headers;
    capturedBody = options.body;
    return {
      ok: true,
      json: async () => ({
        id: 'doc-uuid-1',
        filename: 'test_lease.pdf',
        mime_type: 'application/pdf',
        page_count: 2,
        status: 'ready',
      }),
    };
  };

  try {
    // Mock File object
    const fakeFile = { name: 'test_lease.pdf', size: 1024, type: 'application/pdf' };
    const doc = await uploadDocument(fakeFile);
    assert.strictEqual(doc.id, 'doc-uuid-1');
    assert.strictEqual(doc.filename, 'test_lease.pdf');
    assert.strictEqual(capturedHeaders['Authorization'], 'Bearer token_upload_test');
    assert.ok(capturedBody);
  } finally {
    setAuthToken(null);
    globalThis.fetch = originalFetch;
  }
});

test('uploadDocument propagates 415 Unsupported Media Type detail', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: false,
    status: 415,
    statusText: 'Unsupported Media Type',
    json: async () => ({ detail: 'Only legitimate PDF and DOCX files are accepted.' }),
  });

  try {
    const fakeFile = { name: 'virus.exe', size: 500 };
    await assert.rejects(
      async () => await uploadDocument(fakeFile),
      /Only legitimate PDF and DOCX files are accepted/
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getDocuments returns list of documents', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents`);
    return {
      ok: true,
      json: async () => [
        { id: 'doc-1', filename: 'lease1.pdf', page_count: 3 },
        { id: 'doc-2', filename: 'lease2.docx', page_count: 2 },
      ],
    };
  };

  try {
    const docs = await getDocuments();
    assert.strictEqual(docs.length, 2);
    assert.strictEqual(docs[0].id, 'doc-1');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getClauses appends category query param', async () => {
  const originalFetch = globalThis.fetch;
  let requestedUrl = null;

  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return {
      ok: true,
      json: async () => [{ id: 'cl-1', heading: 'Termination', category: 'termination_penalties' }],
    };
  };

  try {
    const clauses = await getClauses('doc-123', 'termination_penalties');
    assert.strictEqual(clauses.length, 1);
    assert.ok(requestedUrl.includes('category=termination_penalties'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getFindings appends severity and category query params', async () => {
  const originalFetch = globalThis.fetch;
  let requestedUrl = null;

  globalThis.fetch = async (url) => {
    requestedUrl = url;
    return {
      ok: true,
      json: async () => [{ id: 'f-1', severity: 'high', type: 'risk' }],
    };
  };

  try {
    const findings = await getFindings('doc-123', 'high', 'rent_fees');
    assert.strictEqual(findings.length, 1);
    assert.ok(requestedUrl.includes('severity=high'));
    assert.ok(requestedUrl.includes('category=rent_fees'));
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('askQuestion sends JSON body and returns verified citations', async () => {
  const originalFetch = globalThis.fetch;
  let requestBody = null;

  globalThis.fetch = async (url, options) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents/doc-99/ask`);
    assert.strictEqual(options.method, 'POST');
    requestBody = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({
        answer: 'Notice period is 60 days.',
        status: 'grounded_high',
        citations: [{ page: 2, clause_id: '9(a)', quote: 'sixty (60) days notice', verified: true }],
        conversation_id: 'conv-abc',
      }),
    };
  };

  try {
    const resp = await askQuestion('doc-99', 'What is the notice period?', 'conv-abc');
    assert.strictEqual(requestBody.question, 'What is the notice period?');
    assert.strictEqual(requestBody.conversation_id, 'conv-abc');
    assert.strictEqual(resp.status, 'grounded_high');
    assert.strictEqual(resp.citations[0].verified, true);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('compareLeases sends document_a_id and document_b_id in JSON payload', async () => {
  const originalFetch = globalThis.fetch;
  let requestBody = null;

  globalThis.fetch = async (url, options) => {
    assert.strictEqual(url, `${API_BASE_URL}/compare`);
    assert.strictEqual(options.method, 'POST');
    requestBody = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({
        id: 'comp-session-1',
        document_a_id: 'doc-a',
        document_b_id: 'doc-b',
        deltas_count: 1,
        findings: [{ category: 'rent_fees', delta_description: 'Rent increased', favors: 'landlord' }],
      }),
    };
  };

  try {
    const comp = await compareLeases('doc-a', 'doc-b');
    assert.strictEqual(requestBody.document_a_id, 'doc-a');
    assert.strictEqual(requestBody.document_b_id, 'doc-b');
    assert.strictEqual(comp.deltas_count, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('submitSituation sends context text and retrieves classification', async () => {
  const originalFetch = globalThis.fetch;
  let requestBody = null;

  globalThis.fetch = async (url, options) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents/doc-55/situation`);
    requestBody = JSON.parse(options.body);
    return {
      ok: true,
      json: async () => ({
        situation_type: 'termination',
        urgency: 'high',
        relevant_categories: ['termination_penalties', 'rent_fees'],
      }),
    };
  };

  try {
    const sit = await submitSituation('doc-55', 'I have to relocate for work immediately.');
    assert.strictEqual(requestBody.context_text, 'I have to relocate for work immediately.');
    assert.strictEqual(sit.situation_type, 'termination');
    assert.strictEqual(sit.urgency, 'high');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getActionPlan retrieves ordered action steps with citations', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents/doc-55/action-plan`);
    return {
      ok: true,
      json: async () => ({
        id: 'plan-1',
        document_id: 'doc-55',
        situation_type: 'termination',
        urgency: 'high',
        steps: [
          { order: 1, action: 'Deliver written 60-day notice', rationale: 'Comply with clause 9' },
        ],
      }),
    };
  };

  try {
    const plan = await getActionPlan('doc-55');
    assert.strictEqual(plan.steps.length, 1);
    assert.strictEqual(plan.steps[0].order, 1);
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getExportPdfUrl returns correct endpoint path', () => {
  const url = getExportPdfUrl('doc-xyz');
  assert.strictEqual(url, `${API_BASE_URL}/documents/doc-xyz/export`);
});

test('getDocument fetches single document details', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents/doc-detail-1`);
    return {
      ok: true,
      json: async () => ({ id: 'doc-detail-1', filename: 'lease.pdf', page_count: 5 }),
    };
  };

  try {
    const doc = await getDocument('doc-detail-1');
    assert.strictEqual(doc.id, 'doc-detail-1');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getDocumentChunks fetches all chunk records for a document', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents/doc-detail-1/chunks`);
    return {
      ok: true,
      json: async () => [{ id: 'ch-1', page_number: 1, text: 'Rent is $2,000' }],
    };
  };

  try {
    const chunks = await getDocumentChunks('doc-detail-1');
    assert.strictEqual(chunks.length, 1);
    assert.strictEqual(chunks[0].id, 'ch-1');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getComparison retrieves saved comparison session by id', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/compare/comp-session-123`);
    return {
      ok: true,
      json: async () => ({ id: 'comp-session-123', deltas_count: 2, findings: [] }),
    };
  };

  try {
    const comp = await getComparison('comp-session-123');
    assert.strictEqual(comp.id, 'comp-session-123');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('getLawyerQuestions fetches topic-grouped questions', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url) => {
    assert.strictEqual(url, `${API_BASE_URL}/documents/doc-55/lawyer-questions`);
    return {
      ok: true,
      json: async () => ({
        document_id: 'doc-55',
        questions: [{ id: 'q-1', topic: 'Deposit', question: 'Is $3,000 legal?' }],
      }),
    };
  };

  try {
    const qs = await getLawyerQuestions('doc-55');
    assert.strictEqual(qs.questions.length, 1);
    assert.strictEqual(qs.questions[0].topic, 'Deposit');
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('signal abort properly aborts fetch request', async () => {
  const controller = new AbortController();
  controller.abort();

  const originalFetch = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    if (options.signal && options.signal.aborted) {
      const err = new Error('The operation was aborted');
      err.name = 'AbortError';
      throw err;
    }
    return { ok: true, json: async () => [] };
  };

  try {
    await assert.rejects(
      async () => await getDocuments(controller.signal),
      /aborted/
    );
  } finally {
    globalThis.fetch = originalFetch;
  }
});
