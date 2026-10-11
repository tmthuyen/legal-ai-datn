# # src/utils/checkpoint_manager.py
# """
# CheckpointManager — lưu và restore toàn bộ trạng thái training.

# Lưu mỗi epoch:
#   - Model weights (state_dict)
#   - Optimizer state (momentum, adaptive LR của Adam)
#   - Scheduler state
#   - Training history (loss/ppl theo epoch)
#   - Epoch hiện tại, best epoch, best val ppl
#   - Config đã dùng

# Cách dùng:
#   # Trong LSTMTextModel / TransformerTextModel
#   ckpt = CheckpointManager("data/checkpoints/lstm")
#   ckpt.save(epoch, model, optimizer, scheduler, history, meta)

#   # Resume
#   state = ckpt.load_latest()
#   if state:
#       model.load_state_dict(state["model"])
#       start_epoch = state["epoch"] + 1
# """

# import json
# import os
# import glob
# import torch
# import numpy as np
# from utils.logger import setup_logger

# logger = setup_logger("CheckpointManager")


# class CheckpointManager:
#     """
#     Quản lý checkpoint cho một model cụ thể.

#     Cấu trúc thư mục:
#       data/checkpoints/{model_type}/
#         ├── epoch_001.pt       ← checkpoint mỗi epoch
#         ├── epoch_002.pt
#         ├── best.pt            ← checkpoint tốt nhất (val_ppl thấp nhất)
#         └── meta.json          ← thông tin tổng hợp, dễ đọc
#     """

#     def __init__(self, checkpoint_dir: str, keep_last_n: int = 3):
#         """
#         checkpoint_dir : thư mục lưu checkpoint, VD: "data/checkpoints/lstm"
#         keep_last_n    : giữ lại N checkpoint gần nhất (tránh đầy disk)
#                          checkpoint "best" luôn được giữ riêng
#         """
#         self.dir         = checkpoint_dir
#         self.keep_last_n = keep_last_n
#         os.makedirs(self.dir, exist_ok=True)

#     # ──────────────────────────────────────────────────────────────────
#     # SAVE
#     # ──────────────────────────────────────────────────────────────────

#     def save(
#         self,
#         epoch:          int,
#         model:          torch.nn.Module,
#         optimizer:      torch.optim.Optimizer,
#         history:        dict,
#         meta:           dict,
#         scheduler=None,
#         is_best:        bool = False,
#     ) -> str:
#         """
#         Lưu checkpoint sau mỗi epoch.

#         epoch     : epoch vừa hoàn thành (1-indexed)
#         model     : nn.Module (NextWordLSTM / NextWordTransformer)
#         optimizer : optimizer hiện tại
#         history   : dict lịch sử loss/ppl
#         meta      : dict thông tin thêm (best_epoch, best_val_ppl, config, ...)
#         scheduler : learning rate scheduler (optional)
#         is_best   : True nếu epoch này có val_ppl tốt nhất → lưu thêm best.pt
#         """
#         state = {
#             "epoch":     epoch,
#             "model":     model.state_dict(),
#             "optimizer": optimizer.state_dict(),
#             "history":   history,
#             "meta":      meta,
#         }
#         if scheduler is not None:
#             # Lưu state của tất cả scheduler được truyền vào
#             if isinstance(scheduler, (list, tuple)):
#                 state["schedulers"] = [
#                     s.state_dict() if s is not None else None
#                     for s in scheduler
#                 ]
#             else:
#                 state["schedulers"] = [scheduler.state_dict()]

#         # Lưu checkpoint epoch
#         epoch_path = os.path.join(self.dir, f"epoch_{epoch:03d}.pt")
#         torch.save(state, epoch_path)
#         logger.info(f"💾 Checkpoint saved → {epoch_path}")

#         # Lưu best checkpoint riêng
#         if is_best:
#             best_path = os.path.join(self.dir, "best.pt")
#             torch.save(state, best_path)
#             logger.info(
#                 f"⭐ Best checkpoint updated → {best_path} "
#                 f"(val_ppl={meta.get('best_val_perplexity', '?'):.4f})"
#             )

#         # Lưu meta.json để dễ đọc không cần load .pt
#         self._save_meta_json(epoch, meta, history, is_best)

#         # Xóa checkpoint cũ, chỉ giữ keep_last_n
#         self._cleanup_old_checkpoints()

