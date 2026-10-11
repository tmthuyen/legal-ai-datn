# File: src/utils/teencode_dict.py

# 1. BẢNG MAPPING TỪ VIẾT TẮT -> TIẾNG VIỆT CHUẨN
TEENCODE_MAP = {
    # Nhóm phủ định / Câu hỏi
    "k": "không", "ko": "không", "khong": "không", "kg": "không", 
    "hok": "không", "hem": "không", "hông": "không",
    "j": "gì", "gi": "gì", "z": "vậy", "dz": "vậy", "zj": "vậy", "zậy": "vậy",

    # Nhóm đại từ nhân xưng
    "m": "mình", "mk": "mình", "t": "tao", "b": "bạn", "bn": "bạn",
    "c": "chồng", "ck": "chồng", "v": "vợ", "vk": "vợ", "ny": "người_yêu", 
    "2ny": "người_yêu", "ad": "quản_trị_viên",

    # Nhóm động từ / Tính từ
    "dc": "được", "đc": "được", "duoc": "được",
    "vs": "với", "r": "rồi", "rùi": "rồi", "lm": "làm", "đg": "đang", "dag": "đang",
    "wa": "quá", "wá": "quá", "wa'": "qua", "thjk": "thích", "iu": "yêu", 
    "mún": "muốn", "mun": "muốn", "ns": "nói", "nt": "nhắn_tin",

    # Nhóm danh từ / Trạng từ thời gian
    "hum": "hôm", "hnay": "hôm_nay", "hqua": "hôm_qua",
    "sp": "sản_phẩm", "vđ": "vấn_đề", "sz": "kích_cỡ",
    "sg": "sài_gòn", "hn": "hà_nội",

    # Nhóm cảm thán / Slang
    "ak": "à", "uk": "ừ", "uh": "ừ", "oke": "ok", "ô kê": "ok",
    "vl": "rất", "vcl": "rất", "sml": "sấp_mặt", "cheems": "trời_ơi", 
    "chòi oi": "trời_ơi", "omg": "ôi_trời_ơi",

    # Nhóm từ mượn Tiếng Anh phổ biến
    "ib": "nhắn_tin", "rep": "trả_lời", "off": "ngoại_tuyến", "on": "trực_tuyến",
    "avt": "ảnh_đại_diện", "kute": "dễ_thương", "sr": "xin_lỗi", 
    "tks": "cảm_ơn", "3q": "cảm_ơn", "3n": "cảm_ơn",
    "klq": "không_liên_quan", "f.a": "độc_thân", "add": "kết_bạn",
    "pls": "làm_ơn", "plz": "làm_ơn", "bz": "bận", "bzz": "bận",
    "cu": "tạm_biệt", "cya": "tạm_biệt", "4u": "cho_bạn", "gr8": "tuyệt_vời"
}

# 2. HÀM XỬ LÝ QUY TẮC CHỮ (Thay thế quy tắc 9x như ph->f, ng->q)
def normalize_typing_rules(word: str) -> str:
    """Xử lý các luật gõ teencode theo cấu trúc từ"""
    if not word: return word
    
    # Đổi 'f' ở đầu thành 'ph' (VD: fa -> pha, fim -> phim)
    if word.startswith('f'):
        word = 'ph' + word[1:]
    # Đổi 'q' ở đầu thành 'qu' hoặc 'ng' (Tùy ngữ cảnh, tạm thời đổi các từ quen thuộc)
    if word == "qá": return "quá"
    if word == "qen": return "quen"
    
    return word

# 3. NHÓM ICON CẢM XÚC (Đưa về chung 1 token để model hiểu đây là biểu cảm)
EMOJI_MAP = {
    ":))": "TOKENSMILE", "=))": "TOKENSMILE", ":v": "TOKENSMILE", 
    "xD": "TOKENSMILE", "^^": "TOKENSMILE", "lol": "TOKENSMILE",
    "huhu": "TOKENSAD"
}

# 4. Nhóm từ viết tắt phổ biến 
COMMON_ABBREVIATIONS = {
    "thg": "tháng", "năm": "năm", "t2": "thứ_hai", "t3": "thứ_ba",
    "t4": "thứ_tư", "t5": "thứ_năm", "t6": "thứ_sáu", 
    "t7": "thứ_bảy", "cn": "chủ_nhật"
}