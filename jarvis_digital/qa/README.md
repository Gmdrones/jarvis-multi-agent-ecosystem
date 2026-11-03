# Jarvis Digital — QA real

Instale Playwright no ambiente de desenvolvimento e o navegador Firefox oficial. O módulo não utiliza perfis, cookies ou sessões do usuário.

```bash
python browser_qa.py http://127.0.0.1:8765/ ./qa-output
```

Abre três contextos isolados em 1440×900, 768×1024 e 390×844. Registra console, respostas HTTP com erro, overflow, imagens, nomes de links e âncoras, foco inicial de teclado, capturas completas e hashes SHA-256.

O destino deve ser localhost ou jarvis-digital.pages.dev. Não clica CTAs externos nem envia mensagens. O resultado técnico não concede aprovação visual, factual, de licenças, de contraste ou de acessibilidade integral. Esses itens permanecem pendentes até revisão independente.

Validação realizada em 03/11/2026: renderização real de um build anterior em três larguras. Detectou imagem não carregada e retornou REPROVADO_TECNICO. Nenhum cliente ou site foi publicado por este teste. Corrigida coleta de imagens lazy antes de avaliar. Esta branch contém apenas código genérico; não inclui CRM, leads, credenciais ou arquivos do computador do usuário.
