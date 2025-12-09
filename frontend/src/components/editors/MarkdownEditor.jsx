import { Milkdown, MilkdownProvider, useEditor } from "@milkdown/react";
import { Crepe } from "@milkdown/crepe";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import "@milkdown/crepe/theme/common/style.css";
import "@milkdown/crepe/theme/frame.css";
import "./MarkdownEditor.css";

function MilkdownEditor({ markdown, onChange, readOnly }) {
  const { resolvedTheme } = useTheme();

  useEditor((root) => {
    const crepe = new Crepe({
      root,
      defaultValue: markdown,
      featureConfigs: {
        [Crepe.Feature.ImageBlock]: {
          onUpload: async (file) => {
            // Convert file to base64 data URI
            return new Promise((resolve, reject) => {
              const reader = new FileReader();
              reader.onload = (e) => {
                resolve(e.target?.result);
              };
              reader.onerror = (e) => {
                reject(new Error('Failed to read file'));
              };
              reader.readAsDataURL(file);
            });
          },
        },
      },
    });
    crepe.setReadonly(readOnly);

    crepe.on((listener) => {
      listener.markdownUpdated((_, markdown) => {
        onChange?.(markdown);
      });
    });

    return crepe;
  });

  return (
    <div
      className={`w-full h-full bg-white dark:bg-background ${
        (resolvedTheme === 'dark')
          ? 'dark milkdown-theme-dark'
          : 'milkdown-theme-light'
      }`}
    >
      <Milkdown />
    </div>
  );
}

export default function MarkdownEditor({ markdown, onChange, readOnly }) {
  return (
    <MilkdownProvider>
      <MilkdownEditor markdown={markdown} onChange={onChange} readOnly={readOnly} />
    </MilkdownProvider>
  );
}
