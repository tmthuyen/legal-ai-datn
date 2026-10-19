'use client';

import { ConfirmDialog } from '@/components/common/ConfirmDialog';

interface CrudDeleteDialogProps {
  /** Bản ghi đang xóa — `null` = đóng dialog. */
  target: { id: number | string; label: string } | null;
  onCancel: () => void;
  onConfirm: () => void;
  isPending?: boolean;
  /** Tên loại bản ghi, vd: 'thể loại', 'phim'. */
  entityLabel?: string;
}

/**
 * Hộp thoại xác nhận xóa dùng chung cho mọi trang CRUD admin
 * (bọc `ConfirmDialog` sẵn có — không viết lại).
 */
export function CrudDeleteDialog({
  target,
  onCancel,
  onConfirm,
  isPending = false,
  entityLabel = 'bản ghi',
}: CrudDeleteDialogProps) {
  return (
    <ConfirmDialog
      isOpen={Boolean(target)}
      title={`Xác nhận xóa ${entityLabel}`}
      description={
        target
          ? `Bạn có chắc chắn muốn xóa "${target.label}"? Hành động này không thể hoàn tác.`
          : ''
      }
      confirmText={isPending ? 'Đang xóa…' : 'Xóa'}
      cancelText="Hủy"
      variant="destructive"
      onConfirm={onConfirm}
      onCancel={onCancel}
    />
  );
}
