import { useState, useRef, useEffect, useCallback, useMemo } from 'react';
import axios from 'axios';
import { toast } from 'sonner';
import { Save } from 'lucide-react';
import MarkdownEditor from '@/components/editors/MarkdownEditor'
import ExcalidrawEditor, { generateExcalidrawImageBase64 } from '@/components/editors/ExcalidrawEditor'


export default function DocumentEditor({ document, onDocumentUpdate, onFetchContent }) {
  const [content, setContent] = useState(null);
  const [saveStatus, setSaveStatus] = useState('saved');
  const [changeCounter, setChangeCounter] = useState(document.type == "markdown" ? -1 : -3);
  const [isLoadingContent, setIsLoadingContent] = useState(false);
  const saveTimeoutRef = useRef(null);

  useEffect(() => {
    const loadContent = async () => {
      if (!document.content && onFetchContent) {
        setIsLoadingContent(true);
        try {
          await onFetchContent(document.id);
        } catch (error) {
          console.error('Failed to load document content:', error);
          toast.error('Failed to load document content');
        } finally {
          setIsLoadingContent(false);
        }
      }
    };

    loadContent();
  }, [document.id, document.content, onFetchContent]);

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
        const b64image = await generateExcalidrawImageBase64(content);
        contentToSave = {
          raw: content,
          image: b64image
        };
      } else {
        contentToSave = {
          markdown: content,
        };
      }

      await axios.put(
        `/api/v1/projects/${document.project_id}/documents/${document.id}`,
        { content: contentToSave },
        { withCredentials: true }
      );

      setSaveStatus('saved');

      if (onDocumentUpdate) {
        onDocumentUpdate(document.id, { content: contentToSave });
      }
    } catch (error) {
      console.error("Error saving document:", error);
      setSaveStatus('unsaved');
      toast.error(`Failed to save document: ${error.response?.data?.detail || error.message}`);
    }
  }, [content, document.project_id, document.id, onDocumentUpdate]);

  useEffect(() => {
    if (changeCounter > 0 && saveStatus === 'unsaved') {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }

      saveTimeoutRef.current = setTimeout(() => {
        performSave();
      }, 200);
    }

    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current);
      }
    };
  }, [changeCounter, performSave, saveStatus]);

  const excalidrawInitialData = useMemo(() => {
    if (!document.content) return null;
    return content || document.content.raw;
  }, [content, document.content]);

  const saveIconBottomOffset = document.type === "markdown"
    ? 4
    : 16

  // Show loading state while content is being fetched
  if (isLoadingContent || !document.content) {
    return (
      <div className="flex items-center justify-center w-full h-full">
        <div className="text-muted-foreground">Loading document...</div>
      </div>
    );
  }

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