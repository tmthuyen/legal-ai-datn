# Spec: Bộ dữ liệu, huấn luyện và serving cho Legal AI

> **Trạng thái:** Bản nháp đã cập nhật theo phản hồi; chờ duyệt yêu cầu  
> **Phạm vi:** Đặc tả yêu cầu; chưa triển khai code, chưa gọi LLM API và chưa tạo dataset  
> **Nguồn sinh dataset:** Bộ luật Dân sự 2015 và Luật Hôn nhân và gia đình 2014  
> **Serving mục tiêu:** Ollama local trên CPU, máy 10GB RAM; có thể thử huấn luyện trên Google Colab GPU  
> **Đối tượng sử dụng:** Nhóm xây dựng, kiểm tra và thử nghiệm mô hình Legal AI

## Tóm tắt yêu cầu

Pipeline phải tách retrieval/rerank, lấy rules, trích xuất facts, kiểm chứng tri-state và tạo câu trả lời có căn cứ. Mô hình chỉ giải thích kết quả đã kiểm chứng, không phán quyết; yêu cầu gốc được giữ nguyên ở mục 13.

## 1. Mục tiêu

Xây dựng quy trình dùng LLM API tạo bộ câu hỏi đáp hợp lệ từ nội dung Bộ luật Dân sự 2015 và Luật Hôn nhân và gia đình, kết hợp các rule/predicate/condition tương ứng. Mục tiêu là huấn luyện và thử một mô hình đa nhiệm, đồng thời giữ retrieval và kiểm chứng luật thành các tầng riêng, có thể truy vết.

1. Retrieval code lấy các luật/tài liệu ứng viên từ câu hỏi.
2. Tìm rule, predicate và condition thuộc các luật ứng viên.
3. Mô hình trích xuất facts, entities, chủ thể, đối tượng, quan hệ và sự kiện theo cấu trúc mà rule evaluator/Prolog có thể kiểm chứng.
4. Rule evaluator/Prolog xác định điều kiện `true`, `false` hoặc `unknown`.
5. Mô hình dùng luật, facts và kết quả kiểm chứng để giải thích theo tam đoạn luận và tạo câu trả lời có căn cứ.

Mục tiêu chống ảo giác là của toàn pipeline, không chỉ của LLM: truy xuất chỉ tạo ứng viên; khớp luật phải được kiểm chứng; kết quả thiếu hoặc không khớp giữ là `unknown`; câu trả lời không được vượt quá căn cứ đã kiểm chứng. Mô hình giải thích, không đóng vai thẩm phán và không có quyền phán quyết.

## 2. Capability map và thứ tự phụ thuộc

| Capability | Trách nhiệm | Loại thành phần | Phụ thuộc |
|---|---|---|---|
| `legal-retrieval` | Semantic + BM25 + graph retrieval và rerank; trả `relevant_laws`, `relevant_documents` dạng ứng viên | Code/retrieval models; không phải task fine-tune LLM trong spec này | — |
| `rule-context-resolution` | Lấy rule/predicate/condition/node thuộc các luật ứng viên; không mặc định luật ứng viên chắc chắn liên quan | Code + nguồn rule/Graph | `legal-retrieval` |
| `scenario-fact-dataset` | Dùng LLM API tạo tình huống/câu hỏi và nhãn facts có evidence; con người duyệt | Dataset pipeline | `rule-context-resolution` |
| `scenario-fact-extraction` | Fine-tune mô hình để trích xuất facts/entity/relations/events đúng cấu trúc cần kiểm chứng | Task của LLM | `scenario-fact-dataset`, `rule-context-resolution` |
| `rule-verification` | Chạy facts qua evaluator hoặc Prolog; trả `true`, `false`, `unknown` theo từng điều kiện/rule | Rule engine/Prolog; không để LLM tự thay kết quả kiểm chứng | `scenario-fact-extraction` |
| `syllogistic-answer` | Tạo giải thích/câu trả lời từ context và kết quả kiểm chứng, gồm luật áp dụng, điều kiện chưa thỏa và unknown | Task của LLM | `rule-verification` |
| `model-training-serving` | Fine-tune đa nhiệm bằng Unsloth, thử model, phục vụ local bằng Ollama và đánh giá | Training/serving | Các task trên |

**Build order:** `legal-retrieval` → `rule-context-resolution` → `scenario-fact-dataset` → `scenario-fact-extraction` → `rule-verification` → `syllogistic-answer` → `model-training-serving`.

