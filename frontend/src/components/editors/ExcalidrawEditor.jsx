import React, { Suspense, useCallback, useEffect, useRef, useState } from "react";
import { exportToBlob } from "@excalidraw/excalidraw";

const ExcalidrawLazy = React.lazy(async () => {
  return import("@excalidraw/excalidraw").then((m) => ({ default: m.Excalidraw }));
});


function sanitizeAppState(appState) {
  if (!appState) return {};
  const { collaborators, ...rest } = appState;
  return rest;
}

function sanitizeInitialData(data) {
  if (!data) {
    return { type: "excalidraw", version: 2, elements: [], appState: {}, files: {} };
  }
  return { ...data, appState: sanitizeAppState(data.appState) };
}

function makeSnapshot(elements, appState, files) {
  return { type: "excalidraw", version: 2, source: "ui", elements, appState: sanitizeAppState(appState), files };
}


export async function generateExcalidrawImageBase64(excalidrawData, options = {}) {
  const {
    mimeType = "image/png",
    quality = 0.92,
    scale = 2,
  } = options;

  const { elements, appState, files } = excalidrawData;

  // Export to blob using Excalidraw's built-in export function
  const blob = await exportToBlob({
    elements,
    appState,
    files: files || {},
    mimeType,
    quality,
    exportPadding: 20,
    getDimensions: (width, height) => ({
      width: width * scale,
      height: height * scale,
      scale,
    }),
  });

  // Convert blob to base64
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onloadend = () => {
      resolve(reader.result);
    };
    reader.onerror = reject;
    reader.readAsDataURL(blob);
  });
}


export default function ExcalidrawEditor({ initialData, onChange, readOnly, excalidrawRef }) {
  const clean = sanitizeInitialData(initialData);

  return (
      <Suspense>
        <ExcalidrawLazy
          initialData={clean}
          onChange={onChange}
          excalidrawAPI={(api) => {
            if (excalidrawRef) {
              excalidrawRef.current = api;
            }
          }}
          UIOptions={{ canvasActions: { export: false, loadScene: false } }}
        />
      </Suspense>
  );
}
