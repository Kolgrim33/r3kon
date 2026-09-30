import shutil, sys

MAIN_BLOCK = r'''
from flask import Response, stream_with_context


def _nd(obj):
    return json.dumps(obj) + '\n'


@app.route('/api/triage/batch', methods=['POST'])
def triage_batch():
    data = request.get_json(silent=True) or {}
    texts = data.get('texts')
    if not isinstance(texts, list) or not texts:
        return jsonify({'error': 'No messages'}), 400
    texts = texts[:5000]
    use_ai = data.get('mode') != 'fast' and model_loaded

    def gen():
        for i, tx in enumerate(texts):
            try:
                tx = str(tx or '').strip()[:3000]
                if not tx:
                    yield _nd({'i': i, 'skip': True})
                    continue
                if use_ai and tri_rules_analyze(tx)['score'] < 70:
                    with model_lock:
                        r = tri_classify(tx, llm=llm)
                else:
                    r = tri_classify(tx, llm=None)
                yield _nd({'i': i, 'r': r})
            except Exception as e:
                yield _nd({'i': i, 'error': str(e)})
        yield _nd({'done': True, 'total': len(texts)})

    return Response(stream_with_context(gen()), mimetype='application/x-ndjson',
                    headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/api/csv/save', methods=['POST'])
def csv_save():
    import csv
    data = request.get_json(silent=True) or {}
    header = data.get('header') or []
    rows = data.get('rows') or []
    folder = os.path.join(BASE_PATH, 'results')
    os.makedirs(folder, exist_ok=True)
    name = re.sub(r'[^A-Za-z0-9_.-]', '_', str(data.get('name') or 'triage'))[:60]
    path = os.path.join(folder, f"{name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv")
    with open(path, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    return jsonify({'path': path, 'rows': len(rows)})
'''

