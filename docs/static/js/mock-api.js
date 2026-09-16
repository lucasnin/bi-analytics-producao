(() => {
  const REQUIRED_COLUMNS = [
    'id_front','convenio','Esteira_Funcao','Status_Funcao','produto','modalidade',
    'valor_contrato','valor_liberacao','Equipe_Padronizada','operador','gerente',
    'Gerente_Manual','data_atualizacao','data_cadastro','data_integracao',
  ];
  const DB_NAME = 'bi-analytics-browser';
  const DB_STORE = 'imports';
  const DB_KEY = 'production';
  const latest = new Date('2026-09-15T15:08:00-03:00');
  const labels = ['01/09','02/09','03/09','04/09','08/09','09/09','10/09','11/09','14/09','15/09'];
  const values = [980325,729630,1035643,978403,1194220,1087460,1128310,1268920,965376,233844];
  const dailyIntegratedValues = [456000,338000,481000,455000,555000,505000,524000,590000,390398.48,265967.53];
  const integrated = 4560366.01;

  const entities = (names, base) => names.map((label, index) => {
    const inserted = Math.round(base * (1 - index * .075));
    const paid = Math.max(2, 42 - index * 3);
    const contracts = paid + 18 + index;
    const integratedValue = Math.round(inserted * (.71 - index * .025));
    return {label, inserted, integrated: integratedValue, contracts, paid, conversion: integratedValue / inserted * 100};
  });
  const demoTeams = entities(['Uruguai','Chile','França','Praia do Flamengo','Praia de Ipanema','Argentina','Sérvia','Marrocos','Japão','Praia do Forte'], 910000);
  const demoOperators = entities(['Nicolas Rodrigues','Gabriel Guimarães','Everson Nascimento','Kimberly Almeida','Raphael Tavares','Arcangelo Santos','Willian Pinheiro','Vitória Oliveira','Ademir Geronymo','Aline Barbosa'], 238000);
  const demoManagements = entities(['Térreo','Luana','1º Andar','Alphaville'], 2190000);
  const demoAgreements = entities(['GOV São Paulo','Prefeitura de São Paulo','SIAPE','GOV Rio de Janeiro','GOV Minas Gerais'], 1660000);
  const demoModalities = entities(['Novo','Compra'], 5200000);
  const demoStatuses = [
    {label:'Integrado',value:integrated,count:741},{label:'Andamento',value:3130239,count:328},
    {label:'Reprovado',value:1243856,count:174},{label:'Pendente',value:599241,count:57},
    {label:'Liberado',value:210965,count:25},{label:'Cancelado',value:30236,count:5},
  ];
  const demoMonthlyValues = [6867045,7745498,11385480,8865404,9012633,9774280,13285604,12887422,4560366];
  const demoMonthly = demoMonthlyValues.map((value,index) => ({
    label:`${String(index+1).padStart(2,'0')}/2026`, integrated:value,
    projection:index===8?9120732:Math.round(value*(.88+index*.012)),
    variance:index?((value/demoMonthlyValues[index-1])-1)*100:0,
  }));
  const demoDashboard = {
    kpis:[{key:'production',label:'Produção total',value:values.reduce((sum,value)=>sum+value,0)},
      {key:'integrated',label:'Valor integrado',value:integrated}],
    daily:labels.map((label,index)=>({label,value:values[index]})), accumulated:[],
    teams:demoTeams.map(row=>({label:row.label,value:row.inserted})),
    operators:demoOperators.map(row=>({label:row.label,value:row.inserted})),
    managements:demoManagements.map(row=>({label:row.label,value:row.inserted})), statuses:demoStatuses,
    daily_by_status:{Integrado:dailyIntegratedValues,Andamento:values.map(v=>v*.32),Pendente:values.map(v=>v*.08),Reprovado:values.map(v=>v*.13)},
    monthly:demoMonthly,
    insights:[{type:'alert',title:'Evolução no período',text:'A produção está 12,8% abaixo do ritmo projetado para o fechamento.'}],
    story:['O período reúne 1.330 contratos e R$ 9,8 milhões em valor contratado.','O valor integrado representa 46,7% da produção selecionada.','Uruguai lidera entre as equipes, concentrando 8,1% do valor contratado.','No ritmo atual, o integrado do mês pode alcançar R$ 9,1 milhões.'],
    analytics:{statuses:demoStatuses,team:demoTeams,operator:demoOperators,manual_management:demoManagements,agreement:demoAgreements,modality:demoModalities},
    source:'demo',
  };
  const demoFilters = {
    managements:[],manual_managements:['TÉRREO','LUANA','1_ANDAR','ALPHAVILLE'],teams:demoTeams.map(r=>r.label),operators:demoOperators.map(r=>r.label),
    products:['Empréstimo','Cartão Benefício','Cartão de Crédito','Adiantamento Salarial'],modalities:['Novo','Compra'],agreements:demoAgreements.map(r=>r.label),
    statuses:demoStatuses.map(r=>r.label),years:[2026],latest_date:'2026-09-15',latest_update:latest.toISOString(),source:'demo',
  };

  const json = (body, status=200) => new Response(JSON.stringify(body), {status,headers:{'Content-Type':'application/json'}});
  const brl = value => new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(value||0));
  const fold = value => String(value||'').normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLocaleLowerCase('pt-BR').trim();
  const unique = (rows,key) => [...new Set(rows.map(row=>row[key]).filter(Boolean))].sort((a,b)=>a.localeCompare(b,'pt-BR'));
  const businessDate = row => fold(row.status)==='integrado' ? row.integratedAt : row.createdAt;
  const inPeriod = (date,start,end) => Boolean(date && (!start || date>=start) && (!end || date<=end));
  const isoDate = value => {
    const text=String(value||'').trim(); if(!text || fold(text)==='null')return null;
    const iso=text.match(/^(\d{4})-(\d{2})-(\d{2})/); if(iso)return `${iso[1]}-${iso[2]}-${iso[3]}`;
    const br=text.match(/^(\d{1,2})\/(\d{1,2})\/(\d{2,4})/); if(br)return `${br[3].length===2?'20'+br[3]:br[3]}-${br[2].padStart(2,'0')}-${br[1].padStart(2,'0')}`;
    return null;
  };
  const parseMoney = value => {
    let text=String(value||'').trim(); if(!text || fold(text)==='null')return 0;
    text=text.replace(/R\$|\s/g,'');
    if(text.includes(','))text=text.replace(/\./g,'').replace(',','.');
    const parsed=Number(text); if(!Number.isFinite(parsed))throw Error(`Valor monetário inválido: ${value}`); return parsed;
  };

  function detectDelimiter(text){
    const line=text.replace(/^\uFEFF/,'').split(/\r?\n/,1)[0]; let comma=0,semi=0,quoted=false;
    for(let i=0;i<line.length;i++){if(line[i]==='"')quoted=!quoted;else if(!quoted&&line[i]===',')comma++;else if(!quoted&&line[i]===';')semi++;}
    return semi>comma?';':',';
  }
  function parseCsv(text){
    const delimiter=detectDelimiter(text),table=[]; let row=[],field='',quoted=false;
    for(let i=0;i<text.length;i++){
      const char=text[i];
      if(quoted){if(char==='"'&&text[i+1]==='"'){field+='"';i++;}else if(char==='"')quoted=false;else field+=char;continue;}
      if(char==='"'){quoted=true;continue;} if(char===delimiter){row.push(field);field='';continue;}
      if(char==='\n'||char==='\r'){if(char==='\r'&&text[i+1]==='\n')i++;row.push(field);field='';if(row.some(value=>value!==''))table.push(row);row=[];continue;}
      field+=char;
    }
    if(field||row.length){row.push(field);if(row.some(value=>value!==''))table.push(row);}
    if(!table.length)throw Error('O arquivo CSV está vazio');
    const headers=table.shift().map((value,index)=>index===0?value.replace(/^\uFEFF/,'').trim():value.trim());
    const normalized=new Map(headers.map((name,index)=>[fold(name),index]));
    const missing=REQUIRED_COLUMNS.filter(name=>!normalized.has(fold(name)));
    if(missing.length)throw Error('Colunas obrigatórias ausentes: '+missing.join(', '));
    const get=(raw,name)=>raw[normalized.get(fold(name))]??'';
    const rows=table.map((raw,index)=>{
      try{return {
        id:String(get(raw,'id_front')).trim()||`linha-${index+2}`,agreement:String(get(raw,'convenio')).trim()||'Sem convênio',stage:String(get(raw,'Esteira_Funcao')).trim(),
        status:String(get(raw,'Status_Funcao')).trim()||'Sem status',product:String(get(raw,'produto')).trim()||'Sem produto',modality:String(get(raw,'modalidade')).trim()||'Sem modalidade',
        contract:parseMoney(get(raw,'valor_contrato')),released:parseMoney(get(raw,'valor_liberacao')),team:String(get(raw,'Equipe_Padronizada')).trim()||'Sem equipe',
        operator:String(get(raw,'operador')).trim()||'Sem operador',management:fold(get(raw,'gerente'))==='null'?'Sem gerência':String(get(raw,'gerente')).trim()||'Sem gerência',
        manualManagement:String(get(raw,'Gerente_Manual')).trim()||'Sem gerência manual',createdAt:isoDate(get(raw,'data_cadastro')),integratedAt:isoDate(get(raw,'data_integracao')),
        updatedAt:String(get(raw,'data_atualizacao')).trim()||null,
      };}catch(error){throw Error(`Linha ${index+2}: ${error.message}`);}
    });
    if(!rows.length)throw Error('O CSV não contém registros');
    return rows;
  }

  function openDb(){
    return new Promise((resolve,reject)=>{const request=indexedDB.open(DB_NAME,1);request.onupgradeneeded=()=>request.result.createObjectStore(DB_STORE,{keyPath:'key'});request.onsuccess=()=>resolve(request.result);request.onerror=()=>reject(request.error);});
  }
  async function saveImport(record){const db=await openDb();await new Promise((resolve,reject)=>{const tx=db.transaction(DB_STORE,'readwrite');tx.objectStore(DB_STORE).put(record);tx.oncomplete=resolve;tx.onerror=()=>reject(tx.error);});db.close();}
  async function loadImport(){try{const db=await openDb();const result=await new Promise((resolve,reject)=>{const request=db.transaction(DB_STORE).objectStore(DB_STORE).get(DB_KEY);request.onsuccess=()=>resolve(request.result||null);request.onerror=()=>reject(request.error);});db.close();return result;}catch{return null;}}
  let importedPromise=loadImport();

  function filterConfig(params,rows){
    const config={start:params.get('start_date'),end:params.get('end_date')};
    [['manual_management','manualManagement'],['team','team'],['operator','operator'],['status','status'],['modality','modality'],['product','product'],['agreement','agreement']].forEach(([query,key])=>{config[key]=params.get(query)||'';});
    const dates=rows.map(businessDate).filter(Boolean).sort(); const last=dates.at(-1);
    if(!config.end)config.end=last;if(!config.start&&last)config.start=last.slice(0,8)+'01';
    return config;
  }
  function matches(row,config){return ['manualManagement','team','operator','status','modality','product','agreement'].every(key=>!config[key]||fold(row[key])===fold(config[key]));}
  function rank(map,limit=10){return [...map.entries()].map(([label,value])=>({label,value})).sort((a,b)=>b.value-a.value).slice(0,limit);}
  function add(map,key,value){map.set(key,(map.get(key)||0)+Number(value||0));}
  function monthStart(iso,offset=0){const date=new Date(`${iso.slice(0,7)}-01T12:00:00`);date.setMonth(date.getMonth()+offset);return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-01`;}
  function monthEnd(start){const date=new Date(`${start}T12:00:00`),last=new Date(date.getFullYear(),date.getMonth()+1,0);return `${last.getFullYear()}-${String(last.getMonth()+1).padStart(2,'0')}-${String(last.getDate()).padStart(2,'0')}`;}
  function businessDays(start,end){let count=0,date=new Date(`${start}T12:00:00`),last=new Date(`${end}T12:00:00`);for(;date<=last;date.setDate(date.getDate()+1)){const day=date.getDay();if(day!==0&&day!==6)count++;}return count;}
  function groupAdvanced(rows,config,start,end){
    const names=['operator','manualManagement','team','agreement','modality'];
    const groups=Object.fromEntries(names.map(name=>[name,new Map()])); const statuses=new Map();
    const bucket=(map,label)=>{if(!map.has(label))map.set(label,{label,inserted:0,integrated:0,contracts:new Set(),paid:new Set()});return map.get(label);};
    rows.forEach(row=>{if(!matches(row,config))return;const created=inPeriod(row.createdAt,start,end),paid=fold(row.status)==='integrado'&&inPeriod(row.integratedAt,start,end),business=inPeriod(businessDate(row),start,end);
      if(business){if(!statuses.has(row.status))statuses.set(row.status,{label:row.status,value:0,ids:new Set()});const item=statuses.get(row.status);item.value+=row.contract;item.ids.add(row.id);}
      names.forEach(name=>{const item=bucket(groups[name],row[name]);if(created){item.inserted+=row.contract;item.contracts.add(row.id);}if(paid){item.integrated+=row.contract;item.paid.add(row.id);}});
    });
    const output=map=>[...map.values()].map(item=>({label:item.label,inserted:item.inserted,integrated:item.integrated,contracts:item.contracts.size,paid:item.paid.size,conversion:item.inserted?item.integrated/item.inserted*100:0})).sort((a,b)=>b.inserted-a.inserted);
    return {statuses:[...statuses.values()].map(item=>({label:item.label,value:item.value,count:item.ids.size})).sort((a,b)=>b.value-a.value),operator:output(groups.operator),manual_management:output(groups.manualManagement),team:output(groups.team),agreement:output(groups.agreement),modality:output(groups.modality)};
  }
  function monthlyAnalysis(rows,config,latestDate){
    const points=[];const cutoffDay=Number(latestDate.slice(8,10));
    for(let offset=-8;offset<=0;offset++){
      const start=monthStart(latestDate,offset),end=monthEnd(start),cutoff=`${start.slice(0,8)}${String(Math.min(cutoffDay,Number(end.slice(8,10)))).padStart(2,'0')}`;
      let actual=0,partial=0;rows.forEach(row=>{if(fold(row.status)!=='integrado'||!matches(row,config)||!inPeriod(row.integratedAt,start,end))return;actual+=row.contract;if(row.integratedAt<=cutoff)partial+=row.contract;});
      const elapsed=Math.max(1,businessDays(start,cutoff)),totalDays=Math.max(1,businessDays(start,end)),projection=partial/elapsed*totalDays,previous=points.at(-1)?.integrated||0;
      points.push({label:`${start.slice(5,7)}/${start.slice(0,4)}`,integrated:actual,projection,variance:previous?(actual/previous-1)*100:0});
    }
    return points;
  }
  function dashboardFromRows(rows,params){
    const config=filterConfig(params,rows),selected=rows.filter(row=>inPeriod(businessDate(row),config.start,config.end)&&matches(row,config));
    const daily=new Map(),dailyStatus=new Map(),teams=new Map(),operators=new Map(),managements=new Map(),statuses=new Map();
    selected.forEach(row=>{const date=businessDate(row);add(daily,date,row.contract);if(!dailyStatus.has(row.status))dailyStatus.set(row.status,new Map());add(dailyStatus.get(row.status),date,row.contract);add(teams,row.team,row.contract);add(operators,row.operator,row.contract);add(managements,row.manualManagement,row.contract);add(statuses,row.status,row.contract);});
    const dates=[...daily.keys()].sort(),total=selected.reduce((sum,row)=>sum+row.contract,0),integratedValue=selected.filter(row=>fold(row.status)==='integrado').reduce((sum,row)=>sum+row.contract,0),contracts=new Set(selected.map(row=>row.id)).size;
    const previousEnd=new Date(`${config.start}T12:00:00`);previousEnd.setDate(previousEnd.getDate()-1);const prevEnd=`${previousEnd.getFullYear()}-${String(previousEnd.getMonth()+1).padStart(2,'0')}-${String(previousEnd.getDate()).padStart(2,'0')}`,prevStart=prevEnd.slice(0,8)+'01';
    const previous=rows.filter(row=>inPeriod(businessDate(row),prevStart,prevEnd)&&matches(row,config)).reduce((sum,row)=>sum+row.contract,0),change=previous?(total/previous-1)*100:0;
    const statusRows=rank(statuses),statusValues=Object.fromEntries(statusRows.map(item=>[fold(item.label),item.value])),analytics=groupAdvanced(rows,config,config.start,config.end),monthly=monthlyAnalysis(rows,config,rows.map(businessDate).filter(Boolean).sort().at(-1));
    let running=0;const dailyRows=dates.map(date=>({label:`${date.slice(8,10)}/${date.slice(5,7)}`,value:daily.get(date)}));const accumulated=dailyRows.map(item=>({label:item.label,value:(running+=item.value)}));
    const teamRows=rank(teams),operatorRows=rank(operators),managementRows=rank(managements),rate=total?integratedValue/total*100:0,top=teamRows[0];
    const story=contracts?[`O período reúne ${contracts.toLocaleString('pt-BR')} contratos e ${brl(total)} em valor contratado.`,`O valor integrado representa ${rate.toFixed(1).replace('.',',')}% da produção filtrada.`,...(top?[`${top.label} lidera entre as equipes, concentrando ${(top.value/Math.max(1,total)*100).toFixed(1).replace('.',',')}% do valor contratado.`]:[]),...(monthly.at(-1)?.projection>monthly.at(-1)?.integrated?[`No ritmo atual, o integrado do mês pode alcançar ${brl(monthly.at(-1).projection)}.`]:[])]:['Não há produção para a combinação de filtros selecionada.'];
    return {total,integrated:integratedValue,contracts,kpis:[{key:'production',label:'Produção total',value:total,change},{key:'integrated',label:'Valor integrado',value:integratedValue},{key:'contracts',label:'Contratos',value:contracts,format:'number'},{key:'cancelled',label:'Valor cancelado',value:statusValues.cancelado||0},{key:'progress',label:'Em andamento',value:statusValues.andamento||0},{key:'pending',label:'Valor pendente',value:statusValues.pendente||0},{key:'ticket',label:'Ticket médio',value:contracts?total/contracts:0},{key:'change',label:'Variação mensal',value:change,format:'percent',change}],
      daily:dailyRows,accumulated,teams:teamRows,operators:operatorRows,managements:managementRows,statuses:statusRows,daily_by_status:Object.fromEntries([...dailyStatus].map(([status,map])=>[status,dates.map(date=>map.get(date)||0)])),monthly,analytics,story,
      insights:[{type:change>=0?'positive':'alert',title:'Evolução no período',text:`A produção está ${Math.abs(change).toFixed(1).replace('.',',')}% ${change>=0?'acima':'abaixo'} do período anterior.`}],source:'browser-import'};
  }
  function filtersFromRows(rows,meta){const dates=rows.map(businessDate).filter(Boolean).sort(),updates=rows.map(row=>row.updatedAt).filter(Boolean).sort();return {managements:unique(rows,'management'),manual_managements:unique(rows,'manualManagement'),teams:unique(rows,'team'),operators:unique(rows,'operator'),products:unique(rows,'product'),modalities:unique(rows,'modality'),agreements:unique(rows,'agreement'),statuses:unique(rows,'status'),years:[...new Set(dates.map(date=>Number(date.slice(0,4))))].sort((a,b)=>b-a),latest_date:dates.at(-1),latest_update:updates.at(-1)||meta.importedAt,filename:meta.filename,source:'browser-import'};}
  function explicitQuestionDate(question,latestDate){const match=question.match(/\b(\d{1,2})\/(\d{1,2})(?:\/(\d{2,4}))?\b/);if(match)return `${match[3]?(match[3].length===2?'20'+match[3]:match[3]):latestDate.slice(0,4)}-${match[2].padStart(2,'0')}-${match[1].padStart(2,'0')}`;const date=new Date(`${latestDate}T12:00:00`);if(question.includes('ontem'))date.setDate(date.getDate()-1);else if(!question.includes('hoje'))return null;return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,'0')}-${String(date.getDate()).padStart(2,'0')}`;}
  function answerFromRows(record,body){const rows=record.rows,question=fold(body.question),latestDate=rows.map(businessDate).filter(Boolean).sort().at(-1),date=explicitQuestionDate(question,latestDate),params=new URLSearchParams(body.filters||{});if(date){params.set('start_date',date);params.set('end_date',date);}if(question.includes('integr'))params.set('status','Integrado');const data=dashboardFromRows(rows,params),advanced=data.analytics;let dimension=null,groups=null;if(question.includes('operador')){dimension='operador';groups=advanced.operator;}else if(question.includes('equipe')){dimension='equipe';groups=advanced.team;}else if(question.includes('gerenc')){dimension='gerência';groups=advanced.manual_management;}else if(question.includes('convenio')){dimension='convênio';groups=advanced.agreement;}else if(question.includes('modalidade')){dimension='modalidade';groups=advanced.modality;}const countQuestion=/quantos|quantidade|numero de|número de/.test(question);if(groups){const ranking=groups.map(row=>({label:row.label,value:countQuestion?row.paid:row.integrated})).sort((a,b)=>b.value-a.value),leader=ranking[0];return {answer:leader?`${leader.label} lidera por ${dimension} com ${countQuestion?leader.value.toLocaleString('pt-BR')+' contratos':brl(leader.value)}.`:`Não há dados por ${dimension} no período.`,visualization:'ranking',value_format:countQuestion?'number':'currency',data:ranking.slice(0,question.includes('5')?5:10)};}const period=date?`em ${date.slice(8,10)}/${date.slice(5,7)}/${date.slice(0,4)}`:'no período selecionado';return countQuestion?{answer:`A quantidade de contratos integrados ${period} é ${data.contracts.toLocaleString('pt-BR')}.`,visualization:'kpi',value_format:'number',data:[]}:{answer:`O valor integrado ${period} é ${brl(data.integrated)}.`,visualization:'kpi',value_format:'currency',data:[]};}

  const originalFetch=window.fetch.bind(window);
  window.fetch=async(input,init={})=>{
    const url=new URL(typeof input==='string'?input:input.url,location.href);if(!url.pathname.startsWith('/api/'))return originalFetch(input,init);
    if(url.pathname==='/api/imports/production'&&String(init.method||'GET').toUpperCase()==='POST'){
      try{const file=init.body instanceof FormData?init.body.get('file'):null;if(!(file instanceof File))throw Error('Selecione um arquivo CSV');if(!file.name.toLowerCase().endsWith('.csv'))throw Error('Envie um arquivo CSV');const rows=parseCsv(await file.text()),record={key:DB_KEY,rows,meta:{filename:file.name,rows:rows.length,importedAt:new Date().toISOString(),size:file.size}};await saveImport(record);importedPromise=Promise.resolve(record);const dates=rows.map(businessDate).filter(Boolean).sort();return json({filename:file.name,rows:rows.length,start_date:dates[0],end_date:dates.at(-1),storage:'browser'});}catch(error){return json({detail:error.message||'Falha na importação'},400);}
    }
    const record=await importedPromise;
    if(url.pathname.endsWith('/production/filters'))return json(record?filtersFromRows(record.rows,record.meta):demoFilters);
    if(url.pathname==='/api/dashboard/resumo')return json(record?dashboardFromRows(record.rows,url.searchParams):demoDashboard);
    if(url.pathname==='/api/ai/ask'){
      const body=JSON.parse(init.body||'{}');if(record)return json(answerFromRows(record,body));
      const question=fold(body.question);if(question.includes('operador'))return json({answer:`Nicolas Rodrigues lidera o período com ${brl(demoOperators[0].integrated)} integrados.`,visualization:'ranking',value_format:'currency',data:demoOperators.slice(0,question.includes('5')?5:10).map(row=>({label:row.label,value:row.integrated}))});if(question.includes('equipe'))return json({answer:`A equipe Uruguai lidera o período com ${brl(demoTeams[0].integrated)} integrados.`,visualization:'ranking',value_format:'currency',data:demoTeams.slice(0,5).map(row=>({label:row.label,value:row.integrated}))});const date=explicitQuestionDate(question,'2026-09-15'),index=date?labels.indexOf(`${date.slice(8,10)}/${date.slice(5,7)}`):-1;return json({answer:date&&index>=0?`O valor integrado em ${date.slice(8,10)}/${date.slice(5,7)}/${date.slice(0,4)} é ${brl(dailyIntegratedValues[index])}.`:`O valor integrado no período selecionado é ${brl(integrated)}.`,visualization:'kpi',value_format:'currency',data:[]});
    }
    return json({detail:'Rota indisponível na demonstração.'},404);
  };
})();