## 3. Nguồn luật và trạng thái dữ liệu

### 3.1 Nguồn làm căn cứ

- Sinh dataset từ nội dung **Bộ luật Dân sự 2015** và **Luật Hôn nhân và gia đình 2014**, cùng rule/predicate/condition của hai luật này.
- Retrieval có thể trả về `relevant_laws`/`relevant_documents` khác làm ứng viên/context; không đồng nghĩa chúng chắc chắn liên quan và không mở rộng nguồn sinh nhãn vàng ngoài hai luật trên nếu chưa được duyệt.
- Đối chiếu danh sách văn bản tại `backend/data/documents_config.json`, rule tại `backend/data/rules/`, catalog predicate/effect và node đang tồn tại trong Neo4j.
- Không dựa riêng vào README hoặc danh sách corpus ghi tĩnh nếu khác với cấu hình/dữ liệu Graph hiện tại. Mỗi lần tạo dataset phải ghi snapshot nguồn và thời điểm trích xuất.
- Mỗi căn cứ pháp lý trong mẫu phải lưu `rule_id`, `node_id`, nhãn Điều/Khoản/Điểm và nội dung/citation lấy từ Graph.
- Ghi nhận phiên bản văn bản (`ORIGINAL`, `AMENDED`, `CONSOLIDATED` nếu có), ngày hiệu lực và trạng thái hiệu lực khi các metadata này được xác minh.

### 3.2 Điều kiện dùng rule làm nhãn chuẩn

- Chỉ dùng rule có nguồn node xác định và đã qua rà soát ngữ nghĩa làm ground truth; trạng thái trong metadata phải được kiểm tra theo rule/schema hiện hành.
- Rule chưa xác minh, đã deprecated, hoặc có node nguồn không tồn tại phải được giữ ở trạng thái cần rà soát; không dùng như căn cứ hợp lệ mặc định.
- Tình trạng thiếu node phải được xuất hiện rõ trong provenance. Không cho phép sinh citation từ node ID bị thiếu hoặc tự dựng nội dung thay thế.
- Trước khi phát hành dataset, phải xác nhận các rule đang dùng tương thích với phiên bản/hiệu lực văn bản liên quan đến tình huống.

## 4. Hai luồng cần đặc tả

### 4.1 Luồng tạo dataset (offline)

1. Chọn Điều/rule/predicate/condition từ BLDS 2015 hoặc Luật HNGĐ 2014 và lưu snapshot nội dung, node, phiên bản.
2. Gọi LLM API tạo tình huống/câu hỏi theo cách người dùng mô tả vấn đề; tạo đáp án nháp và dữ liệu nhãn theo từng task.
3. Kiểm tra nháp với rule/predicate/condition và căn cứ nguồn; không cho LLM tự tạo luật hoặc citation.
4. Chạy câu hỏi sinh được qua pipeline retrieval để ghi nhận `relevant_laws`, `relevant_documents` như kết quả retrieval thực tế; luật được trả về chỉ là ứng viên, có thể không liên quan.
5. Đưa facts vào evaluator/Prolog để tính trạng thái; tạo/kiểm chứng nhãn lập luận và câu trả lời dựa trên kết quả.
6. Người rà soát sửa/duyệt/loại mẫu. Chỉ mẫu được duyệt mới vào train hoặc benchmark chuẩn.
7. Ghi model/API provider, model version, prompt version, nguồn luật/Graph snapshot, retrieval output, verifier result, trạng thái duyệt và lý do loại.

LLM API chỉ tạo **bản nháp**. Kết quả API không tự trở thành sự thật pháp lý, nhãn vàng hoặc căn cứ để sửa rule trong Graph.

### 4.2 Luồng xử lý câu hỏi (online/inference)

1. Nhận câu hỏi/tình huống người dùng.
2. Retrieval code kết hợp semantic, BM25 và graph retrieval; dùng reranker để trả `relevant_laws`, `relevant_documents`.
3. Ghi nhận đây là candidates; không mặc định luật nào trong danh sách chắc chắn liên quan câu hỏi.
4. Từ luật ứng viên, lấy Rules, predicates, conditions và node/citation tương ứng.
5. LLM trích xuất facts/entities/objects/relations/events từ tình huống theo format tương thích rule evaluator/Prolog.
6. Evaluator/Prolog kiểm chứng từng fact-condition-rule và trả `true`, `false` hoặc `unknown`.
7. Gom câu hỏi, relevant laws/documents, context, rule/predicate/condition, facts, kết quả verifier và citations.
8. LLM dùng dữ liệu đã gom để giải thích theo tam đoạn luận, trả JSON gồm câu trả lời, luật áp dụng, điều kiện chưa thỏa và unknown.

