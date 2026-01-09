import React, { Suspense, useCallback, useEffect, useRef, useState, useMemo } from "react";
import { exportToBlob } from "@excalidraw/excalidraw";
import { useTheme } from "next-themes";

const ExcalidrawLazy = React.lazy(async () => {
  return import("@excalidraw/excalidraw").then((m) => ({ default: m.Excalidraw }));
});
import "@excalidraw/excalidraw/index.css";

const DEFAULT_EXCALIDRAW_DATA = { type: "excalidraw", version: 2, elements: [], appState: {}, files: {} };

function sanitizeAppState(appState) {
  if (!appState) return {};
  const { collaborators, ...rest } = appState;
  return rest;
}

function sanitizeInitialData(data) {
  if (!data) {
    return DEFAULT_EXCALIDRAW_DATA;
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


const UIOptions = { canvasActions: { export: false, loadScene: false } }


export default function ExcalidrawEditor({ initialData, onChange, readOnly, excalidrawRef }) {
  const { resolvedTheme } = useTheme();

  const clean = useMemo(() => {
    const sanitized = sanitizeInitialData(initialData);
    const appState = {
      ...sanitized.appState,
      theme: resolvedTheme === 'dark' ? 'dark' : 'light',
    };

    if (readOnly) {
      appState.viewModeEnabled = true;
    }

    return {
      ...sanitized,
      appState,
    };
  }, []);

  const handleChange = useCallback((elements, appState, files) => {
    if (!readOnly && onChange) {
      onChange({ elements, appState, files });
    }
  }, [readOnly, onChange]);

  const handleExcalidrawAPI = useCallback((api) => {
    if (excalidrawRef) {
      excalidrawRef.current = api;
    }
  }, [excalidrawRef]);

  return (
    <div className="w-full h-full">
      <Suspense fallback={
        <div className="flex items-center justify-center h-full">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
            <p className="mt-4 text-gray-600">Loading whiteboard...</p>
          </div>
        </div>
      }>
        <ExcalidrawLazy
          initialData={clean}
          onChange={handleChange}
          excalidrawAPI={handleExcalidrawAPI}
          UIOptions={UIOptions}
          viewModeEnabled={readOnly}
        />
      </Suspense>
    </div>
  );
}
