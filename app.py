from pathlib import Path

import tensorflow as tf
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

MODEL_PATH = Path(__file__).parent / "spam_detector.keras"
model = tf.keras.models.load_model(MODEL_PATH)

app = FastAPI(title="Scam Shield", description="SMS spam and scam detector")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class Msg(BaseModel):
    text: str = Field(..., min_length=1, max_length=1000)


HTML = r"""
<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Scam Shield</title>
<style>
:root{--accent:#8b5cf6;--accent2:#06b6d4}
*{box-sizing:border-box;margin:0;padding:0;font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif}
body{min-height:100vh;color:#fff;padding:20px 14px 40px;
background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);background-size:300% 300%;
animation:bg 14s ease infinite;overflow-x:hidden}
@keyframes bg{0%{background-position:0 50%}50%{background-position:100% 50%}100%{background-position:0 50%}}
.blob{position:fixed;border-radius:50%;filter:blur(80px);opacity:.45;z-index:0;
background:var(--accent);transition:background .8s}
.b1{width:260px;height:260px;top:-60px;left:-60px}
.b2{width:300px;height:300px;bottom:-80px;right:-80px;background:var(--accent2)}
.wrap{position:relative;z-index:1;max-width:520px;margin:0 auto}
h1{text-align:center;font-size:28px;font-weight:800;letter-spacing:.5px}
h1 span{background:linear-gradient(90deg,var(--accent),var(--accent2));
-webkit-background-clip:text;background-clip:text;color:transparent}
.sub{text-align:center;opacity:.7;font-size:14px;margin:6px 0 18px}
.card{background:rgba(255,255,255,.08);backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
border:1px solid rgba(255,255,255,.18);border-radius:24px;padding:18px;margin-bottom:16px;
box-shadow:0 10px 40px rgba(0,0,0,.35)}
textarea{width:100%;height:120px;resize:none;border-radius:16px;border:1px solid rgba(255,255,255,.2);
background:rgba(0,0,0,.25);color:#fff;padding:14px;font-size:16px;outline:none;transition:.3s}
textarea:focus{border-color:var(--accent);box-shadow:0 0 0 3px color-mix(in srgb,var(--accent) 35%,transparent)}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.chip{font-size:13px;padding:8px 12px;border-radius:999px;cursor:pointer;
background:rgba(255,255,255,.1);border:1px solid rgba(255,255,255,.2);transition:.2s}
.chip:active{transform:scale(.95)}
button.go{width:100%;padding:15px;border:0;border-radius:16px;font-size:17px;font-weight:700;color:#fff;cursor:pointer;
background:linear-gradient(90deg,var(--accent),var(--accent2));transition:.3s;box-shadow:0 6px 20px rgba(0,0,0,.35)}
button.go:active{transform:scale(.98)}
button.go:disabled{opacity:.6}
.res{display:none;text-align:center}
.gauge{position:relative;width:190px;height:190px;margin:4px auto 8px}
.gauge svg{transform:rotate(-90deg)}
.gauge .bg{stroke:rgba(255,255,255,.12)}
.gauge .fg{stroke:var(--accent);stroke-linecap:round;stroke-dasharray:326.7;stroke-dashoffset:326.7;
transition:stroke-dashoffset 1.2s cubic-bezier(.2,.8,.2,1),stroke .6s;filter:drop-shadow(0 0 8px var(--accent))}
.gauge .num{position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center}
.num b{font-size:40px}.num small{opacity:.7;font-size:12px}
.verdict{font-size:26px;font-weight:800;color:var(--accent);transition:color .6s}
.advice{opacity:.85;font-size:14px;margin-top:6px;line-height:1.5}
h3{font-size:15px;margin-bottom:10px;opacity:.85}
svg.chart{width:100%;height:120px}
.row{display:flex;gap:8px;align-items:center;font-size:13px;padding:8px 0;border-top:1px solid rgba(255,255,255,.1)}
.dot{width:10px;height:10px;border-radius:50%;flex:none}
.row .t{flex:1;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;opacity:.9}
.row .p{font-weight:700}
.foot{text-align:center;font-size:12px;opacity:.5;margin-top:10px}
</style></head>
<body>
<div class="blob b1"></div><div class="blob b2"></div>
<div class="wrap">
  <h1>🛡️ <span>Scam Shield</span></h1>
  <p class="sub">Paste any SMS. AI tells you if it is a scam.</p>

  <div class="card">
    <textarea id="msg" placeholder="Paste your SMS message here..."></textarea>
    <div class="chips">
      <div class="chip" data-t="Congratulations! You won a free iPhone. Click this link to claim now">🎁 Prize scam</div>
      <div class="chip" data-t="URGENT: your bank account is blocked, send your PIN to verify">🏦 Bank scam</div>
      <div class="chip" data-t="Bro are you coming to the wedding tomorrow?">💬 Normal chat</div>
    </div>
    <button class="go" id="btn">Check Message</button>
  </div>

  <div class="card res" id="res">
    <div class="gauge">
      <svg width="190" height="190" viewBox="0 0 120 120">
        <circle class="bg" cx="60" cy="60" r="52" fill="none" stroke-width="10"/>
        <circle class="fg" id="fg" cx="60" cy="60" r="52" fill="none" stroke-width="10"/>
      </svg>
      <div class="num"><b id="pct">0%</b><small>spam chance</small></div>
    </div>
    <div class="verdict" id="verdict"></div>
    <div class="advice" id="advice"></div>
  </div>

  <div class="card" id="histCard" style="display:none">
    <h3>📈 Your recent checks</h3>
    <svg class="chart" id="chart" viewBox="0 0 300 100" preserveAspectRatio="none"></svg>
    <div id="list"></div>
  </div>
  <p class="foot">Built with TensorFlow, Keras and FastAPI</p>
</div>

<script>
const $ = id => document.getElementById(id);
const hist = [];
const GREEN = ["#22c55e","#06b6d4"], RED = ["#ef4444","#f97316"];

document.querySelectorAll(".chip").forEach(c =>
  c.onclick = () => { $("msg").value = c.dataset.t; analyze(); });
$("btn").onclick = analyze;

function setTheme(c){
  document.documentElement.style.setProperty("--accent", c[0]);
  document.documentElement.style.setProperty("--accent2", c[1]);
}

function countUp(el, to){
  const start = performance.now();
  (function step(now){
    const k = Math.min((now - start) / 1000, 1);
    el.textContent = Math.round(to * k) + "%";
    if (k < 1) requestAnimationFrame(step);
  })(start);
}

async function analyze(){
  const text = $("msg").value.trim();
  if (!text) { $("msg").focus(); return; }
  $("btn").disabled = true; $("btn").textContent = "Analyzing...";
  try {
    const r = await fetch("/predict", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({text})
    });
    if (!r.ok) throw new Error("Server returned " + r.status);
    show(await r.json(), text);
  } catch(e) { alert("Error: " + e.message); }
  $("btn").disabled = false; $("btn").textContent = "Check Message";
}

function show(d, text){
  const p = d.spam_probability, spam = d.label === "SPAM";
  setTheme(spam ? RED : GREEN);
  $("res").style.display = "block";
  $("fg").style.strokeDashoffset = 326.7;
  setTimeout(() => $("fg").style.strokeDashoffset = 326.7 * (1 - p), 50);
  countUp($("pct"), p * 100);
  $("verdict").textContent = spam ? "⚠️ SPAM / SCAM" : "✅ SAFE MESSAGE";
  $("advice").textContent = spam
    ? "Do not click any link, do not share PIN, OTP or passwords. Delete and block the sender."
    : "This message looks normal. Still stay careful with unknown links.";
  hist.push({p, text, spam});
  if (hist.length > 8) hist.shift();
  drawChart(); drawList();
  $("res").scrollIntoView({behavior: "smooth", block: "center"});
}

function drawChart(){
  $("histCard").style.display = "block";
  const n = hist.length, svg = $("chart");
  const xs = hist.map((_, i) => n === 1 ? 150 : 10 + i * (280 / (n - 1)));
  const ys = hist.map(h => 90 - h.p * 78);
  const col = getComputedStyle(document.documentElement).getPropertyValue("--accent");
  let html = `<defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${col}" stop-opacity=".5"/>
    <stop offset="1" stop-color="${col}" stop-opacity="0"/></linearGradient></defs>
    <line x1="0" y1="50" x2="300" y2="50" stroke="rgba(255,255,255,.15)" stroke-dasharray="4"/>`;
  if (n > 1){
    let d = `M${xs[0]},${ys[0]}`;
    for (let i = 1; i < n; i++){
      const cx = (xs[i-1] + xs[i]) / 2;
      d += ` C${cx},${ys[i-1]} ${cx},${ys[i]} ${xs[i]},${ys[i]}`;
    }
    html += `<path d="${d} L${xs[n-1]},100 L${xs[0]},100 Z" fill="url(#g)"/>
             <path d="${d}" fill="none" stroke="${col}" stroke-width="2.5" stroke-linecap="round"/>`;
  }
  xs.forEach((x, i) => html += `<circle cx="${x}" cy="${ys[i]}" r="4"
    fill="${hist[i].spam ? '#ef4444' : '#22c55e'}" stroke="#fff" stroke-width="1.5"/>`);
  svg.innerHTML = html;
}

function drawList(){
  const box = $("list"); box.innerHTML = "";
  hist.slice().reverse().forEach(h => {
    const row = document.createElement("div"); row.className = "row";
    const dot = document.createElement("div"); dot.className = "dot";
    dot.style.background = h.spam ? "#ef4444" : "#22c55e";
    const t = document.createElement("div"); t.className = "t"; t.textContent = h.text;
    const p = document.createElement("div"); p.className = "p";
    p.textContent = Math.round(h.p * 100) + "%";
    row.append(dot, t, p); box.appendChild(row);
  });
}
</script>
</body></html>
"""


@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/predict")
def predict(m: Msg):
    x = tf.constant([m.text], dtype=tf.string)
    p = float(model(x, training=False).numpy()[0][0])
    return {"spam_probability": round(p, 4),
            "label": "SPAM" if p > 0.5 else "SAFE"}
