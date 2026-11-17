# Neovim -- Hướng dẫn thao tác chi tiết

## Khởi chạy và làm việc với file

### Mở Neovim

```bash
nvim
```

Mở một file:

```bash
nvim main.py
```

Mở nhiều file:

```bash
nvim main.py app.py config.py
```

Mở thư mục hiện tại:

```bash
nvim .
```

Mở file và đặt con trỏ tại dòng cụ thể:

```bash
nvim +25 main.py
```

Mở file tại một dòng và cột cụ thể:

```bash
nvim +call\ cursor\(25\,10\) main.py
```

### Các lệnh lưu và thoát

Các lệnh này được nhập trong Normal Mode bằng cách nhấn `:` để mở
Command-line Mode.

Lệnh Tác dụng

---

`:w` Lưu file hiện tại
`:w filename` Lưu nội dung thành file mới
`:wa` Lưu tất cả file đang mở
`:q` Thoát cửa sổ hiện tại
`:q!` Thoát và bỏ thay đổi chưa lưu
`:wq` Lưu rồi thoát
`:x` Lưu nếu có thay đổi rồi thoát
`:qa` Thoát tất cả cửa sổ
`:qa!` Thoát tất cả và bỏ thay đổi chưa lưu
`ZZ` Lưu và thoát nếu có thay đổi
`ZQ` Thoát mà không lưu

Nếu Neovim báo `No write since last change`, file đang có thay đổi chưa
được lưu. Dùng `:w` để lưu hoặc `:q!` nếu muốn bỏ thay đổi.

## Các chế độ thao tác (Modes)

### Normal Mode

Normal Mode là chế độ mặc định khi mở Neovim. Các phím được dùng để di
chuyển, chọn, xóa, sao chép và chỉnh sửa cấu trúc văn bản.

Nhấn `Esc` để quay về Normal Mode từ hầu hết các chế độ khác.

### Insert Mode

Insert Mode dùng để nhập văn bản thông thường.

---

Phím Tác dụng

---

`i` Chèn trước vị trí con trỏ

`I` Chèn tại đầu dòng, trước ký tự
không phải khoảng trắng đầu tiên

`a` Chèn sau vị trí con trỏ

`A` Chèn tại cuối dòng

`o` Tạo dòng mới bên dưới và chuyển
sang Insert Mode

`O` Tạo dòng mới bên trên và chuyển
sang Insert Mode

`s` Xóa ký tự dưới con trỏ rồi chèn

`S` Xóa nội dung dòng rồi chèn

`Esc` Quay về Normal Mode

---

Ví dụ: đặt con trỏ giữa một dòng, nhấn `i` để chèn trước ký tự đang
đứng; nhấn `A` để thêm nội dung vào cuối dòng.

### Visual Mode

Visual Mode dùng để chọn một vùng văn bản.

Phím Tác dụng

---

`v` Chọn theo ký tự
`V` Chọn theo dòng
`Ctrl-v` Chọn theo khối chữ nhật
`o` Di chuyển con trỏ đến đầu hoặc cuối vùng chọn
`Esc` Hủy vùng chọn

Sau khi chọn, có thể dùng `d` để xóa, `y` để sao chép, `c` để thay thế
hoặc `>` và `<` để tăng/giảm indentation.

### Command-line Mode

Nhấn `:` trong Normal Mode để nhập lệnh. Ví dụ:

```vim
:w
:set number
:help motion
```

Nhấn `Enter` để thực thi lệnh và `Esc` để hủy.

### Replace Mode

- `r` thay thế một ký tự dưới con trỏ.
- `R` vào Replace Mode để ghi đè liên tục các ký tự.
- `Esc` để kết thúc Replace Mode.

### Terminal Mode

Mở terminal tích hợp:

```vim
:terminal
```

Trong Terminal Mode, nhấn `Ctrl-\\` rồi `Ctrl-n` để quay về
Terminal-Normal Mode. Từ đó có thể điều hướng buffer hoặc đóng terminal.
Có thể dùng `i` để quay lại nhập lệnh trong terminal.

## Di chuyển con trỏ

### Di chuyển theo ký tự và dòng

Phím Tác dụng

---

