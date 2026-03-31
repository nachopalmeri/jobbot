import os

html_content = '''<!DOCTYPE html>
<html lang="es" class="scroll-smooth">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>JobBot | Automatiza tu búsqueda de trabajo</title>
  <meta name="description" content="JobBot escanea portales de empleo por ti y te notifica directamente en Telegram con las mejores ofertas.">
  
  <link rel="preconnect" href="https://fonts.googleapis.com" />
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
  
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/gsap.min.js"></script>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.2/ScrollTrigger.min.js"></script>

  <style>
    :root {
      --bg: #ffffff;
      --surface: #f8fafc;
      --border: #e2e8f0;
      --text: #0f172a;
      --text-muted: #64748b;
      --primary: #4f46e5;
      --primary-hover: #4338ca;
      --primary-light: #e0e7ff;
      --ease-smooth: cubic-bezier(0.25, 1, 0.5, 1);
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background-color: var(--bg);
      color: var(--text);
      font-family: 'Inter', system-ui, -apple-system, sans-serif;
      overflow-x: hidden;
      line-height: 1.6;
      -webkit-font-smoothing: antialiased;
    }

    .container { max-width: 1100px; margin: 0 auto; padding: 0 1.5rem; }

    nav {
      position: fixed; top: 0; left: 0; right: 0; z-index: 100;
      background: rgba(255, 255, 255, 0.85); backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border); transition: all 0.3s ease;
    }
    .nav-inner { display: flex; justify-content: space-between; align-items: center; height: 70px; }
    .logo { font-weight: 700; font-size: 1.25rem; color: var(--text); display: flex; align-items: center; gap: 0.5rem; text-decoration: none; letter-spacing: -0.02em; }
    .logo span { color: var(--primary); }
    .nav-links { display: flex; gap: 1.5rem; }
    .nav-link { color: var(--text-muted); text-decoration: none; font-weight: 500; font-size: 0.95rem; transition: color 0.2s; }
    .nav-link:hover { color: var(--text); }
    .btn { display: inline-flex; align-items: center; justify-content: center; gap: 0.5rem; padding: 0.75rem 1.5rem; font-weight: 600; font-size: 0.95rem; text-decoration: none; border-radius: 9999px; cursor: pointer; border: none; transition: all 0.2s var(--ease-smooth); }
    .btn-primary { background-color: var(--primary); color: #ffffff; box-shadow: 0 4px 14px -2px rgba(79, 70, 229, 0.4); }
    .btn-primary:hover { background-color: var(--primary-hover); transform: translateY(-2px); box-shadow: 0 6px 20px -4px rgba(79, 70, 229, 0.5); }

    .hero { padding: 180px 0 100px; text-align: center; position: relative; }
    .hero-badge { display: inline-block; padding: 0.5rem 1rem; background: var(--primary-light); color: var(--primary); border-radius: 9999px; font-size: 0.875rem; font-weight: 600; margin-bottom: 1.5rem; }
    .hero h1 { font-size: clamp(2.5rem, 6vw, 4rem); line-height: 1.15; font-weight: 800; color: var(--text); margin-bottom: 1.25rem; letter-spacing: -0.03em; max-width: 800px; margin-left: auto; margin-right: auto; }
    .hero p { font-size: clamp(1.125rem, 2vw, 1.25rem); color: var(--text-muted); margin-bottom: 2.5rem; max-width: 650px; margin-left: auto; margin-right: auto; }
    .hero-actions { display: flex; gap: 1rem; justify-content: center; align-items: center; }

    .features { padding: 100px 0; background-color: var(--surface); }
    .section-header { text-align: center; margin-bottom: 4rem; }
    .section-header h2 { font-size: clamp(2rem, 4vw, 2.5rem); font-weight: 700; margin-bottom: 1rem; letter-spacing: -0.02em; }
    .section-header p { color: var(--text-muted); font-size: 1.125rem; max-width: 600px; margin: 0 auto; }
    .grid-3 { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 2rem; }
    .feature-card { background: var(--bg); border: 1px solid var(--border); padding: 2.5rem; border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); transition: transform 0.3s var(--ease-smooth); }
    .feature-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08); }
    .icon-wrapper { width: 56px; height: 56px; background: var(--primary-light); color: var(--primary); border-radius: 12px; display: flex; align-items: center; justify-content: center; margin-bottom: 1.5rem; }
    .feature-card h3 { font-size: 1.25rem; font-weight: 700; margin-bottom: 0.75rem; }
    .feature-card p { color: var(--text-muted); font-size: 1rem; line-height: 1.6; }

    .dashboard-preview { padding: 100px 0; }
    .dash-box { background: var(--bg); border: 1px solid var(--border); border-radius: 1rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); padding: 2rem; }
    .input-group { display: flex; gap: 1rem; max-width: 500px; margin: 0 auto 3rem; }
    .input-group input { flex: 1; padding: 0.875rem 1.25rem; border-radius: 9999px; border: 1px solid var(--border); font-family: inherit; font-size: 1rem; outline: none; transition: border-color 0.2s; }
    .input-group input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px var(--primary-light); }
    .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 1.5rem; margin-bottom: 2rem; }
    .stat-card { text-align: center; padding: 1.5rem; background: var(--surface); border-radius: 0.75rem; border: 1px solid var(--border); }
    .stat-title { font-size: 0.875rem; color: var(--text-muted); text-transform: uppercase; font-weight: 600; letter-spacing: 0.05em; margin-bottom: 0.5rem; }
    .stat-value { font-size: 2.25rem; font-weight: 700; color: var(--text); }
    
    .charts-container { display: grid; grid-template-columns: 1fr; gap: 2rem; }
    table { width: 100%; border-collapse: collapse; text-align: left; }
    th { padding: 1rem; font-size: 0.875rem; color: var(--text-muted); font-weight: 600; border-bottom: 1px solid var(--border); background: var(--surface); }
    td { padding: 1.25rem 1rem; font-size: 0.95rem; border-bottom: 1px solid var(--border); }
    .badge { display: inline-block; padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }

    footer { background: var(--surface); padding: 3rem 0; text-align: center; border-top: 1px solid var(--border); color: var(--text-muted); }

    .spinner { animation: spin 1s linear infinite; }
    @keyframes spin { 100% {transform:rotate(360deg);} }

    @media (max-width: 768px) {
      .stats-grid { grid-template-columns: 1fr; }
      .input-group { flex-direction: column; }
      .input-group .btn { width: 100%; }
      .hero { padding: 140px 0 60px; }
      .nav-links { display: none; }
    }
  </style>
</head>

<body>

  <nav>
    <div class="container nav-inner">
      <a href="#" class="logo">
        <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><rect x="2" y="7" width="20" height="14" rx="2" ry="2"></rect><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"></path></svg>
        Job<span>Bot</span>
      </a>
      <div class="nav-links">
        <a href="#como-funciona" class="nav-link">Cómo funciona</a>
        <a href="#mi-panel" class="nav-link">Mi Panel</a>
      </div>
      <div>
        <a href="https://t.me/jobs912bot" class="btn btn-primary" style="padding: 0.6rem 1.25rem;">Probar Gratis</a>
      </div>
    </div>
  </nav>

  <section class="hero">
    <div class="container">
      <div class="hero-badge gs-fade">
        ?? Nuevo: Ahora con análisis de Inteligencia Artificial
      </div>
      <h1 class="gs-fade">Encuentra tu próximo empleo en piloto automático.</h1>
      <p class="gs-fade">No pierdas horas buscando ofertas. JobBot escanea los mejores portales, filtra según tu experiencia y te notifica las mejores oportunidades directamente en Telegram.</p>
      
      <div class="hero-actions gs-fade">
        <a href="https://t.me/jobs912bot" class="btn btn-primary">
          Empezar ahora en Telegram
        </a>
        <a href="#como-funciona" class="btn" style="background:var(--surface); color:var(--text); border:1px solid var(--border);">
          Saber más
        </a>
      </div>
    </div>
  </section>

  <section id="como-funciona" class="features">
    <div class="container">
      <div class="section-header gs-fade">
        <h2>Busca trabajo sin buscar trabajo</h2>
        <p>JobBot es tu asistente personal. Trabaja 24/7 para que tú solo tengas que preocuparte por las entrevistas.</p>
      </div>

      <div class="grid-3">
        <div class="feature-card gs-fade">
          <div class="icon-wrapper">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          </div>
          <h3>Monitoreo Continuo</h3>
          <p>Scanea continuamente LinkedIn, Remotive, Jobicy y más. Encontramos la oferta en los primeros minutos de publicación para que seas el primero en aplicar.</p>
        </div>

        <div class="feature-card gs-fade">
          <div class="icon-wrapper">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z"></path></svg>
          </div>
          <h3>Avisos por Telegram</h3>
          <p>Recibe notificaciones en tu celular al instante. Solo las ofertas que de verdad encajan contigo, sin spam. Te avisamos cuándo y dónde postularte.</p>
        </div>

        <div class="feature-card gs-fade">
          <div class="icon-wrapper">
            <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"></rect><path d="M7 11V7a5 5 0 0 1 10 0v4"></path></svg>
          </div>
          <h3>Privado y Seguro</h3>
          <p>Tus datos siempre protegidos. Nosotros solo gestionamos la búsqueda para que tú tengas el control total de dónde enviar tu información profesional.</p>
        </div>
      </div>
    </div>
  </section>

  <section id="mi-panel" class="dashboard-preview">
    <div class="container">
      <div class="section-header gs-fade">
        <h2>Mi Panel</h2>
        <p>Mide tu éxito. Ingresa tu ID de Telegram para revisar el estado de todas tus postulaciones.</p>
      </div>

      <div class="input-group gs-fade">
        <input type="text" id="tid-input" placeholder="Tu ID de Telegram (Ej: 12345678)" />
        <button id="tid-submit" class="btn btn-primary">Ver mis datos</button>
      </div>

      <div id="dashboard-error" style="color:#ef4444; background:#fef2f2; border:1px solid #fecaca; text-align:center; margin-bottom:2rem; display:none; padding:1rem; border-radius:0.75rem;"></div>

      <div id="dashboard-content" style="display:none;">
        <div class="stats-grid">
          <div class="stat-card">
             <div class="stat-title">Nivel de Perfil</div>
             <div id="d-level" class="stat-value">--</div>
          </div>
          <div class="stat-card">
             <div class="stat-title">Posición</div>
             <div id="d-role" class="stat-value" style="color:var(--primary);">--</div>
          </div>
          <div class="stat-card">
             <div class="stat-title">Ofertas Guardadas</div>
             <div id="d-apps" class="stat-value">--</div>
          </div>
        </div>

        <div class="charts-container">
          <div class="dash-box">
            <h3 style="margin-bottom:1.5rem; font-size:1.125rem;">Avance de Entrevistas</h3>
            <div style="height:300px; width:100%;">
              <canvas id="funnelChart"></canvas>
            </div>
          </div>

          <div class="dash-box" style="padding:0; overflow:hidden;">
            <div style="overflow-x:auto;">
              <table>
                <thead>
                  <tr>
                    <th>Empresa</th>
                    <th>Posición</th>
                    <th>Estado</th>
                    <th>Actualizado</th>
                  </tr>
                </thead>
                <tbody id="d-table-body">
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <footer>
    <div class="container">
      <p>&copy; 2026 JobBot. Creado para ayudarte a crecer.</p>
    </div>
  </footer>

  <script>
    gsap.registerPlugin(ScrollTrigger);
    
    gsap.utils.toArray('.gs-fade').forEach(function(elem, i) {
      gsap.fromTo(elem, 
        { y: 20, opacity: 0 },
        { 
          scrollTrigger: { trigger: elem, start: "top 90%" },
          y: 0, opacity: 1, duration: 0.8, ease: "power2.out",
          delay: elem.closest('.hero') ? i * 0.15 : 0 
        }
      );
    });

    let chartInstance = null;
    const tidSubmit = document.getElementById('tid-submit');
    if (tidSubmit) {
      tidSubmit.addEventListener('click', async () => {
        const tid = document.getElementById('tid-input').value.trim();
        const errEl = document.getElementById('dashboard-error');
        const contentEl = document.getElementById('dashboard-content');
        const btn = document.getElementById('tid-submit');
        
        if(!tid) return;
        
        errEl.style.display = 'none';
        btn.innerHTML = \<svg class="spinner" width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="12" y1="2" x2="12" y2="6"></line><line x1="12" y1="18" x2="12" y2="22"></line><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line><line x1="2" y1="12" x2="6" y2="12"></line><line x1="18" y1="12" x2="22" y2="12"></line><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line></svg> Buscando...\;
        
        try {
          const res = await fetch(\http://127.0.0.1:8080/api/dashboard?telegram_id=\\);
          if (!res.ok) throw new Error('No pudimos encontrar tu cuenta. Asegúrate de haber interactuado con el bot primero.');
          const data = await res.json();
          
          document.getElementById('d-level').textContent = data.user_level || 'General';
          document.getElementById('d-role').textContent = data.user_role || 'No definido';
          document.getElementById('d-apps').textContent = data.applications ? data.applications.length : 0;
          
          const ctx = document.getElementById('funnelChart').getContext('2d');
          if(chartInstance) chartInstance.destroy();
          
          chartInstance = new Chart(ctx, {
              type: 'bar',
              data: {
                  labels: ['Interesado', 'Entrevistas', 'No seleccionado', 'Ofertas'],
                  datasets: [{
                      label: 'Postulaciones',
                      data: [data.funnel.applied, data.funnel.interview, data.funnel.rejected, data.funnel.offer],
                      backgroundColor: ['rgba(99, 102, 241, 0.2)', 'rgba(245, 158, 11, 0.2)', 'rgba(239, 68, 68, 0.2)', 'rgba(16, 185, 129, 0.2)'],
                      borderColor: ['#6366f1', '#f59e0b', '#ef4444', '#10b981'],
                      borderWidth: 2, borderRadius: 6
                  }]
              },
              options: {
                  responsive: true, maintainAspectRatio: false,
                  plugins: { legend: { display: false } },
                  scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } }, x: { grid: { display: false } } }
              }
          });
          
          const tbody = document.getElementById('d-table-body');
          tbody.innerHTML = '';
          
          if (!data.applications || data.applications.length === 0) {
              tbody.innerHTML = '<tr><td colspan="4" style="text-align:center; color:#64748b;">Aún no tienes postulaciones registradas.</td></tr>';
          } else {
              data.applications.forEach(app => {
                  let badge = '';
                  let txt = app.status;
                  if(app.status === 'oferta') badge = 'background:#d1fae5; color:#047857;';
                  else if(app.status === 'entrevista') badge = 'background:#fef3c7; color:#b45309;';
                  else if(app.status === 'rechazado') badge = 'background:#fee2e2; color:#b91c1c;';
                  else { badge = 'background:#e0e7ff; color:#4338ca;'; txt = 'interesado'; }
                  const dStr = app.created_at ? new Date(app.created_at).toLocaleDateString() : '';
                  
                  const tr = document.createElement('tr');
                  tr.innerHTML = \<td style="font-weight:500; color:#0f172a;">\</td><td style="color:#475569;">\</td><td><span class="badge" style="\">\</span></td><td style="color:#64748b; font-size:0.875rem;">\</td>\;
                  tbody.appendChild(tr);
              });
          }
          
          contentEl.style.display = 'block';
          gsap.fromTo(contentEl, {opacity: 0, y: 20}, {opacity: 1, y: 0, duration: 0.5});
          
        } catch(e) {
           errEl.style.display = 'block'; errEl.textContent = e.message;
        } finally {
           btn.innerHTML = 'Ver mis datos';
        }
      });
    }
  </script>
</body>
</html>'''

with open(r'C:\Users\nacho\Downloads\jobobt\jobbot\job_bot\landing\index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print("¡Escritura completada exitosamente con codificación UTF-8!")
