import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

export default function MCPInstructionsModal({ project, onClose }) {
  const [copied, setCopied] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState('claudeCode');

  // Construct the MCP URL
  // For local development, use HTTP (port 9080)
  // For production, use the actual protocol from the browser
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const mcpUrl = `${window.location.protocol}//${window.location.host}/api/mcp/${project.id}`;

  // Generate instructions based on selected system
  const getInstructions = () => {
    switch (selectedSystem) {
      case 'claudeCode':
        return {
          title: 'Claude Code',
          description: 'To connect this project\'s documentation to Claude Code, run the following command in your terminal:',
          content: `claude mcp add --transport http docs ${mcpUrl}`,
          type: 'command'
        };
      case 'cursor':
        return {
          title: 'Cursor',
          description: 'To connect this project\'s documentation to Cursor, add the following to your MCP settings:',
          content: JSON.stringify({
            "mcpServers": {
              "docs": {
                "url": `"${mcpUrl}"`
              }
            }
          }, null, 2),
          type: 'json',
          note: 'Open Settings -> Cursor Settings → Tools & MCP → New MCP Server'
        };
      default:
        return null;
    }
  };

  const instructions = getInstructions();

  const handleCopy = () => {
    navigator.clipboard.writeText(instructions.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50 p-4">
      <div className="bg-background border border-border rounded-lg w-full max-w-2xl max-h-[80vh] flex flex-col shadow-lg">
        {/* Header - fixed */}
        <div className="p-6 pb-4 border-b border-border flex-shrink-0">
          <h2 className="text-xl font-bold mb-4 text-foreground">Connect MCP</h2>

          {/* System selector */}
          <div>
            <label className="block text-sm font-medium text-foreground mb-2">
              Select your AI coding assistant:
            </label>
            <select
              value={selectedSystem}
              onChange={(e) => {
                setSelectedSystem(e.target.value);
                setCopied(false);
              }}
              className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="claudeCode">Claude Code</option>
              <option value="cursor">Cursor</option>
            </select>
          </div>
        </div>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto p-6">
          <div className="space-y-4 text-foreground">
            <p className="text-sm">
              {instructions.description}
            </p>

            {instructions.note && (
              <p className="text-sm bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-md p-3 text-blue-800 dark:text-blue-300">
                <strong>Note:</strong> {instructions.note}
              </p>
            )}

            <div className="bg-muted rounded-lg p-4 relative">
              <code className="text-sm font-mono break-all block pr-12 whitespace-pre-wrap text-foreground">
                {instructions.content}
              </code>
              <button
                onClick={handleCopy}
                className="absolute top-4 right-4 p-2 rounded-md hover:bg-accent transition-colors"
                title="Copy to clipboard"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-green-600 dark:text-green-400" />
                ) : (
                  <Copy className="w-4 h-4 text-muted-foreground" />
                )}
              </button>
            </div>

            <div className="space-y-2 text-sm">
              <p className="font-medium">Available tools:</p>
              <ul className="list-disc list-inside space-y-1 ml-2">
                <li><code className="text-xs bg-muted px-1 rounded">list_documents</code> - List all documents with their hierarchy</li>
                <li><code className="text-xs bg-muted px-1 rounded">search_documents</code> - Search documents by name or content</li>
                <li><code className="text-xs bg-muted px-1 rounded">get_document</code> - Get the full content of a specific document</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Footer - fixed */}
        <div className="p-6 pt-4 border-t border-border flex-shrink-0">
          <button
            onClick={onClose}
            className="w-full px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}
