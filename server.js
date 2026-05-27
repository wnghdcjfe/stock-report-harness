#!/usr/bin/env node

const http = require('http');
const fs = require('fs');
const path = require('path');

const PORT = Number(process.env.PORT) || 3000;
const ROOT = path.resolve(__dirname, 'output');
const REQUESTED_REPORT = process.argv[2] || process.env.REPORT_SLUG || process.env.REPORT;

const MIME_TYPES = {
  '.html': 'text/html; charset=utf-8',
  '.htm': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.mjs': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.png': 'image/png',
  '.jpg': 'image/jpeg',
  '.jpeg': 'image/jpeg',
  '.gif': 'image/gif',
  '.svg': 'image/svg+xml',
  '.webp': 'image/webp',
  '.ico': 'image/x-icon',
  '.txt': 'text/plain; charset=utf-8',
  '.pdf': 'application/pdf',
};

function send(res, statusCode, body, headers = {}) {
  res.writeHead(statusCode, {
    'Content-Type': 'text/plain; charset=utf-8',
    ...headers,
  });
  res.end(body);
}

function safeResolve(urlPath) {
  const decodedPath = decodeURIComponent(urlPath.split('?')[0]);
  const filePath = path.resolve(ROOT, `.${decodedPath}`);

  if (filePath !== ROOT && !filePath.startsWith(`${ROOT}${path.sep}`)) {
    return null;
  }

  return filePath;
}

function renderDirectoryListing(reqPath, entries) {
  const rows = entries
    .filter((entry) => !entry.name.startsWith('.'))
    .map((entry) => {
      const href = path.posix.join(reqPath, entry.name) + (entry.isDirectory() ? '/' : '');
      return `<li><a href="${href}">${entry.name}${entry.isDirectory() ? '/' : ''}</a></li>`;
    })
    .join('\n');

  return `<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>output static server</title>
  <style>
    body { font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; max-width: 800px; margin: 40px auto; padding: 0 20px; line-height: 1.5; }
    a { color: #2563eb; }
  </style>
</head>
<body>
  <h1>output/</h1>
  <ul>${rows || '<li>No files</li>'}</ul>
</body>
</html>`;
}

function toUrlPath(filePath) {
  const relativePath = path.relative(ROOT, filePath).split(path.sep).join('/');
  return `/${relativePath}`;
}

function reportUrl(filePath) {
  return `http://localhost:${PORT}${encodeURI(toUrlPath(filePath))}`;
}

function findHtmlReports() {
  if (!fs.existsSync(ROOT)) {
    return [];
  }

  return fs
    .readdirSync(ROOT, { withFileTypes: true })
    .filter((entry) => entry.isFile() && entry.name.endsWith('.html') && !entry.name.startsWith('.'))
    .map((entry) => {
      const filePath = path.join(ROOT, entry.name);
      return { filePath, name: entry.name, mtimeMs: fs.statSync(filePath).mtimeMs };
    })
    .sort((a, b) => b.mtimeMs - a.mtimeMs);
}

function normalizeRequestedReport(value) {
  if (!value) {
    return '';
  }

  const basename = path.basename(String(value).trim());
  return basename.endsWith('.html') ? basename : `${basename}.html`;
}

function printReportLinks() {
  const reports = findHtmlReports();
  const requestedName = normalizeRequestedReport(REQUESTED_REPORT);
  const requestedReport = requestedName
    ? reports.find((report) => report.name === requestedName)
    : null;
  const latestReport = requestedReport || reports[0];

  console.log(`Serving ${ROOT} at http://localhost:${PORT}/`);

  if (requestedName && !requestedReport) {
    console.warn(`Requested report not found: output/${requestedName}`);
  }

  if (!latestReport) {
    console.log('No HTML reports found yet. Build a report into output/*.html, then reload this server.');
    return;
  }

  console.log(`Report URL: ${reportUrl(latestReport.filePath)}`);

  if (reports.length > 1) {
    console.log('Available reports:');
    reports.forEach((report) => console.log(`- ${reportUrl(report.filePath)}`));
  }
}

const server = http.createServer((req, res) => {
  if (!['GET', 'HEAD'].includes(req.method)) {
    return send(res, 405, 'Method Not Allowed', { Allow: 'GET, HEAD' });
  }

  let filePath;
  try {
    filePath = safeResolve(req.url || '/');
  } catch (_) {
    return send(res, 400, 'Bad Request');
  }

  if (!filePath) {
    return send(res, 403, 'Forbidden');
  }

  fs.stat(filePath, (statError, stats) => {
    if (statError) {
      return send(res, 404, 'Not Found');
    }

    if (stats.isDirectory()) {
      const indexPath = path.join(filePath, 'index.html');
      if (fs.existsSync(indexPath)) {
        filePath = indexPath;
      } else {
        const reqPath = new URL(req.url || '/', `http://${req.headers.host || 'localhost'}`).pathname;
        const entries = fs.readdirSync(filePath, { withFileTypes: true });
        const html = renderDirectoryListing(reqPath, entries);
        res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
        return res.end(req.method === 'HEAD' ? undefined : html);
      }
    }

    const ext = path.extname(filePath).toLowerCase();
    const contentType = MIME_TYPES[ext] || 'application/octet-stream';
    res.writeHead(200, { 'Content-Type': contentType });

    if (req.method === 'HEAD') {
      return res.end();
    }

    fs.createReadStream(filePath).pipe(res);
  });
});

server.on('error', (error) => {
  if (error.code === 'EADDRINUSE') {
    console.error(`Port ${PORT} is already in use. Stop the existing server or run with PORT=<other-port> node server.js.`);
    process.exit(1);
  }

  throw error;
});

server.listen(PORT, printReportLinks);
