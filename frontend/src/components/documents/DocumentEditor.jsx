import { useState, useRef } from 'react';
import axios from 'axios';
import MarkdownEditor from '@/components/editors/MarkdownEditor'
import ExcalidrawEditor, { generateExcalidrawImageBase64 } from '@/components/editors/ExcalidrawEditor'


export default function DocumentEditor({ document }) {
  const [content, setContent] = useState(null);
  const [changed, setChanged] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const excalidrawRef = useRef(null);

  const handleMarkdownChange = (data) => {
    setContent(data);
    setChanged(true);
  }

  const handleExcalidrawChange = (data) => {
    setContent(data);
    setChanged(true);
  }

  const handleSave = async () => {
    setIsSaving(true);
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
          markdown: content,
        };
      }

      // Call the PUT documents API
      await axios.put(
        `/api/v1/projects/${document.project_id}/documents/${document.id}`,
        { content: contentToSave },
        { withCredentials: true }
      );

      // After successful save:
      setChanged(false);
    } catch (error) {
      console.error("Error saving document:", error);
      alert(`Failed to save document: ${error.response?.data?.detail || error.message}`);
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <>
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
            initialData={content || document.content.raw}
            onChange={handleExcalidrawChange}
            readOnly={false}
            excalidrawRef={excalidrawRef}
          />
        )
      }

      {changed && (
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={`
            absolute bottom-2.5 right-2.5
            px-5 py-2.5
            bg-black text-white
            rounded
            font-semibold text-sm
            shadow-md
            z-[1000]
          `}
        >
          Save
        </button>
      )}
    </>
  )
}