### Trạng thái một mẫu dataset

`GENERATED` → `SCHEMA_VALIDATED` → `VERIFIED` → `LEGAL_REVIEWED` → `APPROVED_FOR_TRAINING`; mẫu sai có trạng thái `REJECTED` và lý do loại. Không cho phép bỏ qua verification hoặc duyệt pháp lý để đưa mẫu vào tập chuẩn.

## 5. Các task và hợp đồng dữ liệu

### 5.1 Định dạng lưu trữ chuẩn

- Lưu dữ liệu canonical dưới dạng JSONL, một mẫu cho mỗi dòng; UTF-8.
- Cần có `sample_id`, task, input, target, provenance/snapshot và trạng thái duyệt; field/kiểu cụ thể phải được chốt sau khi đối chiếu evaluator hiện tại và input contract của Prolog.
- Cùng một tình huống có thể có record cho nhiều task nhưng phải tách target theo task để nhãn không nhập nhằng.
- SFT conversation format là dữ liệu dẫn xuất; canonical dataset phải giữ facts, rule IDs, trạng thái kiểm chứng và provenance riêng.
- Không sử dụng schema JSON đề xuất trước đó làm schema chính thức. Schema bị người dùng xác nhận là chưa chính xác; schema mới phải được thiết kế/duyệt sau khi chốt đúng giao diện rule engine/Prolog.
- `fact_schema_v1.json` hiện là schema evaluator/test case; không mặc định nó đã mô tả đủ output model hoặc quan hệ entity/event.

### 5.2 Dataset generation — câu hỏi tình huống và đáp án chuẩn

**Nguồn:** nội dung BLDS 2015 và Luật HNGĐ 2014, cùng rule/predicate/condition có liên quan trong repository/Graph.

LLM API đề xuất các câu hỏi tự nhiên theo hướng người dùng mô tả tình huống. Mỗi câu hỏi/đáp án chuẩn phải có thể truy ngược tới đoạn luật, rule và predicate. Bộ sinh cần tạo nhiều loại tình huống gồm dữ kiện đủ, thiếu, mâu thuẫn, ngoại lệ và trường hợp rule không áp dụng; đáp án của API luôn cần kiểm chứng và người duyệt.

### 5.3 Model task A — Trích xuất thông tin theo rule context

**Đầu vào:** câu hỏi tình huống, `relevant_laws`, `relevant_documents`, và rule/predicate/condition đã lấy được cho các luật ứng viên.

**Mục tiêu:** trích xuất từ câu hỏi những fact cần cho rule liên quan, đúng định dạng mà evaluator/Prolog có thể chạy; không tự đánh giá thay cho verifier.

Thông tin cần biểu diễn trong output, theo contract sẽ được chốt:

- entity, chủ thể/đối tượng, vai trò và tham chiếu ổn định giữa các lần xuất hiện;
- quan hệ, sự kiện/hành vi, thời gian và giá trị liên quan nếu câu hỏi nêu;
- ánh xạ fact tới predicate khi có đủ căn cứ; giữ raw mention và evidence để kiểm tra ánh xạ;
- thông tin thiếu, mâu thuẫn hoặc không ánh xạ được; không ép thành giá trị predicate;
- provenance tới câu/đoạn người dùng và rule context được cung cấp.

`relevant_laws` là kết quả retrieval ứng viên, không đảm bảo luật nào cũng liên quan. Model không được coi retrieval result là kết luận về applicability.

### 5.4 Code task — Rule/predicate verification

Đây là tầng evaluator/Prolog, không phải một model task tự quyết định chân lý. Tầng này nhận facts có cấu trúc và rule context, kiểm tra condition/operator theo rule, rồi trả kết quả tri-state `true`, `false` hoặc `unknown`.

