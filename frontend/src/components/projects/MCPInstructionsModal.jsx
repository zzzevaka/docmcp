import { Copy, Check } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import axios from 'axios';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

export default function MCPInstructionsModal({ project, isOpen, onClose }) {
  const [copied, setCopied] = useState(false);
  const [selectedSystem, setSelectedSystem] = useState('claudeCode');
  const [tokens, setTokens] = useState([]);
  const [selectedToken, setSelectedToken] = useState('');
  const [loadingTokens, setLoadingTokens] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchTokens();
    }
  }, [isOpen]);

  const fetchTokens = async () => {
    setLoadingTokens(true);
    try {
      const response = await axios.get('/api/v1/api-tokens/', { withCredentials: true });
      setTokens(response.data);
      if (response.data.length > 0) {
        setSelectedToken(response.data[0].id);
      }
    } catch (error) {
      console.error('Failed to fetch API tokens:', error);
    } finally {
      setLoadingTokens(false);
    }
  };

  // Construct the MCP URL
  // For local development, use HTTP (port 9080)
  // For production, use the actual protocol from the browser
  const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
  const mcpUrl = `${window.location.protocol}//${window.location.host}/api/mcp/${project.id}`;

  // Get the selected token object
  const currentToken = tokens.find(t => t.id === selectedToken);
  const tokenValue = currentToken ? currentToken.token : '<API token>';

  // Generate instructions based on selected system
  const getInstructions = () => {
    switch (selectedSystem) {
      case 'claudeCode':
        return {
          title: 'Claude Code',
          description: 'To connect this project\'s documentation to Claude Code, run the following command in your terminal:',
          content: `claude mcp add --transport http docs ${mcpUrl} --header "Authorization: Bearer ${tokenValue}"`,
          type: 'command'
        };
      case 'cursor':
        return {
          title: 'Cursor',
          description: 'To connect this project\'s documentation to Cursor, add the following to your MCP settings:',
          content: JSON.stringify({
            "mcpServers": {
              "docs": {
                "url": mcpUrl,
                "headers": {
                  "Authorization": `Bearer ${tokenValue}`
                }
              }
            }
          }, null, 2),
          type: 'json',
          note: 'Open Settings -> Cursor Settings → Tools & MCP → New MCP Server'
        };
      case 'antigravity':
        return {
          title: 'Cursor',
          description: 'To connect this project\'s documentation to Google Antigravity, add the following to your MCP settings:',
          content: JSON.stringify({
            "mcpServers": {
              "docs": {
                "serverUrl": mcpUrl,
                "headers": {
                  "Authorization": `Bearer ${tokenValue}`
                }
              }
            }
          }, null, 2),
          type: 'json',
          note: '... -> MCP Servers → Manage MCP Servers → View raw config'
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
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="sm:max-w-2xl max-h-[80vh] flex flex-col">
        <DialogHeader className="pb-4 border-b border-border flex-shrink-0">
          <DialogTitle>Connect MCP</DialogTitle>

          {/* Token selector */}
          <div className="mt-4">
            <label className="block text-sm font-medium text-foreground mb-2">
              Choose API token:
            </label>
            {loadingTokens ? (
              <div className="text-sm text-muted-foreground">Loading tokens...</div>
            ) : tokens.length === 0 ? (
              <div className="text-sm text-yellow-600 dark:text-yellow-500 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded-md p-3">
                No API tokens found. Please create one in <Link className="text-primary" to="/settings/profile">Profile Settings</Link> first.
              </div>
            ) : (
              <select
                value={selectedToken}
                onChange={(e) => {
                  setSelectedToken(e.target.value);
                  setCopied(false);
                }}
                className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              >
                {tokens.map((token) => (
                  <option key={token.id} value={token.id}>
                    {token.name}
                  </option>
                ))}
              </select>
            )}
          </div>

          {/* System selector */}
          <div className="mt-4">
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
              <option value="antigravity">Google Antigravity</option>
              <option value="cursor">Cursor</option>
            </select>
          </div>
        </DialogHeader>

        {/* Scrollable content */}
        <div className="flex-1 overflow-y-auto">
          {tokens.length > 0 ? (
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
                  <li><code className="text-xs bg-muted px-1 rounded">create_document</code> - Create a new document</li>
                  <li><code className="text-xs bg-muted px-1 rounded">edit_document</code> - Edit an existing document</li>
                </ul>
              </div>
            </div>
          ) : null}
        </div>

        <DialogFooter className="pt-4 border-t border-border flex-shrink-0">
          <Button onClick={onClose} className="w-full">
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
