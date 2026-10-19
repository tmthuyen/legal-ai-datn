'use client';

import { zodResolver } from '@hookform/resolvers/zod';
import { Loader2 } from 'lucide-react';
import { useMemo } from 'react';
import { type FieldValues, type Path, type Resolver, useForm } from 'react-hook-form';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { cn } from '@/lib/utils';

/** Loại field hỗ trợ trong form CRUD — mở rộng khi cần (giữ cố ý minimal). */
export interface CrudFormField {
  /** Tên field — khớp key của schema zod / defaultValues. */
  name: string;
  label: string;
  type?: 'text' | 'textarea' | 'select' | 'multiselect';
  /** Dành cho `select`/`multiselect`. */
  options?: { value: string; label: string }[];
  placeholder?: string;
  /** Ẩn nhãn thị giác (vẫn giữ cho screen reader). */
  hideLabel?: boolean;
}

interface CrudFormDialogProps<T extends Record<string, unknown>> {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title: string;
  description?: string;
  /** Schema zod validation (dùng chung để build defaultValues). */
  schema: z.ZodType<T>;
  fields: CrudFormField[];
  defaultValues: T;
  onSubmit: (values: T) => void | Promise<void>;
  submitting?: boolean;
}

/**
 * Dialog form CRUD dùng chung (react-hook-form + zod, shadcn Dialog):
 * mọi trang admin khai báo `fields` + `schema` — không viết lại form.
 * Error message hiển thị inline theo field (tiếng Việt do schema cung cấp).
 */
export function CrudFormDialog<T extends Record<string, unknown>>({
  open,
  onOpenChange,
  title,
  description,
  schema,
  fields,
  defaultValues,
  onSubmit,
  submitting = false,
}: CrudFormDialogProps<T>) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
  } = useForm<T>({
    // @hookform/resolvers khai input = FieldValues, schema của ta khai input unknown → cast 2 lớp.
    resolver: zodResolver(schema as unknown as z.ZodType<unknown, FieldValues>) as unknown as
      Resolver<T>,
    values: defaultValues, // đồng bộ lại khi đổi item đang sửa
  });

  // setValue/watch với tên field string động (generic T) — cast 1 đầu vào helper.
  const setFormValue = setValue as unknown as (
    name: string,
    value: unknown,
    options?: { shouldValidate: boolean }
  ) => void;
  const watchFormValue = watch as unknown as (name: string) => unknown;

  const renderField = (field: CrudFormField) => {
    const type = field.type ?? 'text';
    const error = errors[field.name]?.message as string | undefined;
    const fieldId = `crud-field-${field.name}`;

    const inputClassName = cn('w-full', error && 'border-destructive focus-visible:border-destructive');

    return (
      <div key={field.name} className="space-y-1.5">
        <Label htmlFor={fieldId} className={cn(field.hideLabel && 'sr-only')}>
          {field.label}
        </Label>

        {type === 'textarea' ? (
          <Textarea
            id={fieldId}
            placeholder={field.placeholder}
            className={inputClassName}
            rows={4}
            {...register(field.name as Path<T>)}
          />
        ) : type === 'select' ? (
          <select
            id={fieldId}
            className={cn(
              'border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex h-9 w-full rounded-md border px-3 py-1 text-sm shadow-xs transition-[color,box-shadow] focus-visible:ring-2 focus-visible:outline-none',
              inputClassName,
            )}
            {...register(field.name as Path<T>)}
          >
            {(field.options ?? []).map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        ) : type === 'multiselect' ? (
          <div
            className={cn(
              'max-h-44 space-y-1.5 overflow-y-auto rounded-md border p-2',
              error && 'border-destructive',
            )}
            role="group"
            aria-label={field.label}
          >
            {(field.options ?? []).length === 0 ? (
              <p className="text-muted-foreground text-sm">Không có lựa chọn.</p>
            ) : (
              (field.options ?? []).map((option) => {
                const selected = ((watchFormValue(field.name) as string[] | undefined) ?? []).includes(
                  option.value,
                );
                return (
                  <label
                    key={option.value}
                    className="hover:bg-accent flex cursor-pointer items-center gap-2 rounded px-1.5 py-1 text-sm"
                  >
                    <input
                      type="checkbox"
                      checked={selected}
                      onChange={() => {
                        const current = ((watchFormValue(field.name) as string[] | undefined) ??
                          []
                        ).slice();
                        const next = selected
                          ? current.filter((value) => value !== option.value)
                          : [...current, option.value];
                        setFormValue(field.name, next, { shouldValidate: true });
                      }}
                      className="accent-primary size-4"
                    />
                    {option.label}
                  </label>
                );
              })
            )}
          </div>
        ) : (
          <Input
            id={fieldId}
            placeholder={field.placeholder}
            className={inputClassName}
            {...register(field.name as Path<T>)}
          />
        )}

        {error ? (
          <p role="alert" className="text-destructive text-sm">
            {error}
          </p>
        ) : null}
      </div>
    );
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[85vh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description ? <DialogDescription>{description}</DialogDescription> : null}
        </DialogHeader>

        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4" noValidate>
          {fields.map(renderField)}

          <DialogFooter className="gap-2 pt-2">
            <Button
              type="button"
              variant="outline"
              onClick={() => onOpenChange(false)}
              disabled={submitting}
              className="cursor-pointer"
            >
              Hủy
            </Button>
            <Button type="submit" disabled={submitting} className="cursor-pointer">
              {submitting ? <Loader2 className="size-4 animate-spin" aria-hidden="true" /> : null}
              Lưu
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  );
}

/** Build `defaultValues` từ dữ liệu edit/create — dùng chung ở mọi trang. */
export function buildDefaults<T extends Record<string, unknown>>(
  fields: CrudFormField[],
  source?: object | null,
): T {
  const record = source as Record<string, unknown> | null | undefined;
  const defaults: Record<string, unknown> = {};
  fields.forEach((field) => {
    const value = record?.[field.name];
    if (field.type === 'multiselect') {
      defaults[field.name] = Array.isArray(value) ? value.map(String) : [];
    } else {
      defaults[field.name] = value === undefined || value === null ? '' : String(value);
    }
  });
  return defaults as T;
}

/**
 * `defaultValues` memo theo item đang sửa — tránh reset form mỗi render
 * (RHF `values` prop so sánh theo reference).
 */
export function useCrudFormValues<T extends Record<string, unknown>>(
  fields: CrudFormField[],
  editing: object | null,
): T {

  return useMemo(() => buildDefaults<T>(fields, editing), [editing, fields]);
}
