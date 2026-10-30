// Keep the same content in both languages; source receipt values are never translated.
const phrases = {
  page_title: [
    "ReceiptTrace · Extração que você pode conferir",
    "ReceiptTrace · Extraction you can check",
  ],
  skip: ["Pular para o exemplo", "Skip to the example"],
  navigation: ["Navegação principal", "Main navigation"],
  nav_approach: ["A proposta", "The approach"],
  nav_demo: ["Explorar exemplo", "Explore an example"],
  nav_results: ["Resultados", "Results"],
  eyebrow: ["IA aplicada, com evidências", "Applied AI, backed by evidence"],
  hero_a: ["Da imagem do recibo", "From a receipt image"],
  hero_b: ["ao dado que você confere.", "to data you can check."],
  hero_description: [
    "Leia os valores, compare OCR e IA e acompanhe cada correção. Um estudo com recibos reais, resultados verificáveis e limites claros.",
    "Read the values, compare OCR and AI, and trace each correction. A study with real receipts, verifiable results, and clear limits.",
  ],
  explore: ["Explorar um recibo", "Explore a receipt"],
  see_results: ["Ver o que foi medido", "See what was measured"],
  hero_note: [
    "Exemplos já processados. Não exige chave de API.",
    "Saved examples. No API key required.",
  ],
  hero_visual: [
    "Exemplo real com total recuperado pela IA",
    "Real example with a total recovered by AI",
  ],
  real_document: ["UM DOCUMENTO REAL. DUAS LEITURAS.", "ONE REAL DOCUMENT. TWO READINGS."],
  source_document: ["Recibo de origem", "Source receipt"],
  hero_alt: ["Recibo público CORD, exemplo 0006", "Public CORD receipt, example 0006"],
  recovered_total: ["Total recuperado pela IA", "Total recovered by AI"],
  matches_annotation: ["Confere com a anotação oficial", "Matches the official annotation"],
  metrics_label: ["Resumo do experimento", "Experiment summary"],
  metric_correct: ["Totais corretos com IA", "Correct totals with AI"],
  metric_sample: ["na amostra de desenvolvimento", "in the development sample"],
  metric_gain: ["Além do OCR", "Beyond OCR"],
  metric_gain_note: ["totais adicionais recuperados", "additional totals recovered"],
  metric_time: ["Tempo típico com IA", "Typical AI processing time"],
  metric_time_note: ["mediana por recibo neste lote", "median per receipt in this batch"],
  metric_cost: ["Custo estimado de API", "Estimated API cost"],
  metric_cost_note: ["Free Tier; não é custo operacional", "Free Tier; not total operating cost"],
  approach_index: ["01 / O PROBLEMA", "01 / THE PROBLEM"],
  approach_title: [
    "Ler é uma etapa. Conferir é outra.",
    "Reading is one step. Checking is another.",
  ],
  approach_body: [
    "Um recibo pode confundir o valor do pagamento com o total. A proposta é apoiar quem organiza comprovantes: extrair campos, tornar as dúvidas visíveis e preservar o que foi corrigido.",
    "A receipt can make a payment amount look like the total. The goal is to support receipt reviewers: extract fields, surface uncertainty, and preserve a record of corrections.",
  ],
  flow_label: ["Fluxo da solução", "Solution workflow"],
  flow_image: ["Imagem", "Image"],
  flow_extraction: ["Extração", "Extraction"],
  flow_check: ["Conferência", "Checking"],
  flow_history: ["Histórico", "History"],
  approach_note: [
    "Cenário proposto para equipes administrativas e financeiras. Ganho de produtividade ainda não foi medido.",
    "A proposed use case for administrative and finance teams. Productivity gains have not been measured.",
  ],
  workspace_index: ["02 / EXPLORE UM CASO REAL", "02 / EXPLORE A REAL CASE"],
  workspace_title: ["Da leitura à revisão.", "From extraction to review."],
  workspace_description: [
    "Escolha um exemplo e veja o que cada abordagem encontrou.",
    "Choose an example and see what each approach found.",
  ],
  case_label: ["Escolha um exemplo", "Choose an example"],
  case_1: ["Pagamento ou total?", "Payment or total?"],
  case_2: ["Subtotal ou total?", "Subtotal or total?"],
  case_3: ["Um total pouco legível", "A hard-to-read total"],
  curation_note: [
    "Três casos escolhidos para ilustrar falhas do OCR. Os indicadores vêm do lote completo de 20 recibos.",
    "Three cases selected to illustrate OCR failures. Summary metrics use the full batch of 20 receipts.",
  ],
  local_mode: ["Revisão local disponível", "Local review available"],
  readonly_mode: ["Demonstração de consulta", "Read-only demonstration"],
  retry: ["Tentar novamente", "Try again"],
  load_failed: [
    "Não foi possível carregar o exemplo. Confira se o servidor está disponível e tente novamente.",
    "The example could not be loaded. Check that the server is available and try again.",
  ],
  original_image: ["Documento original", "Original document"],
  enlarge: ["Ampliar", "Enlarge"],
  selected_alt: ["Imagem original do recibo selecionado", "Original image of the selected receipt"],
  method_label: ["Método de extração", "Extraction method"],
  ocr: ["OCR local", "Local OCR"],
  ai: ["Gemini · IA", "Gemini · AI"],
  field_note: [
    "Valores como foram escritos no recibo. A moeda não foi presumida.",
    "Values as written on the receipt. Currency has not been assumed.",
  ],
  field: ["Informação", "Information"],
  original_extraction: ["Extração original", "Original extraction"],
  reference: ["Referência", "Reference"],
  current_value: ["Revisão atual", "Current review"],
  evaluation_note: [
    "A comparação mede a extração original. Uma correção não altera os resultados publicados.",
    "The comparison measures the original extraction. Corrections do not change published results.",
  ],
  readonly_note: [
    "Esta demonstração está em modo de consulta. Para salvar correções, execute a revisão local.",
    "This demonstration is read-only. Run the local review application to save corrections.",
  ],
  review_invite: [
    "Quer conferir ou corrigir estes campos?",
    "Want to check or correct these fields?",
  ],
  review_invite_note: [
    "O original é preservado. Cada alteração fica registrada.",
    "The original is preserved. Each change is recorded.",
  ],
  open_review: ["Abrir revisão local", "Open local review"],
  review_fields: ["Revisão dos campos", "Field review"],
  review_scope: [
    "Esta tela permite corrigir os cinco campos de totais. Itens e cálculos sem dados suficientes não ficam automaticamente aprovados.",
    "This screen lets you correct the five totals fields. Items and calculations with missing data are not automatically approved.",
  ],
  actor: ["Responsável", "Reviewer"],
  reason: ["Motivo ou registro da conferência", "Reason or record of checking"],
  actor_placeholder: ["Como você se identifica", "How you identify yourself"],
  reason_placeholder: [
    "O que você conferiu e por que alterou?",
    "What did you check, and why did you change it?",
  ],
  identity_note: [
    "Identificação declarada localmente, sem autenticação.",
    "Identity is declared locally, without authentication.",
  ],
  ack_unverified: [
    "Estou ciente de que há cálculos não verificados. Isso não aprova esses cálculos.",
    "I acknowledge that some calculations were not checked. This does not approve them.",
  ],
  ack_findings: [
    "Estou ciente das divergências ou dos valores inválidos, descritos no meu motivo.",
    "I acknowledge the discrepancies or invalid values described in my reason.",
  ],
  save: ["Registrar correção", "Record correction"],
  complete: ["Concluir revisão", "Complete review"],
  discard: ["Descartar rascunho", "Discard draft"],
  completion_note: [
    "Concluir a revisão não é aprovação de pagamento ou de conformidade fiscal.",
    "Completing a review is not payment approval or a fiscal-compliance check.",
  ],
  conflict_text: [
    "A revisão mudou em outra sessão. Confira a versão atual antes de continuar.",
    "The review changed in another session. Check the current version before continuing.",
  ],
  reload_review: ["Recarregar e descartar rascunho", "Reload and discard draft"],
  history: ["Histórico da revisão", "Review history"],
  export: ["Baixar revisão em JSON", "Download review as JSON"],
  checks: ["O que pôde ser verificado?", "What could be checked?"],
  checks_note: [
    "Sem componentes suficientes, o resultado é “Não verificada”. Isso é diferente de “Cálculo confere”.",
    "With insufficient components, the result is “Not checked”. That is different from “Arithmetic matches”.",
  ],
  items: [
    "Itens extraídos · qualidade ainda não avaliada",
    "Extracted items · accuracy not yet measured",
  ],
  technical: ["Detalhes técnicos e origem", "Technical details and source"],
  raw_note: [
    "Campos da extração original, antes das correções:",
    "Original extraction fields, before corrections:",
  ],
  results_index: ["03 / O QUE OS DADOS RESPONDEM", "03 / WHAT THE DATA TELLS US"],
  results_title: [
    "Mais valores corretos. Mais tempo por leitura.",
    "More correct values. More time per reading.",
  ],
  full_report: ["Dados da comparação", "Comparison data"],
  comparison_caption: [
    "Acertos por informação · mesmos 20 recibos",
    "Correct fields · the same 20 receipts",
  ],
  denominator_note: [
    "Nem todo recibo tem todos os campos anotados. Sem referência válida, não há nota de acerto para o campo.",
    "Not every receipt has every field annotated. Without a valid reference, field accuracy cannot be scored.",
  ],
  question_quality: ["A IA leu melhor?", "Did AI read more accurately?"],
  question_speed: ["E o tempo de processamento?", "What about processing time?"],
  question_trust: ["Podemos dispensar a conferência?", "Can we skip human checking?"],
  answer_quality: [
    "Nesta amostra, a IA acertou {ai} de {n} totais; o OCR acertou {ocr}. Isso apoia continuar o experimento, não generalizar para qualquer documento.",
    "In this sample, AI got {ai} of {n} totals right; OCR got {ocr}. This supports continuing the experiment, not generalizing to every document.",
  ],
  answer_speed: [
    "Mediana de {ai} s com IA e {ocr} s com OCR. As etapas medidas são diferentes. O tempo de revisão por pessoas ainda não foi medido.",
    "Median of {ai} s with AI and {ocr} s with OCR. The timing scopes differ. Human review time has not been measured.",
  ],
  answer_trust: [
    "Ainda não. A amostra já foi usada no desenvolvimento, os itens não foram avaliados e as verificações aritméticas do lote ficaram sem componentes suficientes.",
    "Not yet. The sample was already used during development, item accuracy is unmeasured, and the batch's arithmetic checks lacked required components.",
  ],
  limits_title: ["Resultado de um estudo de desenvolvimento.", "Results from a development study."],
  limits_body: [
    "Não é teste em dados reservados, validação de documentos fiscais brasileiros ou medição de economia de trabalho. A demonstração usa respostas salvas e não faz novas chamadas de IA.",
    "This is not a held-out test, validation of Brazilian fiscal documents, or a measurement of labor savings. The demonstration uses saved responses and makes no new AI calls.",
  ],
  footer_description: [
    "Engenharia de IA com resultados que podem ser conferidos.",
    "AI engineering with results you can check.",
  ],
  evidence: ["Evidências da avaliação", "Evaluation evidence"],
  attribution: ["Dados CORD · CC BY 4.0", "CORD data · CC BY 4.0"],
  footer_note: [
    "Dados públicos dos autores do CORD / NAVER CLOVA. Três imagens originais, sem alteração. Houve assistência de IA no desenvolvimento; revisão e responsabilidade pertencem ao mantenedor.",
    "Public data by the CORD authors / NAVER CLOVA. Three unchanged original images. AI assisted development; review and responsibility remain with the maintainer.",
  ],
  total: ["Total", "Total"],
  subtotal: ["Subtotal", "Subtotal"],
  tax: ["Imposto", "Tax"],
  service: ["Serviço", "Service"],
  discount: ["Desconto", "Discount"],
  absent: ["Não extraído", "Not extracted"],
  no_reference: ["Sem referência", "No reference"],
  no_references: ["Sem referências válidas", "No valid references"],
  ratio: ["{n} de {d}", "{n} of {d}"],
  seconds: ["{value} s", "{value} s"],
  revision: ["Versão {n}", "Revision {n}"],
  correct: ["Confere", "Matches"],
  wrong_value: ["Diverge", "Differs"],
  missed: ["Sem resposta", "No extracted value"],
  invalid_reference: ["Referência inválida", "Invalid reference"],
  unannotated_prediction: ["Sem referência", "No reference"],
  unannotated_abstention: ["Sem referência", "No reference"],
  extraction_ok: ["Extração concluída", "Extraction completed"],
  extraction_error: ["Falha na extração", "Extraction failed"],
  extraction_empty: ["Extração sem texto", "No text extracted"],
  arithmetic_passed: ["Cálculos conferem", "Arithmetic matches"],
  arithmetic_partial: ["Cálculos parcialmente verificados", "Arithmetic partly checked"],
  arithmetic_not_checked: ["Cálculos não verificados", "Arithmetic not checked"],
  arithmetic_findings: ["Verificações com achados", "Checks have findings"],
  arithmetic_unavailable: ["Verificação indisponível", "Checks unavailable"],
  review_pending: ["Revisão pendente", "Review pending"],
  review_completed: ["Revisão concluída", "Review completed"],
  review_unavailable: ["Revisão indisponível", "Review unavailable"],
  review_not_started: ["Revisão não iniciada", "Review not started"],
  changed_fields: [
    "{n} campo(s) alterado(s). Salve ou descarte antes de concluir.",
    "{n} field(s) changed. Save or discard before completing.",
  ],
  no_changes: ["Nenhuma alteração pendente.", "No unsaved changes."],
  completed_hint: [
    "Esta versão foi revisada. Uma nova correção reabrirá a revisão.",
    "This version was reviewed. A new correction will reopen the review.",
  ],
  saved: [
    "Correção registrada. Os cálculos foram reavaliados; confira os estados antes de concluir.",
    "Correction recorded. Checks were recalculated; inspect their status before completing.",
  ],
  completed: [
    "Conclusão registrada. As verificações não realizadas continuam identificadas.",
    "Completion recorded. Unperformed checks remain identified.",
  ],
  reloaded: [
    "Versão atual carregada. O rascunho foi descartado; confira os campos novamente.",
    "Current revision loaded. The draft was discarded; check the fields again.",
  ],
  no_events: [
    "Nenhuma correção ou conclusão registrada.",
    "No corrections or completion recorded.",
  ],
  event_corrected: ["Correção registrada", "Correction recorded"],
  event_completed: ["Revisão concluída", "Review completed"],
  event_unverified: [
    "Ciência de cálculos não verificados registrada.",
    "Acknowledgement of unchecked calculations recorded.",
  ],
  event_findings: ["Ciência dos achados registrada.", "Acknowledgement of findings recorded."],
  pass: ["Cálculo confere", "Arithmetic matches"],
  mismatch: ["Divergência no cálculo", "Arithmetic mismatch"],
  skipped: ["Não verificada", "Not checked"],
  invalid: ["Valor inválido para verificação", "Invalid value for check"],
  item_total: ["Valor do item", "Item total"],
  receipt_total: ["Total do recibo", "Receipt total"],
  numeric_field: ["Formato numérico", "Numeric format"],
  missing_or_invalid_component: [
    "Faltam componentes numéricos válidos.",
    "Valid numeric components are missing.",
  ],
  incomplete_or_nested_items: [
    "Lista de itens incompleta ou com subitens.",
    "Item list is incomplete or contains nested items.",
  ],
  nested_item_semantics_unknown: [
    "A composição deste item ainda não tem regra definida.",
    "The composition of this nested item has no defined rule yet.",
  ],
  unsupported_numeric_format: ["Formato numérico não suportado.", "Unsupported numeric format."],
  negative_amount: [
    "Valor negativo não permitido neste campo.",
    "Negative amount is not allowed for this field.",
  ],
  unsupported_quantity_format: [
    "Formato de quantidade não suportado.",
    "Unsupported quantity format.",
  ],
  nonpositive_quantity: ["Quantidade precisa ser positiva.", "Quantity must be positive."],
  text_too_long: ["Texto acima do limite aceito.", "Text exceeds the supported limit."],
  no_items: ["Nenhum item foi extraído.", "No items were extracted."],
  unnamed_item: ["Item sem descrição", "Item without description"],
  quantity: ["Quantidade", "Quantity"],
  image_hash: ["SHA-256 da imagem", "Image SHA-256"],
  result_hash: ["SHA-256 do resultado original", "Original result SHA-256"],
  manifest_hash: ["SHA-256 do manifesto da extração", "Extraction manifest SHA-256"],
  evaluation_hash: ["SHA-256 do relatório de avaliação", "Evaluation report SHA-256"],
  error_read_only: ["Este modo permite apenas consulta.", "This mode is read-only."],
  error_revision_conflict: [
    "A revisão mudou. Recarregue a versão atual e confira os campos.",
    "The review changed. Reload the current revision and check the fields.",
  ],
  error_invalid_action: [
    "A ação não foi aceita. Confira os campos, o motivo e os reconhecimentos necessários.",
    "The action was rejected. Check the fields, reason and required acknowledgements.",
  ],
  error_invalid_request: [
    "Confira os campos obrigatórios e o formato dos valores.",
    "Check required fields and value formats.",
  ],
  error_integrity_error: [
    "Não foi possível verificar o histórico. Nenhuma nova alteração foi aceita.",
    "The history could not be verified. No new change was accepted.",
  ],
  error_storage_unavailable: [
    "O armazenamento local está indisponível. Tente novamente.",
    "Local storage is unavailable. Try again.",
  ],
  error_not_found: [
    "O exemplo ou a revisão não foi encontrado.",
    "The example or review was not found.",
  ],
  error_origin_rejected: [
    "Abra a aplicação no endereço local indicado pelo servidor.",
    "Open the application at the local address shown by the server.",
  ],
  error_generic: [
    "Não foi possível concluir a ação. Tente novamente e confira a revisão antes de reenviar.",
    "The action could not be completed. Try again and check the review before resubmitting.",
  ],
};

