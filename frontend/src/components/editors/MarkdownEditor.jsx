import { Milkdown, MilkdownProvider, useEditor } from "@milkdown/react";
import { Crepe } from "@milkdown/crepe";

import "@milkdown/crepe/theme/common/style.css";
import "@milkdown/crepe/theme/frame.css";

function MilkdownEditor({ markdown, onChange, readOnly }) {
  useEditor((root) => {
    const crepe = new Crepe({ root, defaultValue: markdown });
    crepe.setReadonly(readOnly);

    crepe.on((listener) => {
      listener.markdownUpdated((_, markdown) => {
        onChange?.(markdown);
      });
    });

    return crepe;
  });

  return <Milkdown />;
}

export default function MarkdownEditor({ markdown, onChange, readOnly }) {
  return (
    <MilkdownProvider>
      <MilkdownEditor markdown={markdown} onChange={onChange} readOnly={readOnly} />
    </MilkdownProvider>
  );
}
