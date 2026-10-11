import re
import unicodedata

try:
    from .teencode_dict import *
except ImportError:
    from teencode_dict import *


def clean_text(text:str="", type:str='article'):
    """_summary_
    Làm sạch văn bản đầu vào theo các kiểu văn bản khác nhau (normal, article, comment, title).

    Args:
        text (str, optional): Văn bản đầu vào cần làm sạch. Mặc định "".
        type (str, optional): Kiểu văn bản. Mặc định 'article'.
    """
    
    if type == 'normal':
        # Loại bỏ các ký tự đặc biệt, giữ lại chữ cái, số và dấu cách
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        # Chuyển về chữ thường
        text = text.lower()
    elif type == 'article':
        
        def encoding(text):
            # NFC normalize — quan trọng với tiếng Việt
            # "à" có thể được encode 2 cách khác nhau → phải chuẩn hóa
            text = unicodedata.normalize('NFC', text)

            # Zero-width characters ẩn
            # text = re.sub(r'[\u200b\u200c\u200d\ufeff\u00ad]', '', text)

            # # Dấu cách đặc biệt → dấu cách thường
            # text = re.sub(r'[\u00a0\u2000-\u200a\u202f\u205f\u3000]', ' ', text)
            
            return text
            
        def clean_html(text):
            # HTML tags còn sót
            text = re.sub(r'<[^>]+>', ' ', text)

            # HTML entities
            text = text.replace('&amp;', '&').replace('&lt;', '<')
            text = text.replace('&gt;', '>').replace('&nbsp;', ' ')
            text = text.replace('&quot;', '"').replace('&#39;', "'")

            # URL
            text = re.sub(r'http[s]?://\S+', ' TOKENURL ', text)
            text = re.sub(r'www\.\S+', ' TOKENURL ', text)

            # Email
            text = re.sub(r'\S+@\S+\.\S+', ' TOKENEMAIL ', text)
            
            return text
        
        def map_emoji(text):
            # map icon cảm xúc và teencode → chuẩn hóa để model hiểu
            for icon, token in EMOJI_MAP.items():
                text = text.replace(icon, f" {token} ")
            return text
            
        def map_rule(text) -> str:
            
                
            # lower
            text = text.lower()
            
            # Teencode hoặc từ viết tắt → tiếng Việt chuẩn
            words = text.split()
            clean_words = []
            for w in words:
                w = TEENCODE_MAP.get(w, w)  # Thay thế teencode
                w = COMMON_ABBREVIATIONS.get(w, w)  # Thay thế từ viết tắt phổ biến
                w = normalize_typing_rules(w)
                clean_words.append(w)
            return ' '.join(clean_words)

        def normalize_special_tokens(text: str) -> str:
            # Chuẩn hóa mọi token dạng token* thành TOKEN* để đồng nhất toàn pipeline.
            return re.sub(
                r'\btoken[a-z0-9_]*\b',
                lambda m: m.group(0).upper(),
                text,
                flags=re.IGNORECASE,
            )

        def clean_structure(text):
            # Caption ảnh
            text = re.sub(r'\(Ảnh[^)]*\)', '', text)
            text = re.sub(r'\(Ảnh[^)]*\.\)', '', text)
            text = re.sub(r'\(Nguồn[^)]*\)', '', text)
            text = re.sub(r'\(Video[^)]*\)', '', text)
            
            return text
            
        def clean_special_chars(text):
            # Dấu ngoặc kép tiếng Việt → bỏ hoặc giữ nội dung
            text = re.sub(r'[""„‟«»]', '"', text)  # chuẩn hóa
            text = re.sub(r'[''‚‛]', "'", text)

            # Dấu gạch ngang các loại → chuẩn hóa
            text = re.sub(r'[–—―]', '-', text)

            # Dấu chấm lửng
            text = re.sub(r'\.{2,}', ' TOKENEOS ', text)  # ... → kết câu
            text = re.sub(r'…', ' TOKENEOS ', text)

            # Ký tự lặp vô nghĩa
            text = re.sub(r'(.)\1{3,}', r'\1', text)  # "aaaaa" → "a"
            
            return text
            
        def clean_digits(text):
            # 1. Phần trăm: 6%, 37.5% -> TOKENPERCENT
            text = re.sub(r'\b\d+([.,]\d+)?\s*%', ' TOKENPERCENT ', text)

            # 2. Ngày tháng: 15/8, 30-12, 2024/01/01 -> TOKENDATE
            text = re.sub(r'\b\d{1,2}[/-]\d{1,2}([/-]\d{2,4})?\b', ' TOKENDATE ', text)

            # 3. Số tiền VN: 10.000, 1.500.000 -> TOKENNUM
            text = re.sub(r'\b\d{1,3}(\.\d{3})+\b', ' TOKENNUM ', text)

            # 4. Số thường (bắt cả số thập phân): 10, 3.14 -> TOKENNUM
            text = re.sub(r'\b\d+([.,]\d+)?\b', ' TOKENNUM ', text)
            
            # 5. Số La Mã: III, IV, IX -> TOKENNUM
            text = re.sub(r'\b[IVXLCDM]+\b', ' TOKENNUM ', text, flags=re.IGNORECASE)
            
            # Tỷ lệ: 1:2, 3/4 -> TOKENNUM
            text = re.sub(r'\b\d+\s*[:/]\s*\d+\b', ' TOKENNUM ', text)

            # ==========================================
            # 5. DỌN DẸP CHIẾN TRƯỜNG (TRIỆT TIÊU LỖI NÓI LẮP)
            # ==========================================
            
            # Gom các TOKENNUM đứng cạnh nhau (chỉ cách nhau bởi khoảng trắng hoặc dấu phẩy/chấm)
            # Ví dụ: "giá TOKENNUM , TOKENNUM triệu" -> "giá TOKENNUM triệu"
            text = re.sub(r'(TOKENNUM\s*[.,]?\s*)+', ' TOKENNUM ', text)

            # Dọn dẹp khoảng trắng thừa do nối chuỗi
            text = re.sub(r'\s+', ' ', text).strip()

            return text
            
        def clean_punctuation(text):
            # làm sạch các dấu câu văn bản
            # Bảo vệ dấu chấm giữa chữ (tp.hcm, pgs.ts)
            text = re.sub(r'(?<=[a-zđàáâ...])\.(?=[a-zđàáâ...])', '_', text)

            # Dấu kết câu → TOKENEOS
            text = re.sub(r'[.!?]+', ' TOKENEOS ', text)

            # Dấu câu còn lại → bỏ
            text = re.sub(r'[,;:()\[\]{}"\'\/\\|]', ' ', text)
            
            return text
            
        def clean_trash(text):
            # Loại bỏ các ký tự không mong muốn còn sót
            # Ký tự rác ==> space
            text = re.sub(
                r"[^\w\s<>"
                r"àáâãèéêìíòóôõùúýăđơư"
                r"ạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ"
                r"]", " ", text
            )
            text = re.sub(r'\s+', ' ', text)  # Xóa khoảng trắng thừa
            return text
        # Thực hiện các bước làm sạch
        text = encoding(text)
        text = clean_html(text)
        text = clean_structure(text)
        text = clean_special_chars(text)

        # mapping + lower
        text = map_emoji(text)
        text = map_rule(text)
        text = normalize_special_tokens(text)
        
        text = clean_digits(text)
        text = clean_punctuation(text)
        text = clean_trash(text)
        text = normalize_special_tokens(text)
        text = text.strip()
        
    return text
        
        
        

