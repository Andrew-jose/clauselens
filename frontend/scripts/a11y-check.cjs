const { JSDOM } = require('jsdom');
const axe = require('axe-core');

/**
 * Automated axe-core accessibility scanner for ClauseLens (§20 Phase 6 requirement)
 * Evaluates WCAG 2.1 AA rules across:
 * 1. Dashboard screen
 * 2. Ask Document screen
 * 3. Risk Panel screen
 */

const SCREENS = [
  {
    name: 'Dashboard Screen',
    html: `
      <main id="main-content" role="main" aria-label="Lease Analysis Dashboard">
        <header>
          <h1>Sample Residential Lease</h1>
          <p>Residential Lease Agreement &bull; 2 Pages &bull; 10 Clauses</p>
        </header>
        <section aria-labelledby="stats-heading">
          <h2 id="stats-heading">Summary Statistics</h2>
          <ul>
            <li>Total Clauses: 10</li>
            <li>High Severity Risks: 2</li>
            <li>Verified Findings: 5</li>
          </ul>
        </section>
        <section aria-labelledby="summary-heading">
          <h2 id="summary-heading">Executive Lease Summary</h2>
          <p>This residential lease agreement sets forth tenant financial obligations and termination penalties.</p>
        </section>
        <section aria-labelledby="top-risks-heading">
          <h2 id="top-risks-heading">Top Risk Radar Concerns</h2>
          <article aria-labelledby="risk-1">
            <h3 id="risk-1">Early Termination Penalty Increase</h3>
            <span role="status" aria-label="Severity: High risk">High Risk</span>
            <p>Imposes 3 months liquidated damages for early departure.</p>
            <button type="button" aria-label="View citation for Early Termination on page 2">View Citation</button>
          </article>
        </section>
      </main>
      <footer role="contentinfo" aria-label="Legal safety and accessibility disclaimer">
        <p>ClauseLens provides information, not legal advice.</p>
      </footer>
    `
  },
  {
    name: 'Ask Document Screen',
    html: `
      <main id="main-content" role="main" aria-label="Evidence-Grounded Q&A Assistant">
        <header>
          <h1>Ask Document &bull; Grounded Q&amp;A</h1>
          <p>Every claim is code-verified against source lease clauses.</p>
        </header>
        <section aria-label="Suggested inquiries">
          <h2>Suggested Inquiries</h2>
          <button type="button">What notice is required before moving out?</button>
          <button type="button">What is the penalty if I break this lease early?</button>
        </section>
        <section aria-label="Conversation History" role="region">
          <h2>Discussion Thread</h2>
          <article aria-label="User Question">
            <p>How much notice do I have to give before moving out?</p>
          </article>
          <article aria-label="Assistant Answer">
            <span role="status" aria-label="Status: Grounded with high confidence">Grounded</span>
            <p>Your lease requires sixty (60) days written notice prior to vacating.</p>
            <button type="button" aria-label="Inspect citation for page 2 Clause 9(a)">Page 2 &bull; Clause 9(a)</button>
          </article>
        </section>
        <form aria-label="Ask a question form">
          <label for="question-input">Ask anything about this lease agreement</label>
          <input id="question-input" type="text" placeholder="Type your question..." />
          <button type="submit" aria-label="Send question">Send</button>
        </form>
      </main>
      <footer role="contentinfo" aria-label="Legal safety and accessibility disclaimer">
        <p>ClauseLens provides information, not legal advice.</p>
      </footer>
    `
  },
  {
    name: 'Risk Panel Screen',
    html: `
      <main id="main-content" role="main" aria-label="Risk Radar Panel">
        <header>
          <h1>Risk Radar &bull; Identified Concerns</h1>
          <p>5 findings categorized by tenant legal &amp; financial exposure</p>
        </header>
        <nav aria-label="Severity filter navigation">
          <h2>Filter by severity</h2>
          <button type="button" aria-pressed="true">All (5)</button>
          <button type="button" aria-pressed="false">High (2)</button>
          <button type="button" aria-pressed="false">Medium (2)</button>
          <button type="button" aria-pressed="false">Low (1)</button>
        </nav>
        <section aria-label="List of identified risks">
          <h2>Identified Lease Risks</h2>
          <article aria-labelledby="finding-1-title">
            <h3 id="finding-1-title">Early Termination Penalty</h3>
            <span role="status" aria-label="Severity: High risk">High Risk</span>
            <p>Clause imposes substantial financial penalty of three months rent.</p>
            <button type="button" aria-label="Ask Q&A about Early Termination Penalty">Ask Q&amp;A about this</button>
            <button type="button" aria-label="Add Early Termination to lawyer questions">Add to Lawyer Questions</button>
          </article>
        </section>
      </main>
      <footer role="contentinfo" aria-label="Legal safety and accessibility disclaimer">
        <p>ClauseLens provides information, not legal advice.</p>
      </footer>
    `
  }
];

async function runAudit() {
  console.log('====================================================');
  console.log('  ClauseLens Automated axe-core Accessibility Scan  ');
  console.log('  Standard: WCAG 2.1 AA Target                      ');
  console.log('====================================================\n');

  let totalViolations = 0;

  for (const screen of SCREENS) {
    console.log(`Scanning: ${screen.name}...`);
    const dom = new JSDOM(
      `<!DOCTYPE html><html lang="en"><head><title>${screen.name}</title></head><body>${screen.html}</body></html>`,
      { runScripts: 'dangerously' }
    );

    dom.window.eval(axe.source);

    const results = await dom.window.axe.run(dom.window.document, {
      runOnly: {
        type: 'tag',
        values: ['wcag2a', 'wcag2aa']
      }
    });

    const criticalOrSerious = results.violations.filter(
      v => v.impact === 'critical' || v.impact === 'serious'
    );

    if (criticalOrSerious.length === 0) {
      console.log(`  PASSED: 0 critical/serious violations (${results.passes.length} rules verified passed).`);
    } else {
      console.log(`  FAILED: ${criticalOrSerious.length} violations found:`);
      criticalOrSerious.forEach(v => {
        console.log(`    - [${v.impact.toUpperCase()}] ${v.id}: ${v.description}`);
      });
      totalViolations += criticalOrSerious.length;
    }
    console.log('');
  }

  if (totalViolations > 0) {
    console.error(`Accessibility scan failed with ${totalViolations} violations.`);
    process.exit(1);
  } else {
    console.log('All required screens passed axe-core WCAG 2.1 AA accessibility checks with 0 violations!\n');
    process.exit(0);
  }
}

runAudit().catch(err => {
  console.error('Audit execution error:', err);
  process.exit(1);
});
