// Keep the same content in both languages; source receipt values are never translated.
const phrases = {
  csv_source: ["SHA-256 da imagem", "Image SHA-256"],
  csv_reason: ["Motivo", "Reason"],
  csv_reviewed: ["Sua revisão", "Your review"],
  csv_original: ["Leitura original", "Original reading"],
  csv_field: ["Informação", "Field"],
  upload_saved_text: [
    "Os campos vêm de uma extração salva; nenhuma nova leitura de texto foi executada neste teste.",
    "Fields come from a saved extraction; no new text reading was run in this test.",
  ],
  upload_saved_field: [
    "Valor preservado da extração de exemplo. Confira-o na imagem.",
    "Value preserved from the sample extraction. Check it against the image.",
  ],
  technical_contract: ["Contrato técnico da API", "Technical API contract"],
  nav_build: ["Como foi feito", "How it was built"],
  upload_event_sample: [
    "Exemplo público carregado com leitura salva",
    "Public example loaded with a saved reading",
  ],
  upload_export_help: [
    "CSV abre em planilhas e resume os valores. JSON inclui a leitura original, as evidências e o registro completo deste teste.",
    "CSV opens in spreadsheets and summarizes the values. JSON includes the original reading, evidence and full test record.",
  ],
  upload_csv: ["Baixar tabela (CSV)", "Download table (CSV)"],
  upload_sample_duration: [
    "Leitura salva do estudo · original preservado.",
    "Saved study reading · original preserved.",
  ],
  upload_sample_note: [
    "Exemplo público com leitura salva do estudo. Nenhum arquivo seu foi enviado e nenhuma nova leitura foi executada. Você pode conferir, corrigir e baixar sua versão.",
    "Public example with a saved study reading. No personal file was uploaded and no new reading was run. You can check, correct and download your version.",
  ],
  upload_retry: ["Verificar disponibilidade novamente", "Check availability again"],
  upload_sample: ["Usar recibo de exemplo", "Use a sample receipt"],
  build_next_body: [
    "Desempenho em documentos novos e brasileiros, tempo de revisão por pessoas, consumo de recursos na hospedagem e uso com vários usuários ainda precisam de avaliação. Esta demonstração não aprova pagamentos nem valida documentos fiscais.",
    "Performance on new and Brazilian documents, human review time, hosting resource use and multiuser operation still need evaluation. This demonstration does not approve payments or validate fiscal documents.",
  ],
  build_next: ["O que ainda precisa ser comprovado?", "What still needs to be established?"],
  build_repo: ["Explorar o repositório", "Explore the repository"],
  build_evidence_body: [
    "O repositório conecta decisões, código, testes e relatórios. Houve assistência de IA; compreender e revisar a entrega é responsabilidade do mantenedor.",
    "The repository connects decisions, code, tests and reports. AI assisted development; understanding and reviewing the result remains the maintainer’s responsibility.",
  ],
  build_evidence: ["Quer verificar a implementação?", "Want to inspect the implementation?"],
  build_boundary_link: ["Conferir proteções e limites", "Review safeguards and limits"],
  build_boundary_body: [
    "FastAPI valida entradas. O envio tem limites de imagem, tempo e concorrência; erros recebem mensagens claras e o OCR roda em processo separado.",
    "FastAPI validates inputs. Uploads have image, time and concurrency limits; errors have clear messages and OCR runs in a separate process.",
  ],
  build_boundary: ["Tratar falhas como parte do produto", "Treat failures as part of the product"],
  build_trace_link: ["Entender o histórico de revisão", "Understand the review history"],
  build_trace_body: [
    "A revisão local usa transações SQLite e controle de versão. O teste nesta aba exporta original, alterações e motivo, sem misturar dados de visitantes com o estudo.",
    "Local review uses SQLite transactions and revision checks. This tab exports the original, changes and reason without mixing visitor data with the study.",
  ],
  build_trace: ["Preservar o que mudou", "Preserve what changed"],
  build_domain_link: ["Examinar as regras do domínio", "Inspect the domain rules"],
  build_domain_body: [
    "Os valores originais são preservados. Python e Decimal permitem conferir cálculos sem arredondamentos de ponto flutuante; um campo ausente não vira zero.",
    "Original values are preserved. Python and Decimal support checks without floating-point rounding; a missing field does not become zero.",
  ],
  build_domain: ["Tratar dinheiro com regras explícitas", "Handle money with explicit rules"],
  build_eval_link: ["Consultar o método de avaliação", "Read the evaluation method"],
  build_eval_body: [
    "OCR e Gemini foram comparados nos mesmos 20 documentos. Falhas e campos sem resposta entram na avaliação, sem selecionar só os acertos.",
    "OCR and Gemini were compared on the same 20 documents. Failures and unanswered fields are included instead of selecting only successes.",
  ],
  build_eval: ["Avaliar antes de escolher", "Evaluate before choosing"],
  build_intro: [
    "Projeto de portfólio de Luiz. O trabalho conecta um problema de conferência a dados públicos, comparação de métodos, uma API e uma interface utilizável. Cada escolha tem uma evidência para você investigar.",
    "A portfolio project by Luiz. It connects a review problem to public data, method comparison, an API and a usable interface. Each choice has evidence you can investigate.",
  ],
  build_title: ["As decisões por trás da demonstração.", "The decisions behind the demonstration."],
  build_index: ["06 / COMO O PROJETO FOI CONSTRUÍDO", "06 / HOW THE PROJECT WAS BUILT"],
  guided_numbers: [
    "Os valores mantêm a escrita do recibo: 61,799 representa 61799 unidades, sem centavos nesta convenção. Não é uma conversão para reais.",
    "Values preserve the receipt notation: 61,799 represents 61799 whole units in this convention. No currency conversion is applied.",
  ],
  guided_action: ["Experimentar este caso", "Try this case"],
  guided_decide_body: [
    "Conferir a imagem, corrigir o campo e registrar por que mudou. O original continua disponível.",
    "Check the image, correct the field and record why it changed. The original stays available.",
  ],
  guided_decide: ["O que a pessoa precisa fazer", "What the reviewer needs to do"],
  guided_compare_body: [
    "A anotação oficial indica outro total. A leitura por Gemini recuperou esse valor.",
    "The official annotation gives a different total. Gemini extraction recovered this value.",
  ],
  guided_compare: ["O que a referência mostra", "What the reference shows"],
  guided_read_body: [
    "O leitor de texto selecionou esse valor como total.",
    "The text reader selected this value as the total.",
  ],
  guided_read: ["O que foi lido", "What was read"],
  guided_intro: [
    "Neste recibo público, a leitura automática confundiu dois valores. A diferença só fica clara quando você pode voltar ao documento.",
    "In this public receipt, automatic reading confused two values. The difference becomes clear when you can return to the document.",
  ],
  guided_title: ["O pagamento não era o total.", "The payment was not the total."],
  guided_index: ["02 / UM ERRO QUE EXPLICA O PROJETO", "02 / ONE ERROR THAT EXPLAINS THE PROJECT"],
  upload_invalid_field: [
    "{field}: o formato é inválido para a convenção escolhida. Confira separadores, sinais e casas decimais.",
    "{field}: the format is invalid for the chosen convention. Check separators, signs and decimal places.",
  ],
  upload_total_mismatch: [
    "O cálculo resultou em {expected}, mas o total informado é {observed}. Confira subtotal, desconto, imposto, serviço e total.",
    "The calculation gave {expected}, but the entered total is {observed}. Check subtotal, discount, tax, service and total.",
  ],
  upload_total_skipped: [
    "A conferência exige cinco campos explícitos e válidos: subtotal, desconto, imposto, serviço e total. Campo em branco não significa zero.",
    "To check the total, subtotal, discount, tax, service and total must be explicit and valid. A blank field does not mean zero.",
  ],
  nav_try: ["Testar meu recibo", "Try my receipt"],
  upload_index: ["04 / EXPERIMENTE E CONFIRA", "04 / TRY AND CHECK"],
  upload_title: [
    "Seu documento. Uma leitura que você acompanha.",
    "Your document. A reading you can follow.",
  ],
  upload_description: [
    "Envie uma imagem, veja o que foi encontrado e confira antes de usar.",
    "Send an image, see what was found and check it before using the data.",
  ],
  upload_examples_link: ["Prefere começar por um exemplo?", "Prefer to start with an example?"],
  upload_steps_label: ["Etapas do teste", "Test steps"],
  upload_step_choose: ["Escolher", "Choose"],
  upload_step_read: ["Ler", "Read"],
  upload_step_review: ["Conferir", "Check"],
  upload_step_export: ["Levar o resultado", "Take the result"],
  upload_choose: ["Escolha a imagem do recibo", "Choose a receipt image"],
  upload_no_file: ["Nenhuma imagem selecionada.", "No image selected."],
  upload_formats: [
    "PNG ou JPG · até 8 MB e 12 megapixels · uma imagem por vez.",
    "PNG or JPG · up to 8 MB and 12 megapixels · one image at a time.",
  ],
  upload_policy: ["Como os números estão escritos?", "How are the numbers written?"],
  upload_policy_brl: ["Vírgula decimal: 12,50 ou 1.234,56", "Decimal comma: 12,50 or 1.234,56"],
  upload_policy_usd: ["Ponto decimal: 12.50 ou 1,234.56", "Decimal point: 12.50 or 1,234.56"],
  upload_policy_idr: [
    "Sem centavos: 61,799 ou 61.799 (CORD)",
    "Whole amounts: 61,799 or 61.799 (CORD)",
  ],
  upload_policy_help: [
    "Escolha pelo documento, não pelo idioma da página. A moeda não será presumida.",
    "Choose based on the document, not the page language. Currency is not inferred.",
  ],
  upload_consent: [
    "Estou enviando apenas um recibo sem dados pessoais ou sensíveis.",
    "I am only sending a receipt without personal or sensitive information.",
  ],
  upload_read: ["Ler meu recibo", "Read my receipt"],
  upload_reset: ["Limpar este teste", "Clear this test"],
  upload_privacy: [
    "OCR local no servidor, sem enviar a provedores de IA. Imagem e texto são processados em memória, sem gravação pela aplicação. O resultado fica nesta aba até você limpar ou fechar.",
    "OCR runs locally on the server, without sending to AI providers. Image and text are processed in memory without being saved by the application. Results remain in this tab until you clear or close it.",
  ],
  upload_your_image: ["A imagem que você enviou", "The image you sent"],
  upload_photo_tip: [
    "Fotografe de frente, com boa luz e o recibo inteiro. Texto legível faz diferença.",
    "Take a straight, well-lit photo of the entire receipt. Readable text makes a difference.",
  ],
  upload_preview_alt: ["Prévia do recibo enviado", "Preview of the uploaded receipt"],
  upload_guide_label: ["O QUE VOCÊ VAI RECEBER", "WHAT YOU WILL GET"],
  upload_guide_title: [
    "Uma leitura inicial, com espaço para conferir.",
    "An initial reading, with room to check.",
  ],
  upload_guide_body: [
    "O sistema procura total, subtotal, imposto, serviço e desconto. Se não encontrar um valor com clareza, deixa o campo em branco. Você confere a imagem e decide o que corrigir.",
    "The system looks for total, subtotal, tax, service and discount. When no clear value is found, the field stays blank. Check the image and decide what to correct.",
  ],
  upload_limit: [
    "Recibos e idiomas diferentes podem exigir correção. Este teste ainda não valida documentos fiscais brasileiros nem mede acurácia.",
    "Different receipts and languages may need corrections. This test does not validate Brazilian fiscal documents or measure accuracy.",
  ],
  upload_resized: [
    "A imagem foi reduzida para limitar o processamento. Confira detalhes pequenos no original.",
    "The image was resized to bound processing. Check small details in the original.",
  ],
  upload_reason: ["O que você corrigiu e por quê?", "What did you correct and why?"],
  upload_reason_placeholder: [
    "Ex.: o valor era do pagamento; corrigi pelo total na imagem.",
    "E.g. the value was the payment; I corrected it using the image total.",
  ],
  upload_reason_required: [
    "Descreva a correção para incluir o motivo no arquivo.",
    "Describe your correction so the reason is included in the file.",
  ],
  upload_validate: ["Conferir formato e cálculos", "Check format and calculations"],
  upload_download: ["Baixar registro completo (JSON)", "Download full record (JSON)"],
  upload_check_limit: [
    "Os itens não são estruturados neste teste, e sua soma não é conferida. Um formato válido não comprova que o valor foi lido corretamente.",
    "Items are not structured in this test and their sum is not checked. A valid format does not prove the value was read correctly.",
  ],
  upload_text_title: ["Ver o texto que o OCR leu", "See the text OCR read"],
  upload_history_title: ["Acompanhar este teste", "Follow this test"],
  upload_history_note: [
    "Registro desta aba, sem identidade autenticada. O download preserva a leitura original, as alterações e os horários. Nada é acrescentado aos indicadores do estudo.",
    "A record of this tab, without authenticated identity. The download preserves the original reading, changes and timestamps. Nothing is added to the study indicators.",
  ],
  upload_connection: [
    "Não foi possível verificar a disponibilidade. Recarregue a página ou explore os exemplos abaixo.",
    "Availability could not be checked. Reload the page or explore the examples below.",
  ],
  upload_disabled: [
    "O envio não está disponível nesta instância. Você pode explorar os exemplos e os resultados abaixo.",
    "Uploads are unavailable on this instance. You can explore the examples and results below.",
  ],
  upload_wait: [
    "Recebendo e lendo a imagem · {n} s. Pode levar até um minuto. Mantenha esta aba aberta.",
    "Receiving and reading the image · {n} s. This may take up to one minute. Keep this tab open.",
  ],
  upload_found: [
    "{n} DE 5 CAMPOS IDENTIFICADOS · ISSO NÃO É NOTA DE ACERTO",
    "{n} OF 5 FIELDS IDENTIFIED · THIS IS NOT AN ACCURACY SCORE",
  ],
  upload_empty: [
    "Não encontramos texto legível. Tente uma foto mais clara.",
    "No readable text found. Try a clearer photo.",
  ],
  upload_needs_review: [
    "Leitura pronta. Agora, confira a imagem.",
    "Reading ready. Now check the image.",
  ],
  upload_edit: ["Seu recibo · {field}", "Your receipt · {field}"],
  upload_original: ["Leitura original: {value}", "Original reading: {value}"],
  upload_missing: ["Não identificado", "Not identified"],
  upload_ambiguous: [
    "Há valores conflitantes. Confira o texto reconhecido e preencha manualmente.",
    "Conflicting values were found. Check the recognized text and enter the value manually.",
  ],
  upload_evidence: ["Encontrado em: {text}", "Found in: {text}"],
  upload_no_evidence: [
    "Sem leitura segura para este campo. Preencha apenas se conseguir conferir na imagem.",
    "No clear reading for this field. Only fill it in if you can check it in the image.",
  ],
  upload_duration: [
    "OCR local e regras de leitura · {n} s, incluindo inicialização.",
    "Local OCR and reading rules · {n} s, including initialization.",
  ],
  upload_changed: [
    "{n} campo(s) alterado(s). Confira o formato e registre o motivo antes de baixar.",
    "{n} changed field(s). Check the format and record the reason before downloading.",
  ],
  upload_unchanged: [
    "Nenhuma alteração em relação à leitura original.",
    "No changes from the original reading.",
  ],
  upload_checks_summary: [
    "{pass} cálculo(s) conferido(s) · {issues} problema(s) de formato ou cálculo · {skipped} verificação(ões) sem dados suficientes. Ainda é necessário conferir a imagem.",
    "{pass} calculation(s) checked · {issues} format or calculation issue(s) · {skipped} check(s) without enough data. The image still needs to be checked.",
  ],
  upload_check_pending: [
    "Os valores foram alterados. Confira o formato e os cálculos antes de baixar.",
    "Values have changed. Check the format and calculations before downloading.",
  ],
  upload_downloaded: [
    "Download solicitado. O arquivo inclui a leitura original, sua versão e o registro deste teste.",
    "Download requested. The file includes the original reading, your version and this test record.",
  ],
  upload_event_selected: ["Imagem selecionada nesta aba", "Image selected in this tab"],
  upload_event_started: ["Leitura iniciada", "Reading started"],
  upload_event_read: [
    "Leitura recebida; conferência necessária",
    "Reading received; review needed",
  ],
  upload_event_failed: ["Leitura não concluída", "Reading not completed"],
  upload_event_checked: [
    "Formato e cálculos avaliados para os valores atuais",
    "Format and calculations evaluated for current values",
  ],
  upload_event_exported: ["Download solicitado", "Download requested"],
  upload_error_image_required: [
    "Escolha uma imagem PNG ou JPG. PDF e outros formatos ainda não são aceitos.",
    "Choose a PNG or JPG image. PDF and other formats are not supported yet.",
  ],
  upload_error_request_too_large: [
    "A imagem está vazia ou excede 8 MB. Escolha outra ou reduza o arquivo.",
    "The image is empty or exceeds 8 MB. Choose another image or reduce the file size.",
  ],
  upload_error_invalid_image: [
    "A imagem está danificada ou não corresponde ao formato informado. Salve uma nova cópia em PNG ou JPG.",
    "The image is damaged or does not match its stated format. Save a new PNG or JPG copy.",
  ],
  upload_error_image_dimensions: [
    "Use uma imagem de até 12 megapixels, até 12.000 pixels por lado e com pelo menos 32 pixels em cada lado.",
    "Use an image up to 12 megapixels, up to 12,000 pixels per side and at least 32 pixels on each side.",
  ],
  upload_error_image_too_complex: [
    "A imagem contém texto demais para este teste. Envie apenas um recibo.",
    "The image has too much text for this test. Send only one receipt.",
  ],
  upload_error_ocr_busy: [
    "Outra imagem está sendo processada. Aguarde um minuto e tente novamente.",
    "Another image is being processed. Wait a minute and try again.",
  ],
  upload_error_upload_rate_limited: [
    "O limite de testes desta instância foi atingido. Aguarde um minuto e tente novamente.",
    "This instance has reached its test limit. Wait a minute and try again.",
  ],
  upload_error_ocr_timeout: [
    "A leitura excedeu o tempo disponível e foi interrompida. Tente uma imagem menor e mais nítida.",
    "Reading exceeded the available time and was stopped. Try a smaller, clearer image.",
  ],
  upload_error_request_timeout: [
    "A resposta demorou além do limite. Não houve reenvio automático. Aguarde antes de tentar novamente.",
    "The response took too long. No automatic retry was made. Wait before trying again.",
  ],
  upload_error_network_error: [
    "A conexão falhou. Seu arquivo continua selecionado; verifique a conexão antes de tentar novamente.",
    "The connection failed. Your file remains selected; check your connection before trying again.",
  ],
  upload_error_ocr_unavailable: [
    "A leitura está indisponível nesta instância. Explore os exemplos enquanto isso.",
    "Reading is unavailable on this instance. Explore the examples meanwhile.",
  ],
  upload_engine: ["Como ler o recibo?", "How should the receipt be read?"],
  upload_engine_gemini: [
    "IA (Gemini): mais precisa. A imagem é enviada ao Google.",
    "AI (Gemini): more accurate. The image is sent to Google.",
  ],
  upload_engine_ocr: [
    "OCR local: a imagem fica neste servidor.",
    "Local OCR: the image stays on this server.",
  ],
  upload_engine_help: [
    "Se a IA estiver indisponível ou o limite diário acabar, o OCR local faz a leitura e a tela avisa.",
    "If the AI is unavailable or the daily limit is reached, local OCR reads it instead and the page tells you.",
  ],
  upload_consent_gemini: [
    "Estou enviando apenas um recibo sem dados pessoais ou sensíveis e aceito que a imagem seja enviada ao Google (Gemini, plano gratuito). Pelos termos do plano gratuito, o Google pode usar o conteúdo para melhorar seus produtos.",
    "I am only sending a receipt without personal or sensitive information, and I accept that the image is sent to Google (Gemini, free tier). Under the free-tier terms, Google may use the content to improve its products.",
  ],
  upload_privacy_gemini: [
    "Este servidor remove os metadados, reduz a imagem e a envia ao Google Gemini (plano gratuito). Ele não grava a imagem nem o resultado; o Google segue os próprios termos. Há um limite diário de leituras por IA e, ao atingi-lo, o OCR local assume.",
    "This server strips metadata, shrinks the image and sends it to Google Gemini (free tier). It does not save the image or the result; Google follows its own terms. There is a daily limit on AI readings, and local OCR takes over when it is reached.",
  ],
  upload_wait_gemini: [
    "Lendo a imagem com IA · {n} s. Pode levar até dois minutos se o OCR local precisar assumir. Mantenha esta aba aberta.",
    "Reading the image with AI · {n} s. It may take up to two minutes if local OCR has to take over. Keep this tab open.",
  ],
  upload_duration_gemini: [
    "Leitura por IA (Gemini, plano gratuito) · {n} s.",
    "AI reading (Gemini, free tier) · {n} s.",
  ],
  upload_duration_fallback: [
    "OCR local, porque a IA não foi usada · {n} s, incluindo inicialização.",
    "Local OCR, because the AI was not used · {n} s, including initialization.",
  ],
  upload_text_title_gemini: ["Como esta leitura foi feita", "How this reading was made"],
  upload_text_gemini: [
    "A IA devolve os valores já organizados, não o texto reconhecido. Por isso não há trecho de evidência: confira cada campo na imagem.",
    "The AI returns organized values, not the recognized text. That is why there is no evidence excerpt: check each field against the image.",
  ],
  upload_gemini_field: [
    "Valor sugerido pela IA. Confira-o na imagem.",
    "Value suggested by the AI. Check it against the image.",
  ],
  upload_fallback_generic: [
    "A IA não foi usada nesta leitura; o OCR local assumiu. No estudo, o OCR errou mais. Confira cada campo com atenção.",
    "The AI was not used for this reading; local OCR took over. In the study, OCR made more mistakes. Check every field carefully.",
  ],
  upload_fallback_gemini_daily_limit: [
    "O limite diário de leituras por IA desta demonstração foi atingido. O OCR local assumiu; no estudo, ele errou mais. Confira cada campo com atenção.",
    "This demo's daily limit of AI readings was reached. Local OCR took over; in the study it made more mistakes. Check every field carefully.",
  ],
  upload_fallback_gemini_client_limit: [
    "Você atingiu o limite diário de leituras por IA. O OCR local assumiu; no estudo, ele errou mais. Confira cada campo com atenção.",
    "You reached the daily limit of AI readings. Local OCR took over; in the study it made more mistakes. Check every field carefully.",
  ],
  upload_fallback_gemini_rate_limited: [
    "Muitas leituras por IA em pouco tempo. O OCR local assumiu; tente a IA de novo em um minuto.",
    "Too many AI readings in a short time. Local OCR took over; try the AI again in a minute.",
  ],
  upload_fallback_gemini_busy: [
    "A IA está ocupada com outras leituras. O OCR local assumiu; tente a IA de novo em instantes.",
    "The AI is busy with other readings. Local OCR took over; try the AI again shortly.",
  ],
  upload_fallback_gemini_paused: [
    "A IA está em pausa temporária por limite do provedor. O OCR local assumiu; confira cada campo com atenção.",
    "The AI is temporarily paused because of a provider limit. Local OCR took over; check every field carefully.",
  ],
  upload_fallback_gemini_unavailable: [
    "A IA está indisponível agora. O OCR local assumiu; no estudo, ele errou mais. Confira cada campo com atenção.",
    "The AI is unavailable right now. Local OCR took over; in the study it made more mistakes. Check every field carefully.",
  ],
  upload_fallback_gemini_invalid_response: [
    "A IA não conseguiu ler esta imagem. O OCR local assumiu; confira cada campo com atenção.",
    "The AI could not read this image. Local OCR took over; check every field carefully.",
  ],
  upload_fallback_gemini_error: [
    "A IA não conseguiu ler esta imagem. O OCR local assumiu; confira cada campo com atenção.",
    "The AI could not read this image. Local OCR took over; check every field carefully.",
  ],
  upload_fallback_gemini_timeout: [
    "A IA demorou demais. O OCR local assumiu; confira cada campo com atenção.",
    "The AI took too long. Local OCR took over; check every field carefully.",
  ],
  upload_event_fallback: [
    "IA não utilizada; leitura feita pelo OCR local",
    "AI not used; read with local OCR",
  ],
  upload_error_consent_required: [
    "Para usar a IA, aceite o envio da imagem ao Google. Ou escolha o OCR local.",
    "To use the AI, accept sending the image to Google, or choose local OCR.",
  ],
  upload_error_generic: [
    "Não foi possível concluir o teste. A imagem não foi salva pela aplicação. Tente novamente ou explore os exemplos.",
    "The test could not be completed. The image was not saved by the application. Try again or explore the examples.",
  ],
  uncertain_text: [
    "Não foi possível confirmar se a alteração foi salva. Recarregue e confira o histórico antes de tentar novamente.",
    "We could not confirm whether the change was saved. Reload and check the history before trying again.",
  ],
  error_request_timeout: [
    "A solicitação excedeu o tempo de espera. Confira o estado da revisão antes de reenviar uma alteração.",
    "The request timed out. Check the review state before resubmitting a change.",
  ],
  error_network_error: [
    "A conexão falhou. Não foi possível confirmar o resultado da solicitação.",
    "The connection failed. The request outcome could not be confirmed.",
  ],
  error_invalid_response: [
    "O servidor enviou uma resposta inesperada. Confira a revisão antes de reenviar.",
    "The server sent an unexpected response. Check the review before resubmitting.",
  ],
  error_internal_error: [
    "O servidor encontrou um erro inesperado. Confira o histórico antes de reenviar uma alteração.",
    "The server encountered an unexpected error. Check the history before resubmitting a change.",
  ],
  error_request_too_large: [
    "O pedido excedeu o limite permitido. Reduza a quantidade de dados da correção.",
    "The request exceeded the allowed size. Reduce the correction payload.",
  ],
  error_body_timeout: [
    "O servidor não recebeu o pedido completo a tempo. A ação não foi iniciada.",
    "The server did not receive the complete request in time. The action was not started.",
  ],

  page_title: [
    "ReceiptTrace · Extração que você pode conferir",
    "ReceiptTrace · Extraction you can check",
  ],
  skip: ["Pular para o teste", "Skip to the test"],
  navigation: ["Navegação principal", "Main navigation"],
  nav_approach: ["A proposta", "The approach"],
  nav_demo: ["Entender o caso", "Understand the case"],
  nav_results: ["Resultados", "Results"],
  eyebrow: ["IA aplicada, com evidências", "Applied AI, backed by evidence"],
  hero_a: ["Da imagem do recibo", "From a receipt image"],
  hero_b: ["ao dado que você confere.", "to data you can check."],
  hero_description: [
    "Para quem organiza comprovantes e precisa conferir os valores antes de usá-los. Veja como a leitura automática pode errar, acompanhe uma correção e teste com uma imagem sua.",
    "For people organizing receipts who need to check values before using them. See how automatic reading can fail, follow a correction and try your own image.",
  ],
  explore: ["Entender com um exemplo", "Understand through an example"],
  see_results: ["Testar meu recibo", "Try my receipt"],
  hero_note: [
    "Comece com um exemplo pronto. Não precisa de arquivo nem chave de API.",
    "Start with a ready example. No file or API key needed.",
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
  workspace_index: ["03 / COMPARE AS DUAS LEITURAS", "03 / COMPARE THE TWO READINGS"],
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
  ocr: ["Leitura de texto (OCR)", "Text reading (OCR)"],
  ai: ["Leitura por IA (Gemini)", "AI reading (Gemini)"],
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
  results_index: ["05 / O QUE O ESTUDO DEMONSTROU", "05 / WHAT THE STUDY SHOWED"],
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
    "Não é teste em dados reservados, validação de documentos fiscais brasileiros ou medição de economia de trabalho. Os exemplos usam respostas salvas. Um recibo enviado é lido por IA (Gemini, plano gratuito) só se você aceitar o envio ao Google; caso contrário, ou se a IA estiver indisponível, usa OCR local.",
    "This is not a held-out test, validation of Brazilian fiscal documents, or a measurement of labor savings. The examples use saved responses. An uploaded receipt is read by AI (Gemini, free tier) only if you accept sending it to Google; otherwise, or if the AI is unavailable, local OCR is used.",
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
