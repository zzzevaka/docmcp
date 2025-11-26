import { Pencil, Trash2, BookTemplate } from 'lucide-react';

export default function DocumentActionsModal({ document, onClose, onEdit, onDelete, onCreateTemplate }) {
  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
      <div className="bg-background border border-border rounded-lg p-6 w-full max-w-sm shadow-lg">
        <h2 className="text-xl font-bold mb-4 text-foreground">Document Actions</h2>
        <div className="space-y-2">
          <button
            onClick={() => {
              onClose();
              onEdit();
            }}
            className="w-full text-left px-4 py-3 rounded-md hover:bg-accent flex items-center gap-3 transition-colors"
          >
            <Pencil className="w-5 h-5 text-muted-foreground" />
            <div>
              <div className="font-medium text-foreground">Rename</div>
              <div className="text-sm text-muted-foreground">Change document name</div>
            </div>
          </button>
          <button
            onClick={() => {
              onClose();
              onCreateTemplate();
            }}
            className="w-full text-left px-4 py-3 rounded-md hover:bg-accent flex items-center gap-3 transition-colors"
          >
            <BookTemplate className="w-5 h-5 text-blue-600 dark:text-blue-400" />
            <div>
              <div className="font-medium text-foreground">Create Template</div>
              <div className="text-sm text-muted-foreground">Publish to library</div>
            </div>
          </button>
          <button
            onClick={() => {
              onClose();
              onDelete();
            }}
            className="w-full text-left px-4 py-3 rounded-md hover:bg-red-50 dark:hover:bg-red-900/20 flex items-center gap-3 transition-colors"
          >
            <Trash2 className="w-5 h-5 text-red-600 dark:text-red-400" />
            <div>
              <div className="font-medium text-red-600 dark:text-red-400">Delete</div>
              <div className="text-sm text-muted-foreground">Remove document</div>
            </div>
          </button>
        </div>
        <div className="mt-4 pt-4 border-t border-border">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