`h` Sang trái một ký tự
`j` Xuống một dòng
`k` Lên một dòng
`l` Sang phải một ký tự
`gj` Xuống theo dòng hiển thị khi văn bản bị wrap
`gk` Lên theo dòng hiển thị khi văn bản bị wrap
`0` Đầu dòng, kể cả khoảng trắng
`^` Ký tự đầu tiên không phải khoảng trắng
`$` Cuối dòng
`g_` Ký tự cuối cùng không phải khoảng trắng
`gg` Đầu file
`G` Cuối file
`{number}G` Đến dòng có số tương ứng
`:{number}` Đến dòng có số tương ứng

Ví dụ:

```vim
25G
:25
```

Cả hai cách đều đưa con trỏ đến dòng 25.

### Di chuyển theo từ

Phím Tác dụng

---

`w` Đến đầu từ kế tiếp
`W` Đến đầu WORD kế tiếp, phân tách chủ yếu bằng khoảng trắng
`b` Đến đầu từ hiện tại hoặc từ trước
`B` Đến đầu WORD hiện tại hoặc WORD trước
`e` Đến cuối từ hiện tại hoặc từ kế tiếp
`E` Đến cuối WORD
`ge` Đến cuối từ trước đó
`gE` Đến cuối WORD trước đó

Trong Vim, `word` thường coi dấu câu là ranh giới; `WORD` chỉ dùng
khoảng trắng để phân tách.

### Di chuyển theo màn hình

Phím Tác dụng

---

`Ctrl-u` Cuộn lên nửa màn hình
`Ctrl-d` Cuộn xuống nửa màn hình
`Ctrl-b` Cuộn lên một màn hình
`Ctrl-f` Cuộn xuống một màn hình
`H` Đưa con trỏ đến vùng trên màn hình
`M` Đưa con trỏ đến giữa màn hình
`L` Đưa con trỏ đến vùng dưới màn hình
`zz` Đưa dòng hiện tại về giữa màn hình
`zt` Đưa dòng hiện tại lên đầu màn hình
`zb` Đưa dòng hiện tại xuống cuối màn hình

### Di chuyển theo cấu trúc

Phím Tác dụng

---

`%` Nhảy giữa các dấu ngoặc tương ứng
`{` Đến đoạn văn trước
`}` Đến đoạn văn sau
`[[` Di chuyển đến đầu một section/function theo cấu trúc hỗ trợ
`]]` Di chuyển đến section/function tiếp theo
`gd` Đến định nghĩa local của symbol, nếu có hỗ trợ
`gD` Đến định nghĩa global của symbol, nếu có hỗ trợ

Các chuyển động theo cấu trúc code có thể phụ thuộc filetype, plugin
hoặc LSP.

## Chọn, xóa, thay đổi và sao chép

### Operator cơ bản

Operator Tác dụng

---

`d` Xóa vùng được chỉ định
`c` Xóa vùng được chỉ định rồi vào Insert Mode
`y` Sao chép vùng được chỉ định
`>` Tăng indentation
`<` Giảm indentation
`g~` Đảo chữ hoa/thường
`gu` Chuyển thành chữ thường
`gU` Chuyển thành chữ hoa
`=` Tự căn chỉnh theo indent expression

Operator thường kết hợp với motion hoặc text object. Ví dụ `dw` xóa từ
vị trí con trỏ đến đầu từ tiếp theo.

### Thao tác theo dòng

Phím Tác dụng

---

`dd` Xóa cả dòng
`yy` Sao chép cả dòng
`cc` Xóa nội dung dòng và vào Insert Mode
`D` Xóa từ con trỏ đến cuối dòng
`C` Xóa từ con trỏ đến cuối dòng rồi vào Insert Mode
`Y` Sao chép từ con trỏ đến cuối dòng
`p` Dán sau con trỏ hoặc dưới dòng hiện tại
`P` Dán trước con trỏ hoặc trên dòng hiện tại
`J` Nối dòng hiện tại với dòng dưới
`gJ` Nối dòng mà không thêm khoảng trắng

### Kết hợp số lượng (Count)

Có thể đặt số trước thao tác để lặp lại.

```vim
3dd
```

Xóa ba dòng, bắt đầu từ dòng hiện tại.

```vim
5j
```

Di chuyển xuống năm dòng.

```vim
2yy
```