#         return epoch_path

#     # ──────────────────────────────────────────────────────────────────
#     # LOAD
#     # ──────────────────────────────────────────────────────────────────

#     def load_latest(self, device: str = "cpu") -> dict | None:
#         """
#         Load checkpoint mới nhất để resume training.
#         Trả None nếu chưa có checkpoint nào.
#         """
#         latest = self._find_latest_epoch_checkpoint()
#         if latest is None:
#             logger.info("Không tìm thấy checkpoint — bắt đầu training mới.")
#             return None

#         logger.info(f"🔄 Resuming từ checkpoint: {latest}")
#         state = torch.load(latest, map_location=device)
#         logger.info(
#             f"✅ Loaded epoch {state['epoch']} | "
#             f"best_val_ppl={state['meta'].get('best_val_perplexity', 'N/A')}"
#         )
#         return state

#     def load_best(self, device: str = "cpu") -> dict | None:
#         """Load best checkpoint (val_ppl thấp nhất) — dùng cho inference."""
#         best_path = os.path.join(self.dir, "best.pt")
#         if not os.path.exists(best_path):
#             logger.warning("Không tìm thấy best.pt")
#             return None
#         state = torch.load(best_path, map_location=device)
#         logger.info(
#             f"✅ Loaded best checkpoint epoch {state['epoch']} | "
#             f"val_ppl={state['meta'].get('best_val_perplexity', 'N/A')}"
#         )
#         return state

#     def has_checkpoint(self) -> bool:
#         """Kiểm tra xem đã có checkpoint chưa."""
#         return self._find_latest_epoch_checkpoint() is not None

#     def get_meta(self) -> dict | None:
#         """Đọc meta.json không cần load toàn bộ weights."""
#         meta_path = os.path.join(self.dir, "meta.json")
#         if not os.path.exists(meta_path):
#             return None
#         with open(meta_path, encoding="utf-8") as f:
#             return json.load(f)

#     # ──────────────────────────────────────────────────────────────────
#     # PRIVATE
#     # ──────────────────────────────────────────────────────────────────

#     def _find_latest_epoch_checkpoint(self) -> str | None:
#         pattern   = os.path.join(self.dir, "epoch_*.pt")
#         checkpoints = sorted(glob.glob(pattern))
#         return checkpoints[-1] if checkpoints else None

#     def _save_meta_json(self, epoch: int, meta: dict, history: dict, is_best: bool):
#         """Lưu thông tin tóm tắt dạng JSON — dễ đọc, không cần PyTorch."""
#         meta_path = os.path.join(self.dir, "meta.json")

#         # Lấy loss/ppl epoch mới nhất
#         last_train_loss = history.get("train_loss",       [None])[-1]
#         last_val_loss   = history.get("val_loss",         [None])[-1]
#         last_train_ppl  = history.get("train_perplexity", [None])[-1]
#         last_val_ppl    = history.get("val_perplexity",   [None])[-1]

#         summary = {
#             "last_epoch":          epoch,
#             "best_epoch":          meta.get("best_epoch"),
#             "best_val_perplexity": meta.get("best_val_perplexity"),
#             "stopped_early":       meta.get("stopped_early", False),
#             "last_train_loss":     round(last_train_loss, 6) if last_train_loss else None,
#             "last_val_loss":       round(last_val_loss, 6)   if last_val_loss   else None,
#             "last_train_ppl":      round(last_train_ppl, 4)  if last_train_ppl  else None,
#             "last_val_ppl":        round(last_val_ppl, 4)    if last_val_ppl    else None,
#             "is_best_epoch":       is_best,
#             "config":              meta.get("config", {}),
#             "checkpoint_dir":      self.dir,
#         }

#         with open(meta_path, "w", encoding="utf-8") as f:
#             json.dump(summary, f, ensure_ascii=False, indent=2)

#     def _cleanup_old_checkpoints(self):
#         """Giữ lại keep_last_n checkpoint epoch, xóa cái cũ hơn."""
#         pattern     = os.path.join(self.dir, "epoch_*.pt")
#         checkpoints = sorted(glob.glob(pattern))

#         if len(checkpoints) > self.keep_last_n:
#             to_delete = checkpoints[:-self.keep_last_n]
#             for path in to_delete:
#                 os.remove(path)
#                 logger.debug(f"Xóa checkpoint cũ: {path}")
