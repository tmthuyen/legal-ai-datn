import * as React from 'react';
import { SelectOption, SetState } from '@/shared/types/ui.types';
import { CheckIcon, ChevronDown, X } from 'lucide-react';
import { cn } from '@/lib/utils';
import { Button } from '@/components/ui/button';
import {
  Command,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';

export interface InputMultiSelectProvided {
  options: SelectOption[];
  onValueChange: (v: string[]) => void;
  placeholder: string;
  truncateCount: number;
  disabled: boolean;
  selectedValue: string[];
  setSelectedValue: SetState<string[]>;

  isPopoverOpen: boolean;
  setIsPopoverOpen: SetState<boolean>;
  onOptionSelect: (v: string) => void;
  onClearAllOptions: () => void;
}

export interface InputMultiSelectDisplayText {
  placeholder: string;
  selectAll: string;
  clear: string;
  close: string;
  search: string;
}

const displayText = {
  placeholder: 'Select...',
  selectAll: 'Select All',
  clear: 'Clear',
  close: 'Close',
  search: 'Search',
};

export const InputMultiSelect: React.FC<{
  options: SelectOption[];
  value: string[];
  onValueChange: (v: string[]) => void;
  placeholder?: string;
  truncateCount?: number;
  disabled?: boolean;
  className?: string;
  style?: React.CSSProperties;
  displayTextProps?: InputMultiSelectDisplayText;
  children: (v: InputMultiSelectProvided) => React.ReactNode;
}> = ({
  options,
  value = [],
  onValueChange,
  displayTextProps = displayText,
  placeholder = displayTextProps?.placeholder || displayText.placeholder,
  truncateCount = 3,
  disabled = false,
  className,
  children,
  ...restProps
}) => {
  const [selectedValue, setSelectedValue] = React.useState<string[]>(value);
  const [isPopoverOpen, setIsPopoverOpen] = React.useState(false);

  const onOptionSelect = (option: string) => {
    const newSelectedValues = selectedValue.includes(option)
      ? selectedValue.filter((value) => value !== option)
      : [...selectedValue, option];
    setSelectedValue(newSelectedValues);
    onValueChange(newSelectedValues);
  };

  const onClearAllOptions = () => {
    setSelectedValue([]);
    onValueChange([]);
  };

  const toggleAll = () => {
    if (selectedValue.length === options.length) {
      onClearAllOptions();
    } else {
      const allValues = options.map((option) => option.value);
      setSelectedValue(allValues);
      onValueChange(allValues);
    }
  };

  React.useEffect(() => {
    if (isPopoverOpen && JSON.stringify(value) !== JSON.stringify(selectedValue)) {
      setSelectedValue(value);
    }
  }, [isPopoverOpen]);

  return (
    <Popover open={isPopoverOpen} onOpenChange={setIsPopoverOpen}>
      <PopoverTrigger asChild>
        {children({
          options,
          onValueChange,
          placeholder,
          truncateCount,
          disabled,
          selectedValue,
          setSelectedValue,
          isPopoverOpen,
          setIsPopoverOpen,
          onOptionSelect,
          onClearAllOptions,
        })}
      </PopoverTrigger>
      <PopoverContent
        className={cn('w-auto p-0', className)}
        align="start"
        onEscapeKeyDown={() => setIsPopoverOpen(false)}
        {...restProps}
      >
        <Command>
          <CommandInput placeholder={displayTextProps?.search || displayText.search} />
          <CommandList className="max-h-[unset] overflow-y-hidden">
            <CommandEmpty>No results found.</CommandEmpty>
            <CommandGroup>
              <CommandItem key="all" onSelect={toggleAll} className="cursor-pointer">
                <div
                  className={cn(
                    'border-muted-foreground/50 mr-1 flex h-4 w-4 items-center justify-center rounded-md border',
                    selectedValue.length === options.length
                      ? 'bg-primary text-primary-foreground'
                      : 'opacity-50 [&_svg]:invisible',
                  )}
                >
                  <CheckIcon className="h-3.5 w-3.5" />
                </div>
                <span className="text-muted-foreground">
                  {displayTextProps?.selectAll || displayText.selectAll}
                </span>
              </CommandItem>
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup className="max-h-[20rem] min-h-[10rem] overflow-y-auto">
              {options.map((option) => {
                const isSelected = selectedValue.includes(option.value);
                return (
                  <CommandItem
                    key={option.value}
                    onSelect={() => onOptionSelect(option.value)}
                    className="cursor-pointer"
                  >
                    <div
                      className={cn(
                        'border-muted-foreground/50 mr-1 flex h-4 w-4 items-center justify-center rounded-md border',
                        isSelected
                          ? 'bg-primary text-primary-foreground'
                          : 'opacity-50 [&_svg]:invisible',
                      )}
                    >
                      <CheckIcon className="h-3.5 w-3.5" />
                    </div>
                    {option.icon && <option.icon className="text-muted-foreground mr-2 h-4 w-4" />}
                    <span>{option.label}</span>
                  </CommandItem>
                );
              })}
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup>
              <div className="flex items-center justify-between">
                {selectedValue.length > 0 && (
                  <>
                    <CommandItem
                      onSelect={onClearAllOptions}
                      className="flex-1 cursor-pointer justify-center"
                    >
                      {displayTextProps?.clear || 'Clear'}
                    </CommandItem>
                    <Separator orientation="vertical" className="flex h-full min-h-6" />
                  </>
                )}
                <CommandItem
                  onSelect={() => setIsPopoverOpen(false)}
                  className="max-w-full flex-1 cursor-pointer justify-center"
                >
                  {displayTextProps?.close || 'Close'}
                </CommandItem>
              </div>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
  );
};
InputMultiSelect.displayName = 'MultiSelect';

export const InputMultiSelectTrigger = React.forwardRef<
  HTMLButtonElement,
  InputMultiSelectProvided & {
    className?: string;
    children?: (v: SelectOption) => React.ReactNode;
    style?: React.CSSProperties;
      }
      >(
      (
        {
          options,
          // onValueChange,
          placeholder,
          truncateCount,
          disabled,
          selectedValue,
          // setSelectedValue,
          // isPopoverOpen,
          setIsPopoverOpen,
          onOptionSelect,
          onClearAllOptions,
          className,
          style,
          children,
        },
        ref,
      ) => {
        const onTogglePopover = () => {
          setIsPopoverOpen((prev) => !prev);
        };

        return (
          <Button
            ref={ref}
            onClick={onTogglePopover}
            variant="outline"
            type="button"
            disabled={disabled}
            className={cn(
              'flex h-auto min-h-11 w-full items-center justify-between p-1 [&_svg]:pointer-events-auto',
              'hover:bg-transparent',
              disabled && '[&_svg]:pointer-events-none',
              className,
            )}
            style={style}
          >
            {selectedValue.length > 0 ? (
              <div className="flex w-full items-center justify-between">
                <div className="flex flex-wrap items-center px-1">
                  {selectedValue.slice(0, truncateCount).map((value, index) => {
                    const option = options.find((o) => o.value === value);

                    if (!option) {
                      return <div key={`${index}-${value}`}></div>;
                    }

                    if (children) {
                      return <div key={`${index}-${value}`}>{children(option)}</div>;
                    }

                    return (
                      <Badge
                        key={`${index}-${value}`}
                        className={cn(
                          'bg-muted text-foreground hover:bg-muted mr-1 flex cursor-default items-center border-transparent',
                        )}
                      >
                        {option?.icon && <option.icon className="mr-1 h-3.5 w-3.5" />}
                        {option?.label}
                        {/* <X
                      className="text-muted-foreground hover:text-foreground ml-1 h-3.5 w-3.5 cursor-pointer bg-red-200"
                      onClick={(e) => {
                        e.stopPropagation();
                        onOptionSelect(value);
                        console.log('Cleared option:', value);
                      }}
                    /> */}
                        <span
                          className="text-muted-foreground hover:text-destructive ml-1 h-4 w-4 cursor-pointer"
                          onClick={(e) => {
                            e.stopPropagation();
                            onOptionSelect(value);
                          }}
                        >
                      X
                        </span>
                      </Badge>
                    );
                  })}
                  {selectedValue.length > truncateCount && (
                    <div className={cn('text-muted-foreground cursor-default py-1 pl-1.5')}>
                      {`+${selectedValue.length - truncateCount}`}
                    </div>
                  )}
                </div>
                <div className="flex items-center justify-between">
                  <X
                    className="text-muted-foreground mx-2 h-4 cursor-pointer"
                    onClick={(e) => {
                      e.stopPropagation();
                      onClearAllOptions();
                    }}
                  />
                  <Separator orientation="vertical" className="flex h-full min-h-6" />
                  <ChevronDown className="text-muted-foreground mx-2 h-4 cursor-pointer" />
                </div>
              </div>
            ) : (
              <div className="mx-auto flex w-full items-center justify-between">
                <span className="text-muted-foreground mx-3 text-sm">{placeholder}</span>
                <ChevronDown className="text-muted-foreground mx-2 h-4 cursor-pointer" />
              </div>
            )}
          </Button>
        );
      },
      );
InputMultiSelectTrigger.displayName = 'InputMultiSelectTrigger';