Sao chép hai dòng.

```vim
3w
```

Di chuyển qua ba từ.

### Text Objects

Text object cho phép thao tác với một đơn vị nội dung mà không cần tự
chọn từng ký tự.

Text object Ý nghĩa

---

`iw` Bên trong một từ
`aw` Một từ, gồm khoảng trắng liên quan
`iW` Bên trong một WORD
`aW` Một WORD
`i"` Bên trong cặp dấu nháy kép
`a"` Cả nội dung và cặp dấu nháy kép
`i'` Bên trong cặp dấu nháy đơn
`a'` Cả nội dung và cặp dấu nháy đơn
`i(` hoặc `ib` Bên trong cặp ngoặc tròn
`a(` hoặc `ab` Bao gồm cả cặp ngoặc tròn
`i[` Bên trong cặp ngoặc vuông
`a[` Bao gồm cặp ngoặc vuông
`i{` hoặc `iB` Bên trong cặp ngoặc nhọn
`a{` hoặc `aB` Bao gồm cặp ngoặc nhọn
`ip` Bên trong đoạn văn
`ap` Cả đoạn văn và khoảng trắng liên quan

Ví dụ:

```vim
ciw
```

Thay thế từ dưới con trỏ: xóa từ đó và vào Insert Mode.

```vim
di"
```

Xóa phần nằm bên trong dấu nháy kép, giữ lại hai dấu nháy.

```vim
ya(
```

Sao chép cả cụm trong ngoặc tròn, bao gồm dấu ngoặc.

```vim
ci{
```

Thay thế nội dung bên trong cặp ngoặc nhọn.

### Một số tổ hợp thao tác thường dùng

Phím Tác dụng

---

`ciw` Thay thế từ hiện tại
`diw` Xóa từ hiện tại
`yiw` Sao chép từ hiện tại
`ci"` Thay thế nội dung trong dấu nháy kép
`da(` Xóa cả cụm ngoặc tròn
`ci{` Thay thế nội dung trong ngoặc nhọn
`dip` Xóa đoạn văn
`yap` Sao chép đoạn văn
`ct,` Thay đổi từ vị trí hiện tại đến trước dấu phẩy tiếp theo
`df)` Xóa đến và bao gồm dấu `)` tiếp theo
`dt)` Xóa đến trước dấu `)` tiếp theo

## Tìm kiếm và thay thế

### Tìm kiếm trong file

Lệnh Tác dụng

---

`/keyword` Tìm về phía sau
`?keyword` Tìm ngược về phía trước
`n` Đến kết quả tiếp theo theo hướng tìm kiếm
`N` Đến kết quả trước đó
`*` Tìm từ dưới con trỏ về phía sau
`#` Tìm từ dưới con trỏ theo hướng ngược lại
`:%s/old/new/g` Thay thế tất cả trong file
`:s/old/new/g` Thay thế trong dòng hiện tại
`:10,20s/old/new/g` Thay thế trong dòng 10 đến 20
`:%s/old/new/gc` Hỏi xác nhận trước mỗi lần thay thế

Ví dụ:

```vim
:%s/foo/bar/g
```

Thay tất cả `foo` thành `bar` trong file hiện tại.

```vim
:%s/foo/bar/gc
```

Hỏi xác nhận từng kết quả trước khi thay thế.

### Tùy chọn tìm kiếm

```vim
:set hlsearch
:set nohlsearch
:set incsearch
:set ignorecase
:set smartcase
```

- `hlsearch`: tô sáng các kết quả tìm được.
- `nohlsearch`: tắt tô sáng kết quả.
- `incsearch`: hiển thị kết quả khi đang nhập từ khóa.
- `ignorecase`: tìm không phân biệt hoa thường.
- `smartcase`: tự phân biệt hoa thường nếu từ khóa có chữ hoa.

Xóa highlight tìm kiếm hiện tại:

```vim
:nohlsearch
```

## Undo, Redo và Registers

### Undo và Redo

Phím Tác dụng

---

`u` Hoàn tác thay đổi gần nhất
`Ctrl-r` Làm lại thay đổi đã undo
`U` Hoàn tác các thay đổi trên dòng theo hành vi của Vim
`.` Lặp lại thao tác chỉnh sửa gần nhất

### Registers

