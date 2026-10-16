#  Duyệt đồ thị neuro symbolic theo các yêu cầu từ retrieval service
#  Được sử dụng trực tiếp với retrieval service


from src.graph.graph_service import LegalGraphService


class BaseGraphTraverse:
    def __init__(self, graph_service: LegalGraphService):
        self.graph_service = graph_service

    # Duyệt các nốt hậu duệ của node hiện tại

    # Lọc các document trong danh sách các nodes truyền vào chứa document_id

    # Tìm kiếm các quan hệ pháp lý của một nốt với các node khác ngoại trừ CONTAINS

    # Duyệt các quan hệ của danh sach các nodes

    #
