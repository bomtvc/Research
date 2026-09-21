# Research Pipeline

Nghiên cứu có kiểm chứng **trước**, viết bài **sau**. Pipeline chạy 12 bước tuần tự, mỗi bước
để lại một artifact JSON có thể đọc và sửa tay; bước sau chỉ được phép dùng những gì bước trước
đã chứng minh.

Đề tài mặc định: *Thực trạng ô nhiễm không khí và ô nhiễm nước tại TP. Hồ Chí Minh và giải pháp*
(`topics/hcmc_pollution.yaml`). Đổi đề tài = đổi file YAML, không đụng tới code.

```
ĐỀ TÀI
  │
  ├─ 1. RESEARCH PLAN ......... câu hỏi nghiên cứu, chỉ số cần đo, yêu cầu về nguồn
  ├─ 2. SOURCE DISCOVERY ...... tra web, gom nguồn ứng viên          [web_search + web_fetch]
  ├─ 3. SOURCE VERIFY ......... thẩm quyền / cập nhật / kiểm chứng   [web_fetch]
  ├─ 4. EVIDENCE MATRIX ....... mỗi dòng = 1 số liệu ↔ 1 nguồn       [web_fetch]
  ├─ 5. DATA ANALYSIS ......... xu hướng, so sánh, nguyên nhân
  ├─ 6. ARGUMENT MAP .......... claim – grounds – warrant – rebuttal
  ├─ 7. OUTLINE ............... dàn ý + ngân sách từ + bằng chứng gắn sẵn
  ├─ 8. WRITING ............... viết từng mục, chỉ với bằng chứng của mục đó
  ├─ 9. CITATION AUDIT ........ câu nào thiếu dẫn, số nào lệch nguồn
  ├─ 10. FACT CHECK ........... kiểm chứng lại bằng nguồn độc lập     [web_search + web_fetch]
  ├─ 11. PEER REVIEW .......... chấm 6 tiêu chí, ra danh sách phải sửa
  └─ 12. FINAL PAPER .......... áp dụng sửa đổi → bài hoàn chỉnh
```

## Cài đặt

```powershell
pip install -r requirements.txt
$env:ANTHROPIC_API_KEY = "sk-ant-..."     # hoặc: ant auth login
```

Máy này hiện **chưa có credential** (`ANTHROPIC_API_KEY` chưa đặt, chưa có `ant`), nên toàn bộ
pipeline mới chỉ được kiểm thử bằng client giả — luồng 12 stage, artifact, resume và xuất file
đều chạy đúng, còn các lời gọi API thật thì chưa từng được thực thi. Lần chạy thật đầu tiên
nên dùng `--to 1` (xem mục dưới) để xác nhận request được API chấp nhận trước khi đốt ngân sách.

## Chạy

```powershell
python run.py --list                            # xem 12 stage
python run.py --topic topics/hcmc_pollution.yaml --to 1    # chạy thử 1 stage
python run.py --topic topics/hcmc_pollution.yaml           # chạy hết 12 stage
```

Mỗi lần chạy tạo một thư mục dưới `runs/`:

```
runs/o-nhiem-...-20260921-2100/
├── manifest.json          # trạng thái, thời gian, token, chi phí ước tính từng stage
├── artifacts/             # 01_research_plan.json ... 12_final_paper.json
├── raw/                   # báo cáo tra web thô của các stage có dùng web tool
└── paper/
    ├── draft.md           # bản thảo (stage 8)
    ├── final_paper.md     # bài hoàn chỉnh (stage 12)
    └── revision_log.md    # sửa gì, bỏ qua gì và vì sao
```

Chạy tiếp / chạy lại một phần:

```powershell
python run.py --run runs/o-nhiem-...-20260921-2100                 # chạy tiếp chỗ dừng
python run.py --run runs/... --from 8 --force                      # viết lại từ stage 8
python run.py --run runs/... --only 10 --force                     # chạy lại đúng stage 10
python run.py --run runs/... --echo                                # in nội dung model sinh ra
```