- `true`/`false` chỉ phản ánh kết quả kiểm tra predicate/condition cụ thể với facts đã trích xuất.
- `unknown` dùng khi thiếu fact, fact không khớp predicate, nguồn mâu thuẫn hoặc chưa đủ điều kiện đánh giá.
- Không biến retrieval match thành kết quả condition; không coi fact không tìm thấy là `false`.
- Kết quả phải giữ liên hệ tới rule, predicate, condition path và fact đầu vào để LLM diễn giải lại được.
- LLM nhận kết quả verifier; không được tự đổi `unknown` thành `true`/`false` để tạo câu trả lời tròn ý.

Lựa chọn evaluator hiện tại hay Prolog và giao diện input/output cụ thể là open question cần kiểm tra với code thực tế trước khi tạo schema cuối.

### 5.5 Model task B — Tam đoạn luận, giải thích và trả lời

**Đầu vào:** câu hỏi gốc, context luật/rule/predicate đã truy xuất, facts đã trích xuất và kết quả kiểm chứng `true`/`false`/`unknown`.

**Đầu ra mong muốn:** giải thích logic tình huống và luật áp dụng theo cấu trúc có thể kiểm tra:

- tiền đề lớn: nội dung rule/condition và căn cứ luật;
- tiền đề nhỏ: facts đã trích xuất, cùng kết quả kiểm chứng và evidence;
- bước áp dụng: điều kiện nào true, false hoặc unknown; rule nào liên quan nhưng không thỏa/không đủ dữ kiện;
- kết luận/câu trả lời trong giới hạn của kết quả kiểm chứng;
- phân biệt luật/rule đã áp dụng, luật/rule ứng viên không áp dụng, điều kiện chưa thỏa, điều kiện unknown và câu hỏi cần bổ sung nếu có;
- node/citation nguồn có trong context và đã xác minh.

Đầu ra cuối phải là JSON. Các ý nghĩa trên là yêu cầu nội dung; tên property, kiểu dữ liệu và schema JSON chính thức chưa được chốt vì cần khớp giao diện evaluator/Prolog.

Model giải thích kết quả, không đóng vai thẩm phán, không tuyên phán quyết và không tự tạo thêm luật. Nếu fact không khớp hoặc chưa được verifier xác nhận, câu trả lời phải ghi chưa xác định; cấm bịa kết luận dựa trên context luật nhưng trái kết quả kiểm chứng.

Không yêu cầu lưu chain-of-thought nội bộ; chỉ lưu các premise, fact references, condition results và giải thích ngắn có thể audit.

## 6. Huấn luyện và so sánh model

- Huấn luyện một mô hình đa nhiệm; task tags tối thiểu phân biệt extraction và syllogistic explanation/answer. Retrieval + rerank là tầng code/model retrieval riêng, không nhập nhằng thành task fine-tune LLM.
- Fine-tune bằng **Unsloth**, theo hướng 4-bit được mô tả trong `docs/MODELS.md`.
- Danh sách chính thức lấy từ `docs/MODELS.md`: model production là `Qwen/Qwen3-4B-Instruct-2507`; nhóm so sánh là `Qwen/Qwen3-4B`, `Qwen/Qwen2.5-3B-Instruct`, `Qwen/Qwen3-1.7B`, `Qwen/Qwen2.5-1.5B-Instruct`.
- Người dùng cũng nêu các model `Qwen/Qwen3-4B-Thinking-2507`, `Qwen/Qwen3-4B-Instruct-2507-FP8` và `Qwen/Qwen3-4B-Instruct-2507` trong trao đổi. Hai model đầu không xuất hiện trong bản `docs/MODELS.md` đã đọc; cần xác nhận có thêm vào tập benchmark hay không, không tự thay đổi file model.
- Benchmark các model trên cùng train/validation/test; lưu lại model nền, quantization, cấu hình Unsloth, seed, dữ liệu và artifact để so sánh có thể lặp lại.
- Chia tập theo tình huống/template và nhóm rule/văn bản để tránh bản diễn đạt gần trùng hoặc cùng tình huống lọt vào nhiều tập.
- Tập đánh giá phải có mẫu retrieval trả về luật ứng viên không liên quan, facts thiếu/không khớp, kết quả verifier `unknown`, điều kiện false và ngoại lệ.

## 7. Đánh giá và tiêu chí chống bịa đặt

### Kiểm tra dữ liệu trước huấn luyện

- JSONL parse được và qua schema validation sau khi schema cuối được chốt.
- `rule_id`, `predicate` và `node_id` tồn tại trong snapshot nguồn; nguồn fact khớp input và rule context.
- Facts đầu ra có thể được nạp vào evaluator/Prolog; kết quả tri-state tái lập được từ cùng facts + rule.
- Citation trả ra truy ngược được tới node luật; node thiếu phải bị chặn hoặc gắn trạng thái cần rà soát.
- Phát hiện duplicate, gần trùng, mâu thuẫn nhãn và rò rỉ giữa các tập.