UI = r'''
<script>
/* R3KON_CSV_UI: upload a CSV / TXT of messages and triage every row */
(function () {
  if (window.__r3kCsv) return;
  window.__r3kCsv = true;

  var css = [
    '#r3k-btn{position:fixed;left:16px;bottom:16px;z-index:9998;background:#38bdf8;color:#04202e;border:0;border-radius:99px;padding:9px 16px;font-weight:700;cursor:pointer;box-shadow:0 2px 10px rgba(0,0,0,.4)}',
    '#r3k-ov{position:fixed;inset:0;background:rgba(0,0,0,.65);z-index:99999;display:none;align-items:center;justify-content:center}',
    '#r3k-card{background:#121923;color:#e6edf3;border:1px solid #1f2a38;border-radius:14px;width:94vw;max-width:1000px;max-height:90vh;overflow:auto;padding:18px;font:14px/1.5 system-ui,sans-serif}',
    '#r3k-card h2{margin:0 0 4px;font-size:18px}',
    '#r3k-card .mut{color:#8b98a8;font-size:12px}',
    '#r3k-card .row{display:flex;gap:10px;flex-wrap:wrap;align-items:center;margin:10px 0}',
    '#r3k-card select,#r3k-card input[type=file]{background:#0b0f14;color:#e6edf3;border:1px solid #1f2a38;border-radius:8px;padding:6px}',
    '#r3k-card button{background:#38bdf8;color:#04202e;border:0;border-radius:8px;padding:8px 14px;font-weight:700;cursor:pointer}',
    '#r3k-card button.g{background:transparent;color:#e6edf3;border:1px solid #1f2a38;font-weight:500}',
    '#r3k-card button:disabled{opacity:.45;cursor:not-allowed}',
    '#r3k-bar{height:8px;background:#1f2a38;border-radius:99px;overflow:hidden}',
    '#r3k-bar i{display:block;height:100%;width:0;background:#38bdf8;transition:width .3s}',
    '.r3k-chip{padding:3px 12px;border-radius:99px;font-weight:700;color:#0b0f14}',
    '#r3k-tbl{width:100%;border-collapse:collapse;margin-top:10px;font-size:13px}',
    '#r3k-tbl th,#r3k-tbl td{border-bottom:1px solid #1f2a38;padding:6px 8px;text-align:left;vertical-align:top}',
    '.r3k-High{color:#ef4444;font-weight:700}.r3k-Medium{color:#f59e0b;font-weight:700}.r3k-Low{color:#22c55e;font-weight:700}'
  ].join('');
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var btn = document.createElement('button');
  btn.id = 'r3k-btn'; btn.textContent = '\uD83D\uDCCE Upload CSV';
  document.body.appendChild(btn);

  var ov = document.createElement('div');
  ov.id = 'r3k-ov';
  ov.innerHTML =
    '<div id="r3k-card">' +
      '<div class="row" style="justify-content:space-between;margin-top:0"><div><h2>Scan a file of messages</h2>' +
      '<div class="mut">CSV, TSV or TXT. Every row is checked on this device. Nothing is uploaded anywhere.</div></div>' +
      '<button class="g" id="r3k-x">Close</button></div>' +
      '<div class="row"><input type="file" id="r3k-file" accept=".csv,.tsv,.txt,text/csv,text/plain"></div>' +
      '<div class="row" id="r3k-opts" style="display:none">' +
        '<label>Message column <select id="r3k-col"></select></label>' +
        '<label>Mode <select id="r3k-mode"><option value="full">Thorough: rules + AI (slower)</option><option value="fast">Fast: rules only</option></select></label>' +
        '<label><input type="checkbox" id="r3k-hdr" checked> First row is a header</label>' +
        '<button id="r3k-go">Start</button><button class="g" id="r3k-stop" style="display:none">Stop</button>' +
      '</div>' +
      '<div class="mut" id="r3k-info"></div>' +
      '<div id="r3k-bar" style="display:none;margin-top:8px"><i></i></div>' +
      '<div class="row" id="r3k-sum"></div>' +
      '<div class="row" id="r3k-savebar" style="display:none"><button id="r3k-save">Save results file</button><span class="mut" id="r3k-saved"></span></div>' +
      '<div style="overflow-x:auto"><table id="r3k-tbl" style="display:none"><thead><tr><th>#</th><th>Message</th><th>Risk</th><th>Threat type</th><th>Score</th></tr></thead><tbody></tbody></table></div>' +
    '</div>';
  document.body.appendChild(ov);

  var $ = function (id) { return document.getElementById(id); };
  var esc = function (s) { return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var parsed = null, lastText = '', lastName = '', results = [], ctrl = null, running = false;

  function parseCSV(text) {
    if (text.charCodeAt(0) === 0xFEFF) text = text.slice(1);
    var first = text.split(/\r?\n/, 1)[0];
    var delim = ',', best = 0;
    [',', ';', '\t', '|'].forEach(function (d) { var c = first.split(d).length; if (c > best) { best = c; delim = d; } });
    var rows = [], row = [], cur = '', q = false;
    for (var i = 0; i < text.length; i++) {
      var ch = text.charAt(i);
      if (q) {
        if (ch === '"') { if (text.charAt(i + 1) === '"') { cur += '"'; i++; } else { q = false; } }
        else { cur += ch; }
      } else if (ch === '"') { q = true; }
      else if (ch === delim) { row.push(cur); cur = ''; }
      else if (ch === '\n') { row.push(cur); rows.push(row); row = []; cur = ''; }
      else if (ch !== '\r') { cur += ch; }
    }
    if (cur.length || row.length) { row.push(cur); rows.push(row); }
    return rows.filter(function (r) { return r.length > 1 || (r[0] && r[0].trim() !== ''); });
  }

  function guessCol(header, rows) {
    var names = ['message', 'text', 'content', 'body', 'sms', 'msg', 'description', 'incident', 'email', 'report'];
    for (var n = 0; n < names.length; n++) {
      for (var c = 0; c < header.length; c++) { if (String(header[c]).trim().toLowerCase() === names[n]) return c; }
    }
    var best = 0, bestLen = -1;
    for (var c2 = 0; c2 < header.length; c2++) {
      var tot = 0, k = Math.min(rows.length, 50);
      for (var r = 0; r < k; r++) tot += (rows[r][c2] || '').length;
      if (k && tot / k > bestLen) { bestLen = tot / k; best = c2; }
    }
    return best;
  }

  function build() {
    var isTxt = /\.txt$/i.test(lastName);
    var header, body;
    if (isTxt) {
      body = lastText.split(/\r?\n/).filter(function (l) { return l.trim(); }).map(function (l) { return [l]; });
      header = ['message'];
    } else {
      var all = parseCSV(lastText);
      if (!all.length) { parsed = null; $('r3k-info').textContent = 'That file looks empty.'; $('r3k-opts').style.display = 'none'; return; }
      var hasHdr = $('r3k-hdr').checked;
      header = hasHdr ? all[0] : all[0].map(function (_, i) { return 'Column ' + (i + 1); });
      body = hasHdr ? all.slice(1) : all;
    }
    parsed = { header: header, rows: body, name: lastName };
    var sel = $('r3k-col'); sel.innerHTML = '';
    header.forEach(function (h, i) { var o = document.createElement('option'); o.value = i; o.textContent = h || ('Column ' + (i + 1)); sel.appendChild(o); });
    sel.value = guessCol(header, body);
    $('r3k-opts').style.display = 'flex';
    $('r3k-info').textContent = lastName + ': ' + body.length + ' rows, ' + header.length + ' column(s). Pick the column that holds the message text, then press Start.';
  }

  function loadFile(file) {
    lastName = file.name;
    var fr = new FileReader();
    fr.onload = function () { lastText = String(fr.result || ''); build(); };
    fr.readAsText(file);
  }

  function setBar(p) { $('r3k-bar').style.display = 'block'; $('r3k-bar').firstChild.style.width = p + '%'; }

  function summary(counts, extra) {
    var col = { High: '#ef4444', Medium: '#f59e0b', Low: '#22c55e' };
    $('r3k-sum').innerHTML =
      ['High', 'Medium', 'Low'].map(function (k) { return '<span class="r3k-chip" style="background:' + col[k] + '">' + k + ' ' + counts[k] + '</span>'; }).join('') +
      '<span class="mut">' + esc(extra || '') + '</span>';
  }

  async function run() {
    if (!parsed || running) return;
    var col = +$('r3k-col').value;
    var texts = parsed.rows.map(function (r) { return r[col] || ''; });
    var total = texts.length, done = 0, t0 = Date.now();
    var counts = { High: 0, Medium: 0, Low: 0 };
    results = new Array(total);
    var tb = $('r3k-tbl').querySelector('tbody'); tb.innerHTML = ''; $('r3k-tbl').style.display = 'table';
    $('r3k-saved').textContent = ''; $('r3k-savebar').style.display = 'none';
    running = true; $('r3k-go').style.display = 'none'; $('r3k-stop').style.display = 'inline-block'; $('r3k-file').disabled = true;
    ctrl = new AbortController();
    summary(counts, '');
    try {
      var res = await fetch('/api/triage/batch', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ texts: texts, mode: $('r3k-mode').value }), signal: ctrl.signal
      });
      if (!res.ok) throw new Error('Server error ' + res.status);
      var reader = res.body.getReader(), dec = new TextDecoder(), buf = '';
      for (;;) {
        var x = await reader.read();
        if (x.done) break;
        buf += dec.decode(x.value, { stream: true });
        var nl;
        while ((nl = buf.indexOf('\n')) >= 0) {
          var line = buf.slice(0, nl).trim(); buf = buf.slice(nl + 1);
          if (!line) continue;
          var m; try { m = JSON.parse(line); } catch (e) { continue; }
          if (m.done) continue;
          done++;
          if (m.r && m.r.risk) {
            results[m.i] = m.r; counts[m.r.risk]++;
            if (m.i < 300) {
              var tr = document.createElement('tr');
              var why = Array.isArray(m.r.why) ? m.r.why.join(' | ') : m.r.why;
              tr.title = why + '\n\nWhat to do: ' + m.r.action;
              tr.innerHTML = '<td>' + (m.i + 1) + '</td><td>' + esc(String(texts[m.i]).slice(0, 110)) + '</td><td class="r3k-' + m.r.risk + '">' + m.r.risk + '</td><td>' + esc(m.r.threat_type) + '</td><td>' + m.r.score + '</td>';
              tb.appendChild(tr);
            }
          }
          var el = (Date.now() - t0) / 1000, left = done ? Math.round(el / done * (total - done)) : 0;
          setBar(Math.round(done / total * 100));
          summary(counts, done + '/' + total + (done < total ? '  |  about ' + (left >= 60 ? Math.round(left / 60) + ' min' : left + ' s') + ' left' : '  |  finished in ' + Math.round(el) + ' s'));
        }
      }
    } catch (e) {
      if (e.name !== 'AbortError') $('r3k-info').textContent = 'Stopped: ' + e.message;
    }
    running = false; $('r3k-go').style.display = 'inline-block'; $('r3k-stop').style.display = 'none'; $('r3k-file').disabled = false;
    if (total > 300) $('r3k-info').textContent = 'The table shows the first 300 rows. The saved file has all of them.';
    $('r3k-savebar').style.display = 'flex';
    save();
  }

  function save() {
    if (!parsed) return;
    var extra = ['r3kon_verdict', 'r3kon_threat_type', 'r3kon_risk', 'r3kon_score', 'r3kon_why', 'r3kon_action'];
    var rows = parsed.rows.map(function (row, i) {
      var r = results[i];
      var add = r ? [r.suspicious ? 'Suspicious' : 'Benign', r.threat_type, r.risk, r.score, Array.isArray(r.why) ? r.why.join(' | ') : r.why, r.action] : ['', '', '', '', '', ''];
      return row.concat(add);
    });
    fetch('/api/csv/save', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name: parsed.name.replace(/\.[^.]+$/, '') + '_r3kon', header: parsed.header.concat(extra), rows: rows })
    }).then(function (r) { return r.json(); }).then(function (j) {
      $('r3k-saved').textContent = j.path ? 'Saved: ' + j.path : ('Save failed: ' + (j.error || 'unknown'));
    }).catch(function (e) { $('r3k-saved').textContent = 'Save failed: ' + e.message; });
  }

  btn.onclick = function () { ov.style.display = 'flex'; };
  $('r3k-x').onclick = function () { if (ctrl && running) ctrl.abort(); ov.style.display = 'none'; };
  $('r3k-file').onchange = function () { if (this.files && this.files[0]) loadFile(this.files[0]); };
  $('r3k-hdr').onchange = function () { if (lastText) build(); };
  $('r3k-go').onclick = run;
  $('r3k-stop').onclick = function () { if (ctrl) ctrl.abort(); };
  $('r3k-save').onclick = save;
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && !running) ov.style.display = 'none'; });
})();
</script>
'''

