import { FileText, Image, FolderTree } from 'lucide-react';

export default function TemplateCard({ template, onClick }) {
  // Choose icon based on whether template has children or its type
  const Icon = template.has_children
    ? FolderTree
    : template.type === 'markdown'
    ? FileText
    : Image;

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6 cursor-pointer"
    >
      <div className="flex items-start justify-between mb-2">
        <h3 className="text-lg font-semibold text-gray-900 flex-1 pr-2">
          {template.name}
        </h3>
        <Icon className="w-5 h-5 text-gray-400 flex-shrink-0" />
      </div>
      <p className="text-sm text-gray-600">
        Created {new Date(template.created_at).toLocaleDateString()}
      </p>
    </div>
  );
}