### Đánh giá mô hình

- Retrieval/rerank: relevance của `relevant_laws`/`relevant_documents`, recall@k/precision@k hoặc metric retrieval phù hợp; đo riêng lỗi luật ứng viên không liên quan.
- Extraction: precision/recall/F1 theo entity, relation, event, predicate và value; kiểm tra evidence correctness và khả năng xuất facts dùng được bởi verifier.
- Verification: so sánh kết quả `true`/`false`/`unknown` với nhãn chuẩn; đặc biệt đo việc không biến thiếu fact thành false/true.
- Lập luận/trả lời: rubric người duyệt cho premise correctness, bám kết quả verifier, condition/exceptions, luật áp dụng/không thỏa/unknown, citation correctness và không đóng vai phán quyết.
- Hallucination challenge set phải có tình huống retrieval sai/không liên quan, thiếu/đánh lạc hướng/ngoài phạm vi. Citation hoặc kết luận pháp lý không được nguồn/verifier hỗ trợ là lỗi nghiêm trọng và chặn phát hành.
- Báo cáo metric theo từng tầng, task, nguồn luật và trạng thái đủ/thiếu facts; không chỉ báo một điểm số tổng.
- Ngưỡng chất lượng số cụ thể được chốt sau pilot/benchmark ban đầu, không tự đặt khi chưa có baseline.

## 8. Serving và thử nghiệm

- Serving mục tiêu là **Ollama local trên CPU với máy khoảng 10GB RAM**, theo `docs/MODELS.md`; thử fine-tuning có thể dùng Google Colab GPU. Export/quantization GGUF `Q4_K_M` là cấu hình tham chiếu cần benchmark trên máy đích.
- Serving nhận câu hỏi/tình huống, gọi pipeline retrieval + graph/rule lookup + fact extraction + verifier + answer generation; trả JSON có câu trả lời, luật/rule đã áp dụng, ứng viên không áp dụng, điều kiện chưa thỏa/unknown, citation và trạng thái chưa xác định. Tên field/JSON Schema cuối còn phải được duyệt.
- VLM không nằm trong scope hiện tại; chỉ xem xét nếu yêu cầu đầu vào ảnh/tài liệu scan được bổ sung.
- Khi model không tìm thấy rule/citation hợp lệ hoặc verifier trả `unknown`, phải ghi rõ chưa xác định/hỏi thêm; không bù bằng kiến thức không truy vết.
- Log phục vụ đánh giá phải có model/version, task, thời gian và kết quả kiểm tra schema; không ghi API key hoặc dữ liệu nhạy cảm vào log.

## 9. Tech stack, cấu trúc và lệnh

### Stack hiện có

- Backend Python chạy trong `backend\.venv`; Neo4j là Graph nguồn.
- Rule schema: `backend/data/rules/schemas/rule_schema_v1.json`.
- Fact evaluator schema: `backend/data/rules/schemas/fact_schema_v1.json`.
- Rule/predicate/effect catalogs: `backend/data/rules/`.
- Model candidate/production: `docs/MODELS.md`.
- Fine-tuning: Unsloth. Serving: Ollama local CPU. LLM API provider và retrieval/reranker model cụ thể chưa chốt.

### Cấu trúc dữ liệu dự kiến

```text
backend/data/datasets/
  generated/       # bản nháp từ LLM API, chưa dùng train
  reviewed/        # mẫu đã rà soát và duyệt
  splits/          # train/validation/test cố định theo snapshot
  manifests/       # nguồn, model/prompt version, split và review status
```

Đây là cấu trúc yêu cầu đề xuất; chưa tạo thư mục hoặc dữ liệu trong phạm vi spec này.

### Lệnh hiện có để khảo sát/kiểm chứng nguồn

Chạy tại thư mục `backend` trong PowerShell:

```powershell
$env:PYTHONIOENCODING = 'utf-8'
.\.venv\Scripts\python.exe scripts\inspect_legal_rules.py --all
.\.venv\Scripts\python.exe scripts\inspect_legal_rules.py --rule-id BLDS_D117_K1_01
.\.venv\Scripts\python.exe scripts\test_reasoning.py
```

