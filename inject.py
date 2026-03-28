import io

file_path = r'C:\Users\nacho\Downloads\jobobt\jobbot\job_bot\landing\index.html'
with io.open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Inyectar Chart.js en el head
if '<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>' not in content:
    content = content.replace('</head>', '  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>\n</head>')

# Añadir Dashboard en el Nav
nav_str = '<div class="nav-logo">Job<span>Bot</span>.ar</div>'
nav_replace = nav_str + '''
      <div style="margin-left:30px; display:flex; align-items:center;">
         <a href="#dashboard" style="color:var(--green); text-decoration:none; font-weight:bold; font-size:14px; background: rgba(0, 255, 136, 0.1); padding: 5px 12px; border-radius: 6px;">Ver EstadÃsticas</a>
      </div>
'''
if 'Ver EstadÃsticas' not in content:
    content = content.replace(nav_str, nav_replace)

# Extraer el HTML de la sección
dashboard_section = '''
  <!-- DASHBOARD -->
  <section id="dashboard" style="padding: 100px 0; background: var(--bg); border-top: 1px solid var(--border);">
    <div class="container">
      <div class="section-tag">// mÃ©tricas personales</div>
      <h2 class="section-title">Tu <span style="color:var(--green)">Dashboard</span></h2>
      <p class="section-desc">IngresÃ¡ tu Telegram ID para ver el estado de tus postulaciones y funnel de conversiÃ³n en tiempo real.</p>
      
      <div style="margin-bottom: 40px; display:flex; gap:10px; max-width: 500px; margin-left:auto; margin-right:auto; justify-content:center;">
        <input type="text" id="tid-input" placeholder="Tu Telegram ID (ej: 123456)" style="padding:12px 20px; border-radius:8px; border:1px solid var(--border); background:var(--surface); color:var(--text); width:100%; font-family:'JetBrains Mono', monospace; font-size:16px; outline:none;" />
        <button id="tid-submit" class="btn-primary" style="cursor:pointer; border:none; padding:12px 24px;">Cargar Datos</button>
      </div>
      
      <div id="dashboard-error" style="color:var(--red); text-align:center; margin-bottom:20px; display:none; font-size:16px;"></div>
      
      <div id="dashboard-content" style="display:none;">
        <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-bottom: 40px;">
          <div style="background:var(--surface); border:1px solid var(--border); padding:24px; border-radius:12px; text-align:center;">
            <div style="color:var(--text-muted); font-size:14px; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px;">Nivel</div>
            <div id="d-level" style="font-size:32px; font-weight:bold; color:var(--green);">--</div>
          </div>
          <div style="background:var(--surface); border:1px solid var(--border); padding:24px; border-radius:12px; text-align:center;">
            <div style="color:var(--text-muted); font-size:14px; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px;">Rol Activo</div>
            <div id="d-role" style="font-size:24px; font-weight:bold; color:var(--green);">--</div>
          </div>
          <div style="background:var(--surface); border:1px solid var(--border); padding:24px; border-radius:12px; text-align:center;">
            <div style="color:var(--text-muted); font-size:14px; margin-bottom:10px; text-transform:uppercase; letter-spacing:1px;">Postulaciones</div>
            <div id="d-apps" style="font-size:32px; font-weight:bold; color:var(--green);">--</div>
          </div>
        </div>
        
        <div style="display: grid; grid-template-columns: 1fr; gap: 40px; margin-bottom: 40px;">
            <div style="background:var(--surface); border:1px solid var(--border); padding:24px; border-radius:12px;">
                <h3 style="margin-bottom:20px; font-size:18px; color:var(--text); font-family:'Syne', sans-serif;">Funnel de ConversiÃ³n</h3>
                <div style="position: relative; height: 300px; width: 100%;">
                <canvas id="funnelChart"></canvas>
                </div>
            </div>
            
            <div style="background:var(--surface); border:1px solid var(--border); border-radius:12px; overflow:hidden;">
                <h3 style="padding:24px; margin:0; font-size:18px; color:var(--text); font-family:'Syne', sans-serif; border-bottom:1px solid var(--border);">Status de Aplicaciones</h3>
                <div style="overflow-x:auto;">
                <table style="width:100%; border-collapse:collapse; text-align:left;">
                    <thead>
                    <tr style="background:#161B22; color:var(--text-muted); font-family:'Syne', sans-serif; font-size:14px;">
                        <th style="padding:16px 24px; font-weight:600; border-bottom:1px solid var(--border);">Empresa</th>
                        <th style="padding:16px 24px; font-weight:600; border-bottom:1px solid var(--border);">Puesto</th>
                        <th style="padding:16px 24px; font-weight:600; border-bottom:1px solid var(--border);">Estado</th>
                        <th style="padding:16px 24px; font-weight:600; border-bottom:1px solid var(--border);">Fecha</th>
                    </tr>
                    </thead>
                    <tbody id="d-table-body" style="font-size: 14px;">
                    <!-- JS Fills Here -->
                    </tbody>
                </table>
                </div>
            </div>
        </div>
      </div>
    </div>
  </section>
'''

