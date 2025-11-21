import { Pencil, Trash2, BookTemplate } from 'lucide-react';

export default function DocumentActionsModal({ document, onClose, onEdit, onDelete, onCreateTemplate }) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 w-full max-w-sm">
        <h2 className="text-xl font-bold mb-4">Document Actions</h2>
        <div className="space-y-2">
          <button
            onClick={() => {
              onClose();
              onEdit();
            }}
            className="w-full text-left px-4 py-3 rounded-md hover:bg-gray-100 flex items-center gap-3 transition-colors"
          >
            <Pencil className="w-5 h-5 text-gray-600" />
            <div>
              <div className="font-medium">Rename</div>
              <div className="text-sm text-gray-500">Change document name</div>
            </div>
          </button>
          <button
            onClick={() => {
              onClose();
              onCreateTemplate();
            }}
            className="w-full text-left px-4 py-3 rounded-md hover:bg-gray-100 flex items-center gap-3 transition-colors"
          >
            <BookTemplate className="w-5 h-5 text-blue-600" />
            <div>
              <div className="font-medium">Create Template</div>
              <div className="text-sm text-gray-500">Publish to library</div>
            </div>
          </button>
          <button
            onClick={() => {
              onClose();
              onDelete();
            }}
            className="w-full text-left px-4 py-3 rounded-md hover:bg-red-50 flex items-center gap-3 transition-colors"
          >
            <Trash2 className="w-5 h-5 text-red-600" />
            <div>
              <div className="font-medium text-red-600">Delete</div>
              <div className="text-sm text-gray-500">Remove document</div>
            </div>
          </button>
        </div>
        <div className="mt-4 pt-4 border-t">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  );
}