Các lệnh tạo dataset, train và serve **chưa tồn tại**; phải được đặc tả/duyệt trước khi triển khai, không xem các lệnh khảo sát trên là pipeline training.

## 10. Phong cách và ranh giới

### Quy ước triển khai sau khi spec được duyệt

- Theo `docs/RULES.md` và quy ước hiện tại: logic nghiệp vụ thuộc `src/`, scripts chỉ điều phối service; không sửa `backend/src/` nếu chưa được giao rõ.
- Python: Black line length 88, isort profile Black; hàm/method trong class có docstring; không thêm comment nếu không cần giải thích.
- Dữ liệu canonical dùng UTF-8 JSONL, key có tên ổn định, schema có version.

### Always

- Tách rõ retrieval candidate, facts trích xuất, kết quả verifier và kết luận ngôn ngữ tự nhiên.
- Gắn facts, rule conditions, conclusions và citations với input/rule/node nguồn cụ thể.
- Bảo toàn `true`, `false`, `unknown`, ngoại lệ, mâu thuẫn và thông tin thiếu; không ép mọi tình huống phải match.
- Duyệt pháp lý các mẫu sinh trước khi dùng làm nhãn chuẩn.
- Version hóa dataset/schema/prompt/model và ghi lại nguồn.

### Ask first

- Chọn LLM API provider, chi phí tối đa và chính sách lưu/truyền dữ liệu.
- Chốt schema facts/evaluator contract, chọn evaluator hiện tại hay Prolog, cùng retrieval/reranker model cụ thể.
- Đặt target size, ngưỡng metric chính thức hoặc mở rộng sang ảnh/VLM.
- Thay đổi rule/catalog, cập nhật nội dung pháp lý hoặc loại bỏ node nguồn.

### Never

- Dùng mẫu chưa duyệt làm ground truth pháp lý.
- Tự bịa nội dung điều luật, rule ID, predicate, node ID hoặc citation.
- Biến dữ kiện mô hình suy ra thành sự kiện người dùng đã khai báo.
- Ép mô hình kết luận khi dữ kiện/rule chưa đủ.
- Đưa API key, credential hoặc dữ liệu nhạy cảm vào repo, dataset công khai hay log.

## 11. Tiêu chí nghiệm thu

1. Retrieval pipeline trả `relevant_laws` và `relevant_documents` bằng semantic + BM25 + graph retrieval; output được xem là ứng viên, không tự xác nhận relevance.
2. Với luật ứng viên, hệ thống lấy đúng rules/predicates/conditions và node nguồn tương ứng.
3. Model extraction tạo facts/entities/objects/relations/events có thể nạp vào evaluator/Prolog; schema cuối phải được xác nhận bằng test tích hợp thực tế.
4. Verifier trả tri-state `true`/`false`/`unknown` đúng theo rule; missing/unmatched fact không bị biến thành false hoặc true.
5. Answer model sử dụng cả luật/context và kết quả kiểm chứng; giải thích theo tam đoạn luận, nêu luật áp dụng, điều kiện chưa thỏa và unknown; không phán quyết.
6. API-generated dataset qua validation và người duyệt trước khi train.
7. Fine-tune đa nhiệm bằng Unsloth; benchmark model theo `docs/MODELS.md`; serve thử bằng Ollama trên CPU khoảng 10GB RAM.
8. Các bộ test gồm retrieval candidate sai/không liên quan, fact thiếu/không khớp, ngoại lệ, false/unknown, citation không có thật và câu hỏi ngoài phạm vi.
9. Chỉ bắt đầu implementation sau khi spec này được duyệt và schema/evaluator contract được chốt.

## 12. Câu hỏi còn mở

1. LLM API provider, ngân sách/token limit và chính sách dữ liệu.
2. Schema facts đầu ra chính xác theo giao diện evaluator/Prolog hiện có; cần đối chiếu code trước khi phê duyệt schema.
3. Chọn rule evaluator hiện tại hay Prolog làm verifier chuẩn; xác định nơi thực hiện retrieval/rerank và model cụ thể.
4. Dataset pilot size/coverage sau khi thống kê các rule/predicate/node hợp lệ của BLDS 2015 và Luật HNGĐ 2014.
5. Ngưỡng metric số sau baseline; quy trình rà soát pháp lý và tiêu chí pass/fail.
6. Cách xử lý hiệu lực/version văn bản khi metadata nguồn chưa được xác minh đầy đủ.
7. Xác nhận có đưa `Qwen/Qwen3-4B-Thinking-2507` và `Qwen/Qwen3-4B-Instruct-2507-FP8` vào benchmark cùng danh sách tại `docs/MODELS.md` không.

