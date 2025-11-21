import { FileText, Image, FolderPlus } from 'lucide-react';

export default function TemplateCard({ template, onClick, onAddToProject }) {
  const Icon = template.type === 'markdown' ? FileText : Image;

  const handleAddClick = (e) => {
    e.stopPropagation(); // Prevent card click
    if (onAddToProject) {
      onAddToProject(template);
    }
  };

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-gray-300 p-4 cursor-pointer hover:border-blue-500 hover:shadow-sm transition-all h-32 flex flex-col justify-between group"
    >
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Icon className="w-4 h-4 text-gray-400" />
          <span className="text-xs text-gray-500 capitalize">{template.type}</span>
        </div>
        {onAddToProject && (
          <button
            onClick={handleAddClick}
            className="opacity-0 group-hover:opacity-100 p-1 hover:bg-blue-100 rounded transition-all"
            title="Add to project"
          >
            <FolderPlus className="w-4 h-4 text-blue-600" />
          </button>
        )}
      </div>
      <h3 className="font-medium text-gray-900 truncate">{template.name}</h3>
    </div>
  );
}
