> CURRENT OVERRIDE: Read `docs/CURRENT_SPEC.md` and `config/editorial.json` first. Main episodes are 5–7 minutes; capture must not depend on the user’s computer. Original duration targets below are historical.

# Arquitetura técnica e fluxo de dados

## Separar responsabilidades
**Work / editor-coordinator:** procura tendências, investiga claims, seleciona a ideia, desenha hipótese/experiência, revê provas, escreve roteiro factual e metadata, coordena calendário e QA. **Codex / builder:** constrói ferramentas, grava ecrã, processa assets, implementa composição/re-render, testa e corrige a pipeline. **Render worker:** FFmpeg/Python, subprocessos isolados com limites e logs; exporta vídeo e áudio. **Higgsfield:** apenas imagens/motion cutaways originais quando o custo é justificado; não é a montagem base.

## Estados de cada episódio
idea -> sourced -> experiment_defined -> experiment_run -> evidence_verified -> script_locked -> narrated -> rough_render -> QA -> final_render -> shorts_rendered -> approved_for_upload -> uploaded_private -> published -> metrics_reviewed.
Cada transição tem `manifest.json` atualizado e evidências verificáveis; um estado falhado não é `done`.

## Pipeline
1. **Discovery:** Work recolhe problemas, análise comparável de vídeos de 6–12 meses, fontes primárias; cria editorial brief e hipóteses testáveis.
2. **Test design:** define dados fictícios/sem dados pessoais, ambiente autorizado, objetivo e medidas de sucesso.
3. **Run & capture:** Codex executa a experiência; grava a janela com OBS/ffmpeg ou ferramenta comprovada; faz screenshots, regista comandos, outputs, custo, duração e erros; evita gravar passwords ou dados privados.
4. **Evidence first:** verifica afirmações e guarda `proofs.json` com captura/timestamps/localização e notas de incerteza.
5. **Script & speech:** Work monta estrutura baseada nas provas, roteiriza 1100–1550 palavras conforme velocidade e clips; TTS produz áudio master com timestamps/alinhamento forçado se disponível (testar o módulo).
6. **Edit plan:** gerar `timeline.json` com campos `source`, `in`, `out`, `destination`, `narration`, `crop`, `overlay`, `license`, `proof_id`; shots devem corresponder a afirmações narradas.
7. **Render:** FFmpeg cria master 1920x1080 30fps (ou frame rate constante consistente), audio 48kHz, MP4 H.264/AAC, SRT; manter assets editáveis. Export adicional OTIO/MLT ou outro formato aberto testado, sem prometer CapCut nativo.
8. **Quality gate:** `ffprobe`, verificações de frames pretos fora de intenção, silêncio inesperado, texto cortado, resolução, rácio, loudness, legendas, sincronização, palavras sem prova e ausência de publicidade indevida.
9. **Shorts:** selecionar os 2–3 micro-arcos autónomos; remix 1080x1920; verificar composição e legendas dentro da área segura.
10. **Packaging:** thumbnail 1280x720, título honesto, descrição com links e disclosures; manifest de assets/licenças.
11. **Upload:** YouTube Data API com OAuth, inicialmente `private`; TikTok por via oficial compatível se houver acesso ou entrega para upload manual. Publicação pública requer política/autorização explícita.
12. **Observe:** recolher métricas 48h/7d/28d, postmortem e feedback para temas futuros.

## Infra inicial
GitHub para código e standards; disco/pasta persistente ou Drive para fontes e exports; Python 3.12+, FFmpeg/ffprobe, gravação de ecrã, TTS, render runner com limites de CPU/memória, CSV/JSON e logs. Para tarefas recorrentes, usar Work Scheduled Tasks ou GitHub Actions/cron com credenciais protegidas, quando autorizados e disponíveis. Agendamentos do ChatGPT não devem depender de ficheiros carregados no projeto: referenciar artefactos acessíveis por ferramentas autorizadas.

## Custos
Sem preço confirmado de Higgsfield ou TTS, não prever preço fixo por episódio. `costs.csv` deve medir: minutos de geração, modelos, tentativas, voz, cloud CPU, armazenamento, uploads e custos de API. Orçamento preflight antes de qualquer geração paga. Real footage first; nenhuma geração por defeito.

## Riscos a resolver cedo
- CapCut nativo pode depender de formato privado e alterações de versão: export MP4 é principal; formato editável aberto é requisito de V1.
- Screen recording no cloud headless pode falhar sem display virtual: validar localmente antes de prometer.
- Fontes externas têm copyright: footage de terceiros não é banco livre.
- Work e Codex requerem acesso autorizado a contas/sistemas e podem necessitar autenticação ou aprovação.
- Algoritmo e monetização do YouTube não têm garantias.
