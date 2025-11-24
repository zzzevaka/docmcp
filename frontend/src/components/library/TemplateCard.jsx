import { FileText, Image, FolderPlus } from 'lucide-react';

export default function TemplateCard({ template, onClick }) {
  const Icon = template.type === 'markdown' ? FileText : Image;

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
      </div>
      <h3 className="font-medium text-gray-900 truncate">{template.name}</h3>
    </div>
  );
}