assert "'''" not in MAIN_BLOCK and "'''" not in UI

m = open('main.py', encoding='utf-8').read()
if 'tri_classify' not in m:
    sys.exit('Run apply_triage.py first (main.py has no triage code yet).')
orig = m

# small fix: don't add the AI's "looks ordinary" sentence when the AI disagrees with the rules
OLD = 'if suspicious and l["why"] not in reasons:'
NEW = 'if suspicious and l.get("suspicious") and l["why"] not in reasons:'
if OLD in m:
    m = m.replace(OLD, NEW)
    print('main.py: fixed a mixed-up explanation when the AI and the rules disagree')

if 'api/triage/batch' in m:
    print('main.py already has the CSV routes - skipped')
else:
    b = m.index('def _analysis_route')
    m = m[:b] + MAIN_BLOCK.lstrip('\n') + '\n\n' + m[b:]
    print('main.py: CSV routes added')

if m != orig:
    shutil.copy('main.py', 'main.py.before-csv')
    open('main.py', 'w', encoding='utf-8').write(m)
    print('(backup: main.py.before-csv)')

h = open('index.html', encoding='utf-8').read()
if 'R3KON_CSV_UI' in h:
    print('index.html already patched - skipped')
else:
    shutil.copy('index.html', 'index.html.before-csv')
    i = h.rfind('</body>')
    h = (h[:i] + UI.lstrip('\n') + h[i:]) if i != -1 else (h + UI)
    open('index.html', 'w', encoding='utf-8').write(h)
    print('index.html: Upload CSV button added (backup: index.html.before-csv)')
