// Se ejecuta (con javascript_tool) en una pestaña ya abierta de cualquier jornada de
// https://ffcm.es/pnfg/NPcd/NFG_CmpJornada?...CodGrupo=23243204...
// Carga las jornadas indicadas en iframes ocultos del mismo dominio y devuelve los
// marcadores tal como se VEN en pantalla. La web oculta los dígitos reales con CSS/JS
// y mete números falsos en <span style="display:none">, así que se calcula el texto
// visible (incluyendo ::before/::after y respetando display:none).
// Uso: cambiar JORNADAS y ejecutar. Devuelve JSON con una lista de partidos.
const JORNADAS = [1, 2, 3, 4, 5, 6];

const cargar = (j) => new Promise((res) => {
  const f = document.createElement('iframe');
  f.style.cssText = 'width:1200px;height:3000px;position:absolute;left:-5000px;top:0';
  f.src = location.href.replace(/CodJornada=\d+/, 'CodJornada=' + j);
  f.onload = () => setTimeout(() => {
    const d = f.contentDocument, w = f.contentWindow;
    const vis = (el) => {
      if (el.nodeType === 3) return el.textContent;
      if (el.nodeType !== 1) return '';
      const cs = w.getComputedStyle(el);
      if (cs.display === 'none' || cs.visibility === 'hidden' || el.tagName === 'SCRIPT' || el.tagName === 'STYLE') return '';
      const pc = (p) => {
        const ps = w.getComputedStyle(el, p);
        const c = ps.content;
        if (!c || c === 'none' || c === 'normal' || ps.display === 'none' || ps.visibility === 'hidden') return '';
        return c.replace(/^"|"$/g, '');
      };
      let s = pc('::before');
      for (const ch of el.childNodes) s += vis(ch);
      return s + pc('::after');
    };
    const out = [];
    d.querySelectorAll('#divResultados_ table table').forEach((t) => {
      const tds = t.querySelectorAll(':scope > tbody > tr:first-child > td');
      if (tds.length < 3) return;
      const sc = [...tds[1].querySelectorAll('span.wid2_resultado_cerrada')].map((s) => vis(s).replace(/[^0-9]/g, ''));
      const horarios = [...tds[1].querySelectorAll('.horario')].map((x) => x.innerText.trim());
      const campoEl = t.querySelector('tr:nth-child(2) a[href*="NFG_VisCampos"]');
      out.push({
        j,
        local: tds[0].innerText.trim(),
        visitante: tds[2].innerText.trim(),
        marcador: sc.length === 2 && sc[0] !== '' && sc[1] !== '' ? sc.join('-') : '',
        fecha: horarios.find((h) => /\d\d-\d\d-\d{4}/.test(h)) || '',
        hora: horarios.find((h) => /^\d\d:\d\d$/.test(h)) || '',
        campo: campoEl ? campoEl.innerText.trim() : '',
        acta: !!tds[1].querySelector('a[title="Acta del partido"]'),
        retirado: !!t.querySelector('.fa-times-circle'),
      });
    });
    f.remove();
    res(out);
  }, 1500);
  document.body.appendChild(f);
});

const todos = [];
for (const j of JORNADAS) todos.push(...(await cargar(j)));
JSON.stringify(todos);