export const messages = Object.fromEntries(
  ["pt", "en"].map((lang, index) => [
    lang,
    Object.fromEntries(Object.entries(phrases).map(([key, values]) => [key, values[index]])),
  ]),
);
export const supportedLanguages = ["pt", "en"];
export function translate(lang, key, values = {}) {
  const phrase = messages[lang]?.[key];
  if (phrase === undefined) throw new Error(`Missing translation: ${lang}.${key}`);
  return phrase.replace(/\{(\w+)\}/g, (_, name) => String(values[name] ?? `{${name}}`));
}

export function applyLanguage(lang) {
  document.documentElement.lang = lang === "pt" ? "pt-BR" : "en";
  document.title = translate(lang, "page_title");
  for (const [attribute, target] of [
    ["data-i18n", null],
    ["data-i18n-aria", "aria-label"],
    ["data-i18n-alt", "alt"],
    ["data-i18n-placeholder", "placeholder"],
  ]) {
    for (const element of document.querySelectorAll(`[${attribute}]`)) {
      const value = translate(lang, element.getAttribute(attribute));
      if (target) element.setAttribute(target, value);
      else element.textContent = value;
    }
  }
  for (const button of document.querySelectorAll("[data-lang]"))
    button.setAttribute("aria-pressed", String(button.dataset.lang === lang));
}