Stage nào đã có artifact thì tự bỏ qua, nên **sửa tay file JSON rồi chạy tiếp** là cách làm
chính: ví dụ mở `artifacts/03_source_verify.json`, loại bớt nguồn yếu, rồi chạy `--from 4`.

Khi một stage lỗi, pipeline dừng ngay tại đó, ghi lý do vào `manifest.json` và in lệnh để chạy
tiếp — không có stage nào chạy trên dữ liệu hỏng của stage trước.

## Thiết kế

**Hai pha cho mọi stage có tra web.** Pha 1 gọi model kèm server tool `web_search` / `web_fetch`
và để nó viết báo cáo dạng văn bản; pha 2 gọi lại (không tool) để ép báo cáo đó vào JSON Schema.
Tách ra như vậy thì lượt tra cứu không bị ràng buộc schema, còn lượt trích xuất thì rẻ và ổn định.
Báo cáo thô được giữ trong `raw/` để đối chiếu khi nghi ngờ.

**Artifact có schema.** Mọi artifact JSON đều sinh qua `output_config.format` (structured outputs),
định nghĩa trong `research_pipeline/schemas.py`. Muốn thêm trường (ví dụ thêm `doi` cho nguồn),
sửa schema ở đó — không cần đụng prompt.

**Bằng chứng có id.** Nguồn là `S01, S02...`, dòng bằng chứng là `E01, E02...`, phát hiện là
`F01...`. Stage 8 chỉ đưa cho người viết đúng những dòng bằng chứng mà dàn ý đã gắn cho mục đó,
nên câu văn khó trôi khỏi dữ liệu. Stage 9 và 10 soi ngược lại chính các id này.

**Ba lớp kiểm tra khác nhau, không trùng nhau.** Stage 9 hỏi "câu này có dẫn nguồn và dẫn đúng
không"; stage 10 hỏi "điều này có đúng không" và tra web độc lập để trả lời; stage 11 hỏi
"lập luận có đứng vững không". Stage 12 gộp cả ba thành một danh sách sửa duy nhất.

`pause_turn` (lượt bị server tool cắt giữa chừng) được nối lại thủ công trong `client.py` —
SDK không tự làm việc này, và nếu bỏ qua thì câu trả lời sẽ bị cụt mà không báo lỗi.

## Cấu hình

`research_pipeline/config.py`:

| Thứ | Mặc định | Ghi chú |
|---|---|---|
| `MODEL` | `claude-opus-5` | đổi bằng `--model` khi cần |
| `STAGE_EFFORT` | `high`, riêng stage 5/6/10/11/12 là `xhigh` | effort càng cao càng kỹ và càng tốn |
| `USER_LOCATION` | TP.HCM / VN | giúp `web_search` ưu tiên nguồn Việt Nam; đặt `None` nếu API trả 400 |
| `MAX_SEARCHES_PER_STAGE` | 12 | trần số lần tìm kiếm mỗi stage |
| `CACHE_*_MULT` | 1.25 / 0.10 | hệ số **ước lượng** để hiển thị chi phí, không phải hoá đơn |

`topics/*.yaml` giữ phần thuộc về đề tài: phạm vi, đối tượng đọc, độ dài, những gì bắt buộc
phải bao phủ, và các ngưỡng (`min_sources`, `min_accepted_sources`, `min_fact_checks`).

Con số chi phí in ra cuối mỗi stage là **ước tính** tính từ token đếm được nhân đơn giá trong
`config.PRICING`; phần token cache dùng hệ số ước lượng nên có sai số. Hoá đơn thật xem ở Console.

## Viết đề tài mới

Copy `topics/hcmc_pollution.yaml`, sửa `title`, `central_question`, `must_cover`, `constraints`,
rồi `python run.py --topic topics/<file>.yaml`. Prompt trong `stages/` viết theo hướng chung cho
nghiên cứu hiện trạng–nguyên nhân–giải pháp, nhưng một số câu đang nhắc trực tiếp tới ô nhiễm
không khí/nước (stage 1, 2, 7); đổi sang đề tài khác hẳn thì nên đọc lại ba file đó.
