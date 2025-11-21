import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import MarkdownEditor from '@/components/editors/MarkdownEditor'
import ExcalidrawEditor, { generateExcalidrawImageBase64 } from '@/components/editors/ExcalidrawEditor'


export default function DocumentEditor({ document }) {
  const [content, setContent] = useState(null);
  const [saveStatus, setSaveStatus] = useState('saved'); // 'saved', 'saving', 'unsaved'
  const excalidrawRef = useRef(null);
  const saveTimeoutRef = useRef(null);
  const contentRef = useRef(content);

  // Keep contentRef in sync with content
  useEffect(() => {
    contentRef.current = content;
  }, [content]);

  const handleMarkdownChange = useCallback((data) => {
    setContent(data);
    setSaveStatus('unsaved');
  }, []);

  const handleExcalidrawChange = useCallback((data) => {
    console.log('whiteboard changed')
    setContent(data);
    setSaveStatus('unsaved');
  }, []);

  const performSave = useCallback(async () => {
    console.log('performSave called, status:', saveStatus);
    setSaveStatus('saving');
    try {
      let contentToSave;

      if (document.type === "whiteboard") {
        // Get current scene data from Excalidraw ref
        if (!excalidrawRef.current) {
          throw new Error("Excalidraw API not available");
        }

        const sceneData = {
          elements: excalidrawRef.current.getSceneElements(),
          appState: excalidrawRef.current.getAppState(),
          files: excalidrawRef.current.getFiles(),
        };

        const b64image = await generateExcalidrawImageBase64(sceneData);
        contentToSave = {
          raw: sceneData,
          image: b64image
        };
      } else {
        contentToSave = {
          markdown: contentRef.current,
        };
      }

      console.log('Saving content:', contentToSave);

      await axios.put(
        `/api/v1/projects/${document.project_id}/documents/${document.id}`,
        { content: contentToSave },
        { withCredentials: true }
      );

      console.log('Save successful');
      // After successful save:
      setSaveStatus('saved');
    } catch (error) {
      console.error("Error saving document:", error);
      setSaveStatus('unsaved');
      toast.error(`Failed to save document: ${error.response?.data?.detail || error.message}`);
    }
  }, [document.project_id, document.id, excalidrawRef]);

  // Auto-save with debounce
  useEffect(() => {
    console.log('useEffect triggered, saveStatus:', saveStatus);
    if (saveStatus === 'unsaved') {
      // Clear any existing timeout
      if (saveTimeoutRef.current) {
        console.log('Clearing existing timeout');
        clearTimeout(saveTimeoutRef.current);
      }

      // Set new timeout for 5 seconds
      console.log('Setting new timeout for 5 seconds');
      saveTimeoutRef.current = setTimeout(() => {
        console.log('Timeout fired, calling performSave');
        performSave();
      }, 200);
    }

    // Cleanup on unmount
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [saveStatus, performSave]);

  // Мемоизируем initialData чтобы не создавать новую ссылку на каждом рендере
  const excalidrawInitialData = useMemo(() => {
    return content || document.content.raw;
  }, [content, document.content.raw]);

  return (
    <div className="relative w-full h-full">
      {
        document.type === "markdown" && (
          <MarkdownEditor
            markdown={content || document.content.markdown}
            onChange={handleMarkdownChange}
            readOnly={false}
          />
        )
      }
      {
        (document.type === "whiteboard") && (
          <ExcalidrawEditor
            initialData={excalidrawInitialData}
            onChange={handleExcalidrawChange}
            readOnly={false}
            excalidrawRef={excalidrawRef}
          />
        )
      }
    </div>
  )
}