## 13. Yêu cầu gốc của người dùng (nguyên văn)

### Đề tài và yêu cầu ban đầu

> đề tài  
> hiện tao muốn lấy thông tin luaaaaut dân sự các điều  
> yêu cầu LLM API để tạo bộ câu hỏi đáp chuẩn  
> câu hỏi tính hướng từ người dùng về các tình huống pháp lý  
> LLM dựa trên các RULE predicate hay conditions để tạo câu trả lời phù hợp không bịa đặt luật  
> dataset về: facts từ tình huống, khớp với rule predicate trong luật, entity, đổi tượng, quan hệ, sự kiện, ... các facts cũng được trích xuất để sau này check rule predicate, các logic pháp luật chống ảo giác bịa đặt  
>   
> dataset về tam đoạn luận dựa trên kết quả của fact và rule, predicate, conditions thì tạo lập luận và trả lời đầy đủ  
>   
> huấn luyện mô hình LLM cho các task trên và giải thích  
> serving model và ollama hoăc vlm  
> nào hãy viết .md mô tả yêu cầu chi tiết này cho t, để tạo keiemr tra, thử

### Làm rõ pipeline, model và giới hạn kết luận

> train với unsloth, serving với ollama, Còn task truy xuất luật và duyệt đồ thì là code lấy các model truy xuất để retrieval và rerank, input câu hỏi tình huống sau đó mới lấy relevant_laws, relevant_documents để tìm luật liên quan, lấy cái rule liên quan của các luật đo, model nhận diện từ câu hổi tình huống sau đó trích xuất fact, entity, .... rồi gửi lại dữ liệu đầy đủ, luật, context, rule, predicate, kết quả kiểm chứng facts và rules conditions cho LLM, llm nhận diên sử dụng tam đoạn luận và kết quả kiểm chừng trả json trả lời cùng như luật được áp dụng và luật chưa thỏa mãn, unknown
>
> Yêu câu các tasks và mô tả khá đúng, nhưng schema sai rất nhiều  
> Đây là các model lựa chọn tham gia huấn luyện  
> file MODELS.md  
> fine tune unsloth  
> serving: ollama local CPU 10GB mấy  
>   
> Flow:  
> Nhận câu hỏi đáp  
> Truy xuất kết hớp semantic và BM25 + Truy xuất đồ thị  
> được relevant_laws, relevant_documents  
> (Bước này chưa chắc các laws sẽ liên quan câu hỏi nha, lưu ý)  
> Tìm các RULEs, predicate, conditions của các laws đó  
> LLM Model trích xuất thông tin từ câu hỏi tình huống, format phải khớp với rule để chạy suy luận kiểm chứng hoặc prolog  
> kết quả kiểm chứng có thể true, false, unknown, chứ không match hết được, giúp mô hình không bịa đặt khi suy luận  
> Gom lại kết quả các tầng trên  
> sử dụng tam đoạn luận để giải thích kết luận (Không đóng vai là thẩm phán và không có quyền phán quyết nha)  
>   
> yêu cầu sinh dataset dữ liệu từ Bô luật dân sự 2015 và Luật hôn nhân và gia đình  
> từ nội dung luật và rules predicate của luật đó, sinh các câu hỏi đáp hợp lệ  
>   
> Các task:  
>   
> trích xuất thông tin từ câu hỏi, format phải khớp và tuân theo các rule liên quan (trong relevant_laws)  
> suy luận từ kết quả kiểm chứng với tam đoạn luận  
> giait thích được logic tình huống và lauajt áp dụng  
> nếu có fact không khớp phải nói là chưa xác định, cấm bịa đặt dựa trên context luật cung cấp mà không đúng với kiếm chứng  
>   
> mục tiêu chông ảo giác thôi, nhưng là cả quá trình gian nan khổ cực  
> nào hãy nhập đầy đủ mô tả của tôi vào file SPEC không sót 1 từ nào đi

### Các model người dùng nêu trong trao đổi

> Qwen/Qwen3-4B-Thinking-2507  
> Qwen/Qwen3-4B-Instruct-2507-FP8  
> Qwen/Qwen3-4B-Instruct-2507