Register là nơi Neovim lưu nội dung được sao chép hoặc xóa.

Lệnh Tác dụng

---

`"` Mở đầu cú pháp chọn register
`:reg` Hiển thị các register
`"ayy` Sao chép dòng vào register `a`
`"ap` Dán nội dung từ register `a`
`"add` Xóa dòng và lưu vào register `a`
`"+y` Sao chép vào clipboard hệ thống
`"+p` Dán từ clipboard hệ thống
`"0p` Dán nội dung yank gần nhất từ register `0`

Clipboard hệ thống cần được hỗ trợ bởi môi trường Neovim. Kiểm tra bằng:

```vim
:checkhealth
```

## Indentation và định dạng văn bản

### Thao tác indentation

Phím Tác dụng

---

`>>` Tăng indent dòng hiện tại
`<<` Giảm indent dòng hiện tại
`==` Tự căn chỉnh dòng hiện tại
`>G` Tăng indent từ dòng hiện tại đến cuối file
`<G` Giảm indent từ dòng hiện tại đến cuối file
`3>>` Tăng indent ba dòng
`=G` Căn chỉnh từ dòng hiện tại đến cuối file

Trong Visual Mode, chọn nhiều dòng rồi nhấn `>` hoặc `<` để tăng hoặc
giảm indent.

### Thiết lập indentation

```vim
:set expandtab
:set tabstop=4
:set shiftwidth=4
:set softtabstop=4
```

- `expandtab`: chuyển phím Tab thành khoảng trắng.
- `tabstop`: độ rộng hiển thị của ký tự Tab.
- `shiftwidth`: số khoảng trắng dùng khi tăng/giảm indent.
- `softtabstop`: số khoảng trắng khi nhấn Tab hoặc Backspace trong
  Insert Mode.

Các giá trị trên là ví dụ; dự án có thể yêu cầu cấu hình khác.

## Comment và Uncomment

Neovim không cung cấp một phím tắt comment đa ngôn ngữ mặc định thống
nhất. Có thể:

- Dùng Visual Mode để chọn dòng và chèn ký tự comment phù hợp.
- Dùng lệnh thay thế theo cú pháp của ngôn ngữ.
- Cài plugin comment như Comment.nvim hoặc mini.comment để thao tác
  thuận tiện hơn.

Ví dụ với Python, thêm `#` đầu dòng bằng thay thế theo phạm vi:

```vim
:'<,'>s/^/# /
```

Bỏ `#` đầu dòng:

```vim
:'<,'>s/^# //
```

Phạm vi `'<,'>` được tự động thêm khi chạy command sau khi chọn vùng
bằng Visual Mode.

## Buffer -- quản lý nội dung đang mở

Buffer là vùng nội dung được Neovim nạp vào bộ nhớ. Một buffer có thể
hiển thị trong một hoặc nhiều window.

Lệnh Tác dụng

---

`:ls` hoặc `:buffers` Liệt kê buffer
`:bnext` hoặc `:bn` Chuyển đến buffer kế tiếp
`:bprevious` hoặc `:bp` Chuyển đến buffer trước
`:bfirst` Chuyển đến buffer đầu tiên
`:blast` Chuyển đến buffer cuối cùng
`:buffer 3` Mở buffer có số 3
`:bdelete` hoặc `:bd` Xóa buffer khỏi danh sách
`:bwipeout` Xóa buffer hoàn toàn khỏi bộ nhớ
`:edit file.txt` Mở file trong buffer

`bdelete` không đồng nghĩa với xóa file khỏi ổ đĩa. Nó chỉ đóng buffer.
Muốn xóa file trên hệ thống, cần dùng lệnh file system phù hợp.

## Window và Split

Window là vùng hiển thị một buffer. Một buffer có thể được hiển thị
trong nhiều window.

### Tạo và đóng split

Lệnh Tác dụng

---

`:split` hoặc `:sp` Chia cửa sổ ngang
`:vsplit` hoặc `:vsp` Chia cửa sổ dọc
`:new` Tạo window ngang với buffer mới
`:vnew` Tạo window dọc với buffer mới
`:close` Đóng window hiện tại
`:only` Chỉ giữ lại window hiện tại

### Di chuyển giữa các window

Phím Tác dụng

---

