import { Pencil, Trash2, BookTemplate } from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export default function DocumentActionsModal({ document, isOpen, onClose, onEdit, onDelete, onCreateTemplate }) {
  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-[375px]">
        <DialogHeader>
          <DialogTitle>Document Actions</DialogTitle>
        </DialogHeader>
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
        <DialogFooter className="mt-4 pt-4 border-t border-border">
          <Button
            onClick={onClose}
            variant="outline"
            className="w-full"
          >
            Cancel
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
