'use client';

import {
  Field,
  FieldContent,
  FieldDescription,
  FieldLabel,
  FieldTitle,
} from '@/components/ui/field';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { useColor } from '@/hooks/useColor';
import { Monitor, Moon, Sun } from 'lucide-react';
import { useTheme } from 'next-themes';
import React from 'react';

// SEO
// export const metadata = {
//   title: 'Theme Settings',
//   description: 'Manage your theme settings',
// };

function ThemePage() {
  const { theme, setTheme } = useTheme();
  const { color, changeColor } = useColor();
  const [mounted, setMounted] = React.useState(false);

  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return <div className="mx-auto animate-pulse space-y-6 p-4">Loading your preferences...</div>;
  }

  // console.log('Current theme:', theme);

  return (
    <div className="mx-auto mt-4 mb-8 w-full space-y-6">
      {/* Theme mode: light, dark, system */}
      <div className="">
        <div className="mb-3 flex-col items-start gap-2">
          <h2 className="text-lg font-semibold">Chế độ</h2>
          <p className="text-muted-foreground text-sm">Chọn chế độ chủ đề bạn ưa thích.</p>
        </div>
        <RadioGroup
          defaultValue={theme}
          className="grid-cols-1 sm:grid-cols-3"
          onValueChange={(value) => setTheme(value)}
        >
          <FieldLabel htmlFor="light" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <Sun className="text-primary h-6 w-6" />
                <FieldTitle>Light</FieldTitle>
                <FieldDescription>Light theme</FieldDescription>
              </FieldContent>
              <RadioGroupItem value="light" id="light" />
            </Field>
          </FieldLabel>
          <FieldLabel htmlFor="dark" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <Moon className="text-primary h-6 w-6" />
                <FieldTitle>Dark</FieldTitle>
                <FieldDescription>Dark theme</FieldDescription>
              </FieldContent>
              <RadioGroupItem value="dark" id="dark" />
            </Field>
          </FieldLabel>
          <FieldLabel htmlFor="system" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <Monitor className="text-primary h-6 w-6" />
                <FieldTitle>System</FieldTitle>
                <FieldDescription>Follow your system&apos;s theme.</FieldDescription>
              </FieldContent>
              <RadioGroupItem value="system" id="system" />
            </Field>
          </FieldLabel>
        </RadioGroup>
      </div>

      {/* Theme color: rose, emerald, blue, violet, orange */}
      <div className="">
        <div className="mb-3 flex-col items-start gap-2">
          <h2 className="block text-lg font-semibold">Màu chủ đạo</h2>
          <p className="text-muted-foreground block text-sm">Chọn màu chủ đạo bạn ưa thích.</p>
        </div>
        <RadioGroup
          defaultValue={color}
          className="grid-cols-1 sm:grid-cols-2"
          onValueChange={(value) =>
            changeColor(value as 'rose' | 'emerald' | 'blue' | 'violet' | 'orange')
          }
        >
          <FieldLabel htmlFor="rose" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <div className="flex items-center gap-4">
                  <div className="h-15 w-15 rounded-md bg-rose-500 transition-transform hover:scale-105 hover:bg-rose-600" />
                  <div className="space-y-1">
                    <FieldTitle>Rose</FieldTitle>
                    <FieldDescription>Rose theme</FieldDescription>
                  </div>
                </div>
              </FieldContent>
              <RadioGroupItem value="rose" id="rose" />
            </Field>
          </FieldLabel>
          <FieldLabel htmlFor="emerald" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <div className="flex items-center gap-4">
                  <div className="h-15 w-15 rounded-md bg-emerald-500 transition-transform hover:scale-105 hover:bg-emerald-600" />
                  <div className="space-y-1">
                    <FieldTitle>Emerald</FieldTitle>
                    <FieldDescription>Emerald theme</FieldDescription>
                  </div>
                </div>
              </FieldContent>
              <RadioGroupItem value="emerald" id="emerald" />
            </Field>
          </FieldLabel>
          <FieldLabel htmlFor="blue" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <div className="flex items-center gap-4">
                  <div className="h-15 w-15 rounded-md bg-blue-500 transition-transform hover:scale-105 hover:bg-blue-600" />
                  <div className="space-y-1">
                    <FieldTitle>Blue</FieldTitle>
                    <FieldDescription>Blue theme</FieldDescription>
                  </div>
                </div>
              </FieldContent>
              <RadioGroupItem value="blue" id="blue" />
            </Field>
          </FieldLabel>
          <FieldLabel htmlFor="violet" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <div className="flex items-center gap-4">
                  <div className="h-15 w-15 rounded-md bg-violet-500 transition-transform hover:scale-105 hover:bg-violet-600" />
                  <div className="space-y-1">
                    <FieldTitle>Violet</FieldTitle>
                    <FieldDescription>Violet theme</FieldDescription>
                  </div>
                </div>
              </FieldContent>
              <RadioGroupItem value="violet" id="violet" />
            </Field>
          </FieldLabel>
          <FieldLabel htmlFor="orange" className="cursor-pointer">
            <Field orientation="horizontal">
              <FieldContent>
                <div className="flex items-center gap-4">
                  <div className="h-15 w-15 rounded-md bg-orange-500 transition-transform hover:scale-105 hover:bg-orange-600" />
                  <div className="space-y-1">
                    <FieldTitle>Orange</FieldTitle>
                    <FieldDescription>Orange theme</FieldDescription>
                  </div>
                </div>
              </FieldContent>
              <RadioGroupItem value="orange" id="orange" />
            </Field>
          </FieldLabel>
        </RadioGroup>
      </div>
    </div>
  );
}

export default ThemePage;