`Ctrl-w h` Sang window bên trái
`Ctrl-w j` Sang window bên dưới
`Ctrl-w k` Sang window bên trên
`Ctrl-w l` Sang window bên phải
`Ctrl-w w` Chuyển sang window kế tiếp
`Ctrl-w p` Quay lại window trước đó

### Thay đổi kích thước window

Phím Tác dụng

---

`Ctrl-w =` Cân bằng kích thước các window
`Ctrl-w +` Tăng chiều cao
`Ctrl-w -` Giảm chiều cao
`Ctrl-w >` Tăng chiều rộng
`Ctrl-w <` Giảm chiều rộng
`Ctrl-w _` Tối đa chiều cao
`Ctrl-w \|` Tối đa chiều rộng

Có thể thêm số trước một số lệnh, ví dụ `5 Ctrl-w +` để tăng chiều cao
năm dòng.

## Tab page

Tab page là một bố cục gồm một hoặc nhiều window, không đơn thuần là một
tab tương ứng với một file.

Lệnh Tác dụng

---

`:tabnew` Tạo tab page mới
`:tabnew file.txt` Tạo tab page và mở file
`:tabnext` hoặc `gt` Sang tab page tiếp theo
`:tabprevious` hoặc `gT` Sang tab page trước
`:tabfirst` Đến tab page đầu
`:tablast` Đến tab page cuối
`:tabclose` Đóng tab page hiện tại
`:tabonly` Chỉ giữ tab page hiện tại

## File Explorer và tìm kiếm file

### NetRW có sẵn

Mở trình duyệt file tích hợp:

```vim
:Explore
```

Mở tại thư mục hiện tại:

```vim
:Sexplore
:Vexplore
```

NetRW có thể duyệt thư mục, mở file, đổi tên và thực hiện một số thao
tác file cơ bản.

### Tìm file bằng lệnh

```vim
:find main.py
```

Lệnh `:find` phụ thuộc `path` và `wildignore` đã cấu hình. Với dự án
lớn, fuzzy finder như Telescope là một lựa chọn bổ sung, không phải tính
năng bắt buộc của Neovim.

## Marks và Jump List

### Marks

Mark lưu vị trí để quay lại sau.

Lệnh Tác dụng

---

