(() => {
  const latest = new Date('2026-09-15T15:08:00-03:00');
  const labels = ['01/09','02/09','03/09','04/09','08/09','09/09','10/09','11/09','14/09','15/09'];
  const values = [980325,729630,1035643,978403,1194220,1087460,1128310,1268920,965376,233844];
  const total = values.reduce((sum, value) => sum + value, 0);
  const integrated = 4560366.01;
  const entities = (names, base) => names.map((label, index) => {
    const inserted = Math.round(base * (1 - index * .075));
    const paid = Math.max(2, 42 - index * 3);
    const contracts = paid + 18 + index;
    const integratedValue = Math.round(inserted * (.71 - index * .025));
    return {label, inserted, integrated: integratedValue, contracts, paid, conversion: integratedValue / inserted * 100};
  });
  const teams = entities(['Uruguai','Chile','França','Praia do Flamengo','Praia de Ipanema','Argentina','Sérvia','Marrocos','Japão','Praia do Forte'], 910000);
  const operators = entities(['Nicolas Rodrigues','Gabriel Guimarães','Everson Nascimento','Kimberly Almeida','Raphael Tavares','Arcangelo Santos','Willian Pinheiro','Vitória Oliveira','Ademir Geronymo','Aline Barbosa'], 238000);
  const managements = entities(['Térreo','Luana','1º Andar','Alphaville'], 2190000);
  const agreements = entities(['GOV São Paulo','Prefeitura de São Paulo','SIAPE','GOV Rio de Janeiro','GOV Minas Gerais'], 1660000);
  const modalities = entities(['Novo','Compra'], 5200000);
  const statuses = [
    {label:'Integrado',value:integrated,count:741},
    {label:'Andamento',value:3130239,count:328},
    {label:'Reprovado',value:1243856,count:174},
    {label:'Pendente',value:599241,count:57},
    {label:'Liberado',value:210965,count:25},
    {label:'Cancelado',value:30236,count:5},
  ];
  const monthlyIntegrated = [6867045,7745498,11385480,8865404,9012633,9774280,13285604,12887422,4560366];
  const monthly = monthlyIntegrated.map((value,index) => {
    const previous = monthlyIntegrated[index-1] || value;
    return {label:`${String(index+1).padStart(2,'0')}/2026`,integrated:value,projection:index===8?9120732:Math.round(value*(.88+index*.012)),variance:index?((value/previous)-1)*100:0};
  });
  const dashboard = {
    kpis:[{key:'production',label:'Produção total',value:total},{key:'integrated',label:'Valor integrado',value:integrated}],
    daily:labels.map((label,index)=>({label,value:values[index]})),
    accumulated:[], teams:teams.map(row=>({label:row.label,value:row.inserted})),
    operators:operators.map(row=>({label:row.label,value:row.inserted})),
    managements:managements.map(row=>({label:row.label,value:row.inserted})), statuses,
    daily_by_status:{
      Integrado:values.map(value=>value*.47), Andamento:values.map(value=>value*.32),
      Pendente:values.map(value=>value*.08), Reprovado:values.map(value=>value*.13),
    }, monthly,
    insights:[{type:'alert',title:'Evolução no período',text:'A produção está 12,8% abaixo do ritmo projetado para o fechamento.'}],
    story:[
      'O período reúne 1.330 contratos e R$ 9,8 milhões em valor contratado.',
      'O valor integrado representa 46,7% da produção selecionada.',
      'Uruguai lidera entre as equipes, concentrando 8,1% do valor contratado.',
      'No ritmo atual, o integrado do mês pode alcançar R$ 9,1 milhões.',
    ],
    analytics:{statuses,team:teams,operator:operators,manual_management:managements,agreement:agreements,modality:modalities},
    source:'demo',
  };
  const filters = {
    managements:[], manual_managements:['TÉRREO','LUANA','1_ANDAR','ALPHAVILLE'],
    teams:teams.map(row=>row.label), operators:operators.map(row=>row.label),
    products:['Empréstimo','Cartão Benefício','Cartão de Crédito','Adiantamento Salarial'],
    modalities:['Novo','Compra'], agreements:agreements.map(row=>row.label), statuses:statuses.map(row=>row.label),
    years:[2026], latest_date:'2026-09-15', latest_update:latest.toISOString(),
  };
  const json = (body, status=200) => new Response(JSON.stringify(body), {status,headers:{'Content-Type':'application/json'}});
  const brl = value => new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(value);
  const originalFetch = window.fetch.bind(window);
  window.fetch = async (input, init={}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    if (!url.pathname.startsWith('/api/')) return originalFetch(input, init);
    if (url.pathname.endsWith('/production/filters')) return json(filters);
    if (url.pathname === '/api/dashboard/resumo') return json(dashboard);
    if (url.pathname === '/api/imports/production' && String(init.method||'GET').toUpperCase()==='POST') {
      return json({detail:'A importação persistente está disponível na versão FastAPI conectada ao servidor.'},400);
    }
    if (url.pathname === '/api/ai/ask') {
      const body = JSON.parse(init.body || '{}'), question = String(body.question||'').toLocaleLowerCase('pt-BR');
      if (question.includes('operador')) return json({answer:`Nicolas Rodrigues lidera o período com ${brl(operators[0].integrated)} integrados.`,visualization:'ranking',value_format:'currency',data:operators.slice(0,question.includes('5')?5:10).map(row=>({label:row.label,value:row.integrated}))});
      if (question.includes('equipe')) return json({answer:`A equipe Uruguai lidera o período com ${brl(teams[0].integrated)} integrados.`,visualization:'ranking',value_format:'currency',data:teams.slice(0,5).map(row=>({label:row.label,value:row.integrated}))});
      if (question.includes('gerência') || question.includes('gerencia')) return json({answer:`A gerência Térreo lidera o período com ${brl(managements[0].integrated)} integrados.`,visualization:'ranking',value_format:'currency',data:managements.map(row=>({label:row.label,value:row.integrated}))});
      if (question.includes('quantos') || question.includes('quantidade')) return json({answer:'A quantidade de contratos integrados no período é 741.',visualization:'kpi',value_format:'number',data:[]});
      const period = question.includes('ontem') ? 'em 14/09/2026' : 'no período selecionado';
      return json({answer:`O valor integrado ${period} é ${brl(question.includes('ontem')?390398.48:integrated)}.`,visualization:'kpi',value_format:'currency',data:[]});
    }
    return json({detail:'Rota indisponível na demonstração.'},404);
  };
})();
