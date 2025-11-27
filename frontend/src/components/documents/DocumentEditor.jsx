import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Save } from 'lucide-react';
import MarkdownEditor from '@/components/editors/MarkdownEditor'
import ExcalidrawEditor, { generateExcalidrawImageBase64 } from '@/components/editors/ExcalidrawEditor'


export default function DocumentEditor({ document }) {
  const [content, setContent] = useState(null);
  const [saveStatus, setSaveStatus] = useState('saved');
  const [changeCounter, setChangeCounter] = useState(document.type == "markdown" ? -1 : -3);
  const excalidrawRef = useRef(null);
  const saveTimeoutRef = useRef(null);
  const contentRef = useRef(content);

  // Keep contentRef in sync with content
  useEffect(() => {
    contentRef.current = content;
  }, [content]);

  const handleChange = useCallback((data) => {
      setChangeCounter(prev => prev + 1);
      setContent(data);
      setSaveStatus('unsaved');
  }, []);

  const performSave = useCallback(async () => {
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
    if (changeCounter > 0 && saveStatus === 'unsaved') {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      saveTimeoutRef.current = setTimeout(() => {
        performSave();
      }, 500);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [changeCounter, performSave]);

  const excalidrawInitialData = useMemo(() => {
    return content || document.content.raw;
  }, [content, document.content.raw]);

  const saveIconBottomOffset = document.type === "markdown"
    ? 4
    : 16

  return (
    <div className="relative w-full h-full">
      {
        document.type === "markdown" && (
          <MarkdownEditor
            key={document.id}
            markdown={document.content.markdown}
            onChange={handleChange}
            readOnly={false}
          />
        )
      }
      {
        (document.type === "whiteboard") && (
          <ExcalidrawEditor
            key={document.id}
            initialData={excalidrawInitialData}
            onChange={handleChange}
            readOnly={false}
            excalidrawRef={excalidrawRef}
          />
        )
      }

      {/* Save status indicator - only show when not saved */}
      {(changeCounter > 0 && saveStatus !== 'saved') && (
        <div
          className={`fixed bottom-${saveIconBottomOffset} right-4 opacity-70 z-40 backdrop-blur-sm rounded-md shadow-md`}
          title={saveStatus === 'saving' ? 'Saving...' : 'Unsaved changes'}
        >
          <Save className="w-5 h-5 text-primary" />
        </div>
      )}
    </div>
  )
}