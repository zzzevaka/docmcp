export default function CategoryPill({ category, isActive, onClick }) {
  return (
    <button
      onClick={onClick}
      className={`w-full px-4 py-2 rounded-full text-sm font-medium transition-colors text-left ${
        isActive
          ? 'bg-blue-500 text-white'
          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
      }`}
    >
      {category.name}
    </button>
  );
}