`ma` Đặt local mark tên `a`
`'a` Nhảy đến dòng chứa mark `a`
`` `a `` Nhảy đến đúng vị trí mark `a`
`:marks` Liệt kê marks

Chữ thường thường dùng cho vị trí trong file hiện tại; chữ hoa có thể
dùng để đánh dấu vị trí giữa các file.

### Jump List

Phím Tác dụng

---

`Ctrl-o` Quay lại vị trí trước trong jump list
`Ctrl-i` Đi tới vị trí tiếp theo
`:jumps` Xem jump list

## Macro -- ghi và phát lại thao tác

Macro ghi lại chuỗi thao tác Normal Mode để phát lại.

Bắt đầu ghi vào register `q`:

```vim
qq
```

Thực hiện các thao tác cần ghi, sau đó nhấn `q` để kết thúc.

Phát lại:

```vim
@q
```

Phát lại macro gần nhất:

```vim
@@
```

Phát lại 5 lần:

```vim
5@q
```

Nên thử macro trên một vùng nhỏ trước khi áp dụng cho toàn file, đặc
biệt khi thao tác có xóa hoặc thay thế nội dung.

## Autocomplete và LSP khi viết code

Các tính năng này không phải tất cả đều có sẵn ngay sau khi cài Neovim.
Cần cấu hình language server hoặc plugin phù hợp.

### Các thao tác LSP thường gặp

Các keymap dưới đây là quy ước phổ biến, không phải phím mặc định cố
định cho mọi cấu hình:

Thao tác Chức năng

---

Go to Definition Đi đến nơi symbol được định nghĩa
Find References Tìm các nơi sử dụng symbol
Hover Hiển thị thông tin và tài liệu
Rename Đổi tên symbol
Code Action Đề xuất hành động sửa code
Diagnostics Xem lỗi và cảnh báo
Format Định dạng code

Trong Neovim, có thể gọi trực tiếp các hàm LSP qua Lua khi client tương
ứng đã được khởi tạo. Ví dụ:

```lua
vim.lsp.buf.definition()
vim.lsp.buf.references()
vim.lsp.buf.hover()
vim.lsp.buf.rename()
vim.lsp.buf.code_action()
vim.lsp.buf.format()
```

Nếu không có language server tương thích đang hoạt động, các thao tác
trên có thể không trả về kết quả.

## Terminal tích hợp

Mở terminal:

```vim
:terminal
```

Mở terminal trong split ngang:

```vim
:split | terminal
```

Mở terminal trong split dọc:

```vim
:vsplit | terminal
```

Thoát chế độ nhập lệnh terminal để điều khiển Neovim:

- Nhấn `Ctrl-\\`.
- Sau đó nhấn `Ctrl-n`.

Quay lại Terminal Mode:

```vim
i
```

Đóng terminal bằng cách kết thúc tiến trình shell hoặc đóng buffer
terminal khi không còn cần sử dụng.

## Các lệnh quản lý cấu hình và trợ giúp

### Trợ giúp tích hợp

Lệnh Tác dụng

---

`:help` Mở trang trợ giúp
`:help motion` Trợ giúp về motion
`:help insert` Trợ giúp Insert Mode
`:help options` Danh sách options
`:help lua` Trợ giúp Lua
`:help key-notation` Cách ghi ký hiệu phím
`:checkhealth` Kiểm tra tình trạng các thành phần

### Kiểm tra cấu hình

```vim
:echo stdpath('config')
:echo stdpath('data')
:scriptnames
:set
:map
:verbose map
```

- `stdpath('config')`: đường dẫn thư mục cấu hình.
- `stdpath('data')`: đường dẫn dữ liệu.
- `scriptnames`: liệt kê script đã được nạp.
- `:map`: xem các mapping.
- `:verbose map`: xem mapping và nơi khai báo gần nhất.

### Nạp lại cấu hình

Nếu cấu hình chính là `init.lua`:

```vim
:luafile %
```

Lệnh này thực thi file Lua hiện tại. Hãy đảm bảo đang mở đúng file cấu
hình trước khi chạy.

## Các thiết lập cơ bản trong init.lua

Ví dụ cấu hình tối thiểu:

```lua
-- Hiển thị số dòng
vim.opt.number = true
vim.opt.relativenumber = true

-- Indentation
vim.opt.expandtab = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.softtabstop = 4

-- Tìm kiếm
vim.opt.ignorecase = true
vim.opt.smartcase = true
vim.opt.hlsearch = true
vim.opt.incsearch = true

-- Giao diện
vim.opt.termguicolors = true
vim.opt.cursorline = true
vim.opt.wrap = false

-- Clipboard hệ thống
vim.opt.clipboard = "unnamedplus"
```

Cấu hình này là ví dụ khởi đầu. Một số thiết lập, đặc biệt clipboard, có
thể phụ thuộc hệ điều hành và công cụ hỗ trợ.

## Keymap cơ bản bằng Lua

Ví dụ khai báo mapping:

```lua
local map = vim.keymap.set

-- Dùng Space làm Leader
vim.g.mapleader = " "

-- Lưu file
map("n", "<leader>w", "<cmd>write<cr>", {
    desc = "Save file",
})

-- Thoát
map("n", "<leader>q", "<cmd>quit<cr>", {
    desc = "Quit window",
})

