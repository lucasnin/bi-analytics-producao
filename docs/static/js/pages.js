(() => {
  const currency = value => money.format(Number(value || 0));
  const percent = value => `${Number(value || 0).toFixed(1).replace('.', ',')}%`;
  const total = (rows, key) => (rows || []).reduce((sum, row) => sum + Number(row[key] || 0), 0);
  const conversion = rows => { const inserted=total(rows,'inserted'), integrated=total(rows,'integrated'); return inserted ? integrated/inserted*100 : 0; };
  const metricCard = (label, value, note, tone='blue') => `<article class="pro-card ${tone}"><span>${label}</span><strong>${value}</strong><small>${note}</small></article>`;
  const performanceRows = rows => (rows || []).slice(0,100).map((row,index)=>`<div class="performance-row"><span class="entity"><b>${index+1}</b>${escapeHtml(row.label)}</span><span>${number.format(row.contracts)}</span><strong>${currency(row.inserted)}</strong><span>${number.format(row.paid)}</span><strong class="paid">${currency(row.integrated)}</strong><span class="conversion"><b>${percent(row.conversion)}</b><i><u style="width:${Math.min(100,row.conversion)}%"></u></i></span></div>`).join('');
  const performanceTable = (title, rows, entity='Operador') => `<section class="pro-panel"><div class="pro-title"><div><span>PERFORMANCE</span><h3>${title}</h3></div><small>${number.format((rows||[]).length)} registros</small></div><div class="performance-row performance-head"><span>${entity}</span><span>Propostas</span><span>Inserido</span><span>Pagos</span><span>Integrado</span><span>Conversão</span></div><div class="performance-body">${performanceRows(rows)}</div></section>`;
  const ranking = (title, rows, key='integrated') => `<section class="pro-panel compact"><div class="pro-title"><h3>${title}</h3></div>${(rows||[]).slice(0,10).map((row,index)=>`<div class="pro-rank"><b>${index+1}</b><span>${escapeHtml(row.label)}</span><strong>${currency(row[key])}</strong><i><u style="width:${Math.min(100,(Number(row[key]||0)/Math.max(1,Number(rows[0]?.[key]||1))*100))}%"></u></i></div>`).join('')}</section>`;
  window.renderAnalysisPage = page => {
    const analysis=document.querySelector('#analysis-page');
    const dashboardSections=['#kpis','#status-kpis','.charts-grid','.team-chart-panel','.monthly-panel','.story-panel','.bottom-grid','.ai-panel'];
    dashboardSections.forEach(selector=>{const element=document.querySelector(selector);if(element)element.hidden=page!=='dashboard'});
    analysis.hidden=page==='dashboard'; if(page==='dashboard') return;
    const data=dashboard.analytics||{}, month=dashboard.monthly.at(-1), factor=month?.integrated?month.projection/month.integrated:1;
    const titles={production:'Produção',integrated:'Pagos / Integrados',teams:'Equipes',operators:'Operadores',managements:'Gerências',projection:'Projeção',comparisons:'Comparativos'};
    let content='';
    if(page==='operators'){
      const rows=data.operator||[];
      content=`<div class="page-cards">${metricCard('Total inserido',currency(total(rows,'inserted')),'Data de cadastro')}${metricCard('Valor integrado',currency(total(rows,'integrated')),'Data de integração','green')}${metricCard('Contratos pagos',number.format(total(rows,'paid')),'Propostas integradas','cyan')}${metricCard('Conversão',percent(conversion(rows)),'Integrado ÷ inserido','purple')}</div>${performanceTable('Visão por operador',rows,'Operador')}`;
    } else if(page==='integrated'){
      const rows=data.agreement||[], daily=dashboard.daily.at(-1);
      content=`<div class="page-cards">${metricCard('Integrado no período',currency(total(rows,'integrated')),'Status Integrado','green')}${metricCard('Contratos pagos',number.format(total(rows,'paid')),'Quantidade integrada','cyan')}${metricCard('Conversão geral',percent(conversion(rows)),'Integrado ÷ inserido','purple')}${metricCard('Último dia',currency(daily?.value),'Movimento diário')}</div><div class="ranking-grid">${ranking('Integrado por convênio',data.agreement)}${ranking('Integrado por gerência',data.manual_management)}${ranking('Integrado por operador',data.operator)}${ranking('Modalidades em destaque',data.modality)}</div>`;
    } else if(page==='managements'){
      const rows=data.manual_management||[];
      content=`<div class="page-cards">${metricCard('Produção inserida',currency(total(rows,'inserted')),'Todas as gerências')}${metricCard('Valor integrado',currency(total(rows,'integrated')),'Data de integração','green')}${metricCard('Conversão',percent(conversion(rows)),'Eficiência comercial','purple')}${metricCard('Gerências ativas',number.format(rows.length),'Na seleção atual','cyan')}</div>${performanceTable('Desempenho das gerências',rows,'Gerência')}`;
    } else if(page==='teams'){
      const rows=data.team||[]; content=`<div class="page-cards">${metricCard('Produção das equipes',currency(total(rows,'inserted')),'Data de cadastro')}${metricCard('Integrado',currency(total(rows,'integrated')),'Data de integração','green')}${metricCard('Conversão',percent(conversion(rows)),'Eficiência das equipes','purple')}${metricCard('Equipes ativas',number.format(rows.length),'Na seleção atual','cyan')}</div>${performanceTable('Ranking completo de equipes',rows,'Equipe')}`;
    } else if(page==='projection'){
      const project = rows => (rows||[]).map(row=>({...row,integrated:Number(row.integrated)*factor,conversion:factor*100}));
      content=`<div class="page-cards">${metricCard('Integrado atual',currency(month?.integrated),'Mês em andamento','green')}${metricCard('Projeção mensal',currency(month?.projection),'Ritmo por dias úteis','purple')}${metricCard('Variação mensal',percent(month?.variance),month?.variance>=0?'Crescimento':'Queda',month?.variance>=0?'green':'red')}${metricCard('Dias analisados',selected('day')||'Mês','Período selecionado','cyan')}</div><div class="ranking-grid">${ranking('Projeção por gerência',project(data.manual_management))}${ranking('Projeção por equipe',project(data.team))}</div>`;
    } else if(page==='comparisons'){
      content=`<div class="page-cards">${metricCard('Mês atual',currency(month?.integrated),'Valor integrado','green')}${metricCard('Fechamento projetado',currency(month?.projection),'Dias úteis','purple')}${metricCard('Variação',percent(month?.variance),'Contra mês anterior',month?.variance>=0?'green':'red')}${metricCard('Meses analisados',number.format(dashboard.monthly.length),'Histórico disponível','cyan')}</div><section class="pro-panel"><div class="pro-title"><h3>Evolução mensal</h3></div>${dashboard.monthly.map(row=>`<div class="month-row"><b>${row.label}</b><span>${currency(row.integrated)}</span><strong>${currency(row.projection)}</strong><em class="${row.variance>=0?'positive':'negative'}">${row.variance>=0?'▲':'▼'} ${percent(Math.abs(row.variance))}</em></div>`).join('')}</section>`;
    } else {
      content=`<div class="page-cards">${(data.statuses||[]).slice(0,4).map((row,index)=>metricCard(row.label,currency(row.value),`${number.format(row.count)} propostas`,['green','red','cyan','purple'][index])).join('')}</div><div class="ranking-grid">${ranking('Produção por equipe',data.team,'inserted')}${ranking('Produção por gerência',data.manual_management,'inserted')}</div>`;
    }
    analysis.innerHTML=`<div class="page-heading"><span>BI ANALYTICS</span><h2>${titles[page]||'Análise'}</h2><p>Dados atualizados conforme os filtros globais.</p></div>${content}`;
    lucide.createIcons();
  };
})();
