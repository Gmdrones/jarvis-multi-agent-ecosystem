# JARVIS Digital — operação reproduzível (03/11/2026)

Estado: piloto validado; missão de 20 empresas NÃO CONCLUÍDA. Não usar o resumo original do HUNTER_RESULTS.json como aprovação: os 20 registros foram bloqueados pelo gate na primeira avaliação. Studio 962 foi posteriormente verificado com capturas reais independentes.

## Fluxo obrigatório
1. Pesquisar nome exato, nome/endereço, site oficial, variações/unidade, perfil Google e biografia Instagram. Salvar retornos originais com URL, UTC e SHA256. Resumo reconstruído ou texto digitado não substitui captura.
2. Conferir identidade da unidade por pelo menos dois identificadores. Não inferir WhatsApp a partir de telefone. Preencher candidate.json no esquema do lead_presence_gate.py canônico, preservado.
3. Executar PipelineOrchestrator com workspace_root e canonical_gate_path explícitos; nunca depender do caminho padrão. Ausência inconclusiva fica NÃO VERIFICADO. Revalidar evidências antes de produzir/publicar.
4. InstagramIntelligence separa referências de mídia autorizada. Exigir URL, data, hash e direitos. Não baixar/republicar Reels sem autorização. Conferência humana de unidade continua obrigatória.
5. Criar briefing e ART_DIRECTION individual. React/Vite, mídia original claramente rotulada, serviços comprovados, sem avaliações/preços/resultados inventados.
6. npm ci --ignore-scripts --no-audit --no-fund; npm run build. Não copiar node_modules, .env, CRM ou capturas para dist.
7. browser_qa.py URL DIRETORIO: renderizar 1440/768/390. A saída técnica fica pendente de revisão independente. Testar menu, Escape, âncoras, teclado e CTAs sem enviar mensagens.
8. SENTINELA deve ler código/fontes e as três capturas, registrar hashes, revisão visual/factual e nota >=90. Mudança de código/mídia invalida revisão. Apenas afirmar aprovação dos itens efetivamente inspecionados.
9. PagesPackager reavalia o gate, mídia e cobertura de hashes. Seu pacote isolado NÃO implementa expiração sozinho. Combinar com expiry_worker.mjs e registro de slugs para expiração server-side.
10. Compor release contendo todos os slugs ativos aprovados. O Pages substitui o deploy completo; nunca publicar um cliente isolado apagando os outros. compose_approved.py atual é específico ao piloto e precisa generalização antes de outro lote.
11. Publicar no projeto existente jarvis-digital; testar HTTPS/200, assets, três viewports, 404, 410, noindex e arquivos internos. Só então atualizar published=true, versão, data e URL.
12. Preparar kit comercial e registrar NOVO / AGUARDANDO_REVISÃO_DE_ENVIO. Não enviar mensagens nesta missão.

## Testes e dependências
Motor: Python 3.13, biblioteca padrão; test_engine.py depende do lead_presence_gate.py original no workspace Comercial. A cópia no Git é um componente do workspace, não um pacote autônomo instalável. Para execução remota, usar caminhos absolutos reais de Python/Node; PATH estava incompleto.
QA: pip Playwright e Firefox limpo, sem perfil/cookies do usuário. node --test hosting/expiry_worker.test.mjs. Não desabilitar TLS.
Em 03/11: 13 testes do motor, 11 do Worker, 8 interações, 3 viewports locais e 3 públicos passaram. Testes básicos não equivalem a auditoria completa WCAG ou benchmark Lighthouse.
Bridge recuperado com classificação STOPPED_SHELL/STARTUP_ERROR. Estar aberto no Maestri não significa agente ativo. Usar maestri list/check e estado real; não reencaminhar filas antigas cegamente.

## Desativar e expirar
No registro do Worker, active=false bloqueia o slug com 410; expires_at UTC bloqueia na data limite. Gerar novo release preservando os demais slugs e publicar. A expiração por data não requer novo deploy. Piloto expira em 2026-11-10T13:26:51.198536Z.
Rollback: republicar release anterior conhecido, verificando que sua validade e registro de clientes ainda são adequados. Releases do runtime-check são TEST_ONLY e não contam como empresas.

## Pendências
19 outras empresas ainda sem qualificação suficiente; nenhum site delas aprovado. Hunter produziu um script com textos simulando capturas: NÃO EXECUTAR qualify_next5.py para fabricar evidências. Outros terminais Maestri não foram todos recuperados. Revisão de regressão dos dez projetos não foi completa; uma imagem quebrada foi observada em Almecorp e não alterada.