-- Bỏ highlight tìm kiếm
map("n", "<Esc>", "<cmd>nohlsearch<cr>", {
    desc = "Clear search highlight",
})
```

Tham số đầu tiên là mode, tham số thứ hai là phím được nhấn, tham số thứ
ba là hành động, tham số cuối là các tùy chọn.

Các mode thường dùng trong keymap:

Ký hiệu Mode

---

`n` Normal
`i` Insert
`v` Visual
`x` Visual
`t` Terminal
`c` Command-line

## Lỗi thường gặp và cách xử lý

### Không lưu được file

Kiểm tra quyền ghi file và đường dẫn. Nếu file chỉ đọc, xem lại quyền
truy cập hoặc dùng quyền phù hợp của hệ điều hành. Không nên mặc định
dùng `:w!` nếu chưa hiểu nguyên nhân.

### Không dán được từ clipboard hệ thống

Kiểm tra:

```vim
:checkhealth
```

Xác nhận Neovim có clipboard provider phù hợp. Trên Linux có thể cần
công cụ clipboard của môi trường desktop hoặc Wayland/X11; trên Windows
và macOS cần kiểm tra môi trường chạy Neovim.

### Phím tắt không hoạt động như mong đợi

- Kiểm tra đang ở đúng mode.
- Dùng `:verbose map <key>` để tìm mapping.
- Kiểm tra plugin có ghi đè mapping hay không.
- Kiểm tra terminal có gửi đúng tổ hợp phím hay không.

### LSP không hoạt động

- Kiểm tra language server đã cài chưa.
- Kiểm tra file có đúng filetype không bằng `:set filetype?`.
- Kiểm tra trạng thái client bằng `:LspInfo` nếu cấu hình có cung cấp
  lệnh này, hoặc dùng API LSP tương ứng.
- Kiểm tra log và thông báo lỗi.
- Xác nhận project root được nhận diện đúng.

### Plugin không tải

- Kiểm tra cấu hình plugin và cú pháp Lua.
- Kiểm tra plugin manager đã được cài và nạp.
- Xem thông báo lỗi khi khởi động.
- Kiểm tra dependencies và phiên bản Neovim mà plugin yêu cầu.

## Bài tập thực hành

### Thực hành thao tác file

- Tạo file `practice.txt`.
- Nhập ít nhất 10 dòng nội dung.
- Lưu file, đóng Neovim và mở lại.
- Mở cùng lúc hai file và chuyển qua lại giữa chúng.

### Thực hành điều hướng

- Di chuyển đến đầu file và cuối file.
- Di chuyển đến dòng 10.
- Tìm một từ xuất hiện nhiều lần.
- Dùng `*`, `n` và `N` để di chuyển giữa kết quả.
- Dùng `Ctrl-d`, `Ctrl-u` để cuộn màn hình.

### Thực hành chỉnh sửa

- Xóa một dòng bằng `dd`.
- Sao chép một dòng bằng `yy` và dán bằng `p`.
- Thay thế một từ bằng `ciw`.
- Xóa nội dung trong dấu nháy bằng `di"`.
- Tăng indent cho nhiều dòng.
- Thử undo và redo.

### Thực hành quản lý cửa sổ

- Mở hai file.
- Chia màn hình ngang và dọc.
- Chuyển qua lại giữa các window.
- Thay đổi kích thước.
- Đóng một window nhưng giữ lại buffer.

### Thực hành tìm kiếm và thay thế

- Tìm một từ bằng `/`.
- Thay thế từ trong một dòng.
- Thay thế trong toàn file.
- Sử dụng chế độ xác nhận với `c`.
- Xóa highlight sau khi tìm kiếm.

## Bảng tra cứu nhanh

Nhu cầu Thao tác

---

Lưu file `:w`
Thoát `:q`
Thoát không lưu `:q!`
Lưu và thoát `:wq`
Vào Insert Mode `i`
Quay về Normal Mode `Esc`
Xóa dòng `dd`
Sao chép dòng `yy`
Dán `p`
Hoàn tác `u`
Làm lại `Ctrl-r`
Tìm kiếm `/keyword`
Kết quả tiếp theo `n`
Đầu file `gg`
Cuối file `G`
Đầu dòng `0`
Cuối dòng `$`
Chia ngang `:split`
Chia dọc `:vsplit`
Liệt kê buffer `:ls`
Trợ giúp `:help`
Kiểm tra môi trường `:checkhealth`

## Tài liệu tham khảo

- [Neovim Documentation](https://neovim.io/doc/)
- [Neovim User Manual --
  Editing](https://neovim.io/doc/user/usr_04.html)
- [Neovim User Manual -- Moving
  Around](https://neovim.io/doc/user/usr_03.html)
- [Neovim User Manual -- Editing
  Files](https://neovim.io/doc/user/usr_07.html)
- [Neovim Lua Guide](https://neovim.io/doc/user/lua-guide.html)
- [Neovim API](https://neovim.io/doc/user/api.html)

---

_Tài liệu tập trung vào thao tác trực tiếp với Neovim. Các tính năng phụ
thuộc plugin hoặc Language Server được ghi chú riêng để phân biệt với
chức năng tích hợp sẵn._