if '<!-- DASHBOARD -->' not in content:
    content = content.replace('<section style="padding-top:0" id="pro">', dashboard_section + '\n  <section style="padding-top:0" id="pro">')
else:
    print('Dashboard section already in content')

js_logic = '''
    // DASHBOARD LOGIC
    let chartInstance = null;
    const tidSubmit = document.getElementById('tid-submit');
    if (tidSubmit) {
        tidSubmit.addEventListener('click', async () => {
          const tid = document.getElementById('tid-input').value.trim();
          const errEl = document.getElementById('dashboard-error');
          const contentEl = document.getElementById('dashboard-content');
          
          if(!tid) return;
          
          errEl.style.display = 'none';
          
          try {
            const res = await fetch(`http://127.0.0.1:8080/api/dashboard?telegram_id=${tid}`);
            if (!res.ok) throw new Error('Usuario no encontrado o no tiene datos procesados.');
            const data = await res.json();
            
            document.getElementById('d-level').textContent = data.user_level || '--';
            document.getElementById('d-role').textContent = data.user_role || 'No definido';
            document.getElementById('d-apps').textContent = data.applications ? data.applications.length : 0;
            
            // Render Chart
            const ctx = document.getElementById('funnelChart').getContext('2d');
            if(chartInstance) chartInstance.destroy();
            
            chartInstance = new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: ['Aplicados', 'Entrevistas', 'Rechazados', 'Ofertas'],
                    datasets: [{
                        label: 'Postulaciones',
                        data: [data.funnel.applied, data.funnel.interview, data.funnel.rejected, data.funnel.offer],
                        backgroundColor: [
                            'rgba(0, 255, 136, 0.2)',
                            'rgba(255, 179, 0, 0.2)',
                            'rgba(255, 71, 87, 0.2)',
                            'rgba(0, 212, 255, 0.2)'
                        ],
                        borderColor: [
                            '#00ff88',
                            '#ffb300',
                            '#ff4757',
                            '#00d4ff'
                        ],
                        borderWidth: 1,
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: { display: false }
                    },
                    scales: {
                        y: { beginAtZero: true, ticks: { color: '#6e7681', stepSize: 1 }, grid: { color: '#1c2733' } },
                        x: { ticks: { color: '#c9d1d9' }, grid: { display: false } }
                    }
                }
            });
            
            // Render Table
            const tbody = document.getElementById('d-table-body');
            tbody.innerHTML = '';
            
            if (!data.applications || data.applications.length === 0) {
                tbody.innerHTML = '<tr><td colspan="4" style="padding:24px; text-align:center; color:var(--text-muted);">No hay postulaciones aÃºn</td></tr>';
            } else {
                data.applications.forEach(app => {
                    let badgeColor = '';
                    let badgeBg = '';
                    let statusTxt = app.status;
                    if(app.status === 'oferta') {badgeColor = '#00ff88'; badgeBg='rgba(0,255,136,0.1)';}
                    else if(app.status === 'entrevista') {badgeColor = '#ffb300'; badgeBg='rgba(255,179,0,0.1)';}
                    else if(app.status === 'rechazado') {badgeColor = '#ff4757'; badgeBg='rgba(255,71,87,0.1)';}
                    else {badgeColor = '#00d4ff'; badgeBg='rgba(0,212,255,0.1)'; statusTxt='aplicado';}
                    
                    const tr = document.createElement('tr');
                    tr.style.borderBottom = '1px solid var(--border)';
                    
                    const dateStr = app.created_at ? new Date(app.created_at).toLocaleDateString() : '';
                    
                    tr.innerHTML = `
                      <td style="padding:16px 24px;">${app.company || 'N/A'}</td>
                      <td style="padding:16px 24px;">${app.job_title || 'N/A'}</td>
                      <td style="padding:16px 24px;">
                        <span style="color:${badgeColor}; background:${badgeBg}; padding:4px 10px; border-radius:20px; font-size:12px; font-weight:600; text-transform:uppercase;">${statusTxt}</span>
                      </td>
                      <td style="padding:16px 24px; color:var(--text-muted);">${dateStr}</td>
                    `;
                    tbody.appendChild(tr);
                });
            }
            
            contentEl.style.display = 'block';
            
          } catch(e) {
             errEl.style.display = 'block';
             errEl.textContent = e.message;
          }
        });
    }
'''

if '// DASHBOARD LOGIC' not in content:
    content = content.replace('    })();\n  </script>', '    })();\n' + js_logic + '\n  </script>')
else:
    print('JS logic already in content')


with io.open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('Injection script finalized')
