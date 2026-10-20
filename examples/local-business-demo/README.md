# JARVIS Local Business Demo — template reutilizável

Template **original**, independente do Emergent, para demonstrações comerciais de pequenos negócios. Não contém código, logos ou ativos do Emergent. Inspirado na estrutura comum de landing pages: hero, serviços, diferenciais, agendamento e WhatsApp.

## Abrir
Use `index.html` em um servidor estático, ou GitHub Pages habilitado para o repositório. Não exige API, npm, build ou banco.

## Personalizar
Edite apenas `config.js` com nome comercial, nicho, identidade, serviços, cidade, fotos autorizadas, número WhatsApp e horários. Todos os textos são tratados como conteúdo, não código. Há também presets demonstrativos selecionáveis por `?demo=estetica`, `?demo=pet` e `?demo=clinica`.

**Atenção:** a demo é NÃO OFICIAL. Os presets usam negócios fictícios. Não use nome, logo, contato ou fotografia de uma empresa real sem autorização/licença. O botão WhatsApp só funciona quando há um número autorizado; sem número, fica desabilitado. Agendamentos são simulações locais — nenhum dado é enviado ou guardado.

## Transformar em produto
Depois da contratação: conectar domínio, WhatsApp Business oficial, calendário/backend, políticas LGPD, SEO local e Perfil da Empresa no Google com aprovação do proprietário. Imagens de drone somente após verificações operacionais e autorizações necessárias.

## Arquivos
- `index.html`: interface
- `config.js`: branding + presets; personalização por cliente
- `style.css`: design responsivo

## Fluxo dos agentes
Hunter → Qualificador → Propostas (duplicar config e gerar print/link) → Pipeline (abordagem individual) → Supervisor/SENTINELA. Não publicar demos como sites oficiais dos prospectados.

## Limites
Este projeto não implementa backend, envio real de WhatsApp ou cadastro de agendamentos. Não usa serviços pagos.

## Agendamento para estética, pet shop e clínicas
Os três presets incluem serviço, data e horário. Quando `phone` em `config.js` estiver preenchido com **número WhatsApp autorizado em formato internacional (ex.: 55 + DDD + número)**, a solicitação abre uma conversa via `wa.me` com mensagem pré-preenchida; **o cliente ainda precisa apertar Enviar**. Sem número, o formulário apenas simula a solicitação, sem transmitir dados. O WhatsApp não confirma automaticamente uma reserva.

**Integração Google Agenda (próxima etapa, após contratação):** conectar o Google Calendar do estabelecimento por OAuth, backend seguro e API; consultar disponibilidade real, criar eventos, impedir sobreposição, administrar fuso horário e cancelamentos e receber notificações de alterações. Não incluir credenciais ou tokens no repositório. Não existe sincronização ativa com Google Agenda nesta versão estática.

Para agendamentos de saúde, minimizar dados pessoais e evitar qualquer informação médica sensível no texto do WhatsApp; validar consentimento, privacidade e controles de acesso na implementação definitiva.