def is_valid_sentence(sent: str) -> bool:
    """Kiểm tra xem một câu có hợp lệ không sau khi đã được làm sạch.

    Args:
        sent (str): Câu cần kiểm tra tính hợp lệ sau khi đã được làm sạch.

    Returns:
        bool: True nếu câu hợp lệ, False nếu câu có khả năng là rác (quá ngắn, toàn số, tiếng nước ngoài, v.v.)
    """
    tokens = sent.split()
    
    # Quá ngắn
    if len(tokens) < 10:
        return False
    
    # Quá nhiều TOKENNUM (câu toàn số)
    if tokens.count('TOKENNUM') / len(tokens) > 0.4:
        return False
    
    # Quá nhiều UNK sau encode (câu tiếng nước ngoài)
    # Kiểm tra sau khi encode
    
    # Toàn ký tự Latin (tiếng Anh lọt vào)
    viet_chars = set('àáâãèéêìíòóôõùúýăđơưạảấầẩẫậắằẳẵặẹẻẽếềểễệỉịọỏốồổỗộớờởỡợụủứừửữựỳỵỷỹ')
    words_with_viet = sum(1 for w in tokens if any(c in viet_chars for c in w))
    if words_with_viet / len(tokens) < 0.3:  # < 30% từ có dấu tiếng Việt
        return False
    
    return True

def is_valid_article(article: dict) -> bool:

    content = article.get("content", "") or ""
    title   = article.get("title",   "") or ""

    # Không có nội dung
    if not content.strip():
        return False

    # Nội dung quá ngắn < 50 từ
    if len(content.split()) < 50:
        return False

    # Tiêu đề rỗng
    if not title.strip():
        return False

    # Nội dung trùng lặp hoàn toàn (duplicate bài)
    # Xử lý riêng bằng hash

    return True

'''
"url": "https://thanhnien.vn/huawei-trinh-lang-matebook-14-trang-bi-man-hinh-hien-thi-2k-1851423366.htm",
        "title": "Huawei trình làng MateBook 14 trang bị màn hình hiển thị 2K",
        "published_date": "2022-01-21T15:04:45+07:00",
        "content": "Toàn bộ thân máy của chiếc MateBook 14 được làm bằng kim loại và dùng màn hình 2k Fullview 14 inch, ​​với tỷ lệ màn hình so với thân máy là 90% và viền siêu mỏng ở cả bốn cạnh bao quanh một bảng điều khiển sáng, độ phân giải cao trong tỷ lệ khung hình 3:2 phù hợp hơn cho các tác vụ năng suất so với các màn hình khác có viền siêu rộng.\nMẫu laptop Huawei MateBook 14 mới\nt.luân\nVề cấu hình, MateBook 14 được trang bị bộ vi xử lý Intel Core thế hệ thứ 11, RAM 8 GB, SSD 512 GB, Wi-Fi 6. Trọng lượng MateBook 14 ở mức 1,49 kg, pin đủ để xem phim 11 tiếng. Pin máy cũng có thể sạc ngược cho thiết bị khác.\nNgoài ra, phím nguồn tích hợp cảm biến vân tay, đồng thời camera được thiết kế ẩn để đảm bảo riêng tư cần thiết và có thêm tính tính năng Huawei Share, cho phép kết nối liên tục giữa những thiết bị của Huawei gồm điện thoại, máy tính bảng, máy tính.\nTại thị trường Việt Nam, MateBook 14 dự kiến sẽ được công bố giá bán và ngày bán chính thức sau dịp Tết Nguyên đán.",
        
'''

# text_raw = "https://thanhnien.vn/huawei-trinh-lang-matebook-14-trang-bi-man-hinh-hien-thi-2k-1851423366.htm "

# text_raw += "Toàn bộ thân máy của chiếc MateBook 14 được làm bằng kim loại và dùng màn hình 2k Fullview 14 inch, ​​với tỷ lệ màn hình so với thân máy là 90% và viền siêu mỏng ở cả bốn cạnh bao quanh một bảng điều khiển sáng, độ phân giải cao trong tỷ lệ khung hình 3:2 phù hợp hơn cho các tác vụ năng suất so với các màn hình khác có viền siêu rộng.\nMẫu laptop Huawei MateBook 14 mới\nt.luân\nVề cấu hình, MateBook 14 được trang bị bộ vi xử lý Intel Core thế hệ thứ 11, RAM 8 GB, SSD 512 GB, Wi-Fi 6. Trọng lượng MateBook 14 ở mức 1,49 kg, pin đủ để xem phim 11 tiếng. Pin máy cũng có thể sạc ngược cho thiết bị khác.\nNgoài ra, phím nguồn tích hợp cảm biến vân tay, đồng thời camera được thiết kế ẩn để đảm bảo riêng tư cần thiết và có thêm tính tính năng Huawei Share, cho phép kết nối liên tục giữa những thiết bị của Huawei gồm điện thoại, máy tính bảng, máy tính.\nTại thị trường Việt Nam, MateBook 14 dự kiến sẽ được công bố giá bán và ngày bán chính thức sau dịp Tết Nguyên đán."

# print(clean_text(text_raw, type='article'))