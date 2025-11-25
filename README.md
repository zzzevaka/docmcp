# DocMCP - Documentation as MCP

![Project Documentation](docs/screenshots/welcome.png)

DocMCP is a light-weight application that bridges the gap between human documentation and AI assistants. Create, organize, and share your project documentation while making it instantly accessible to LLM agents through MCP (Model Context Protocol).

## Quick start

Try the [DEMO](https://docmcp-demo.onrender.com/) or run in Docker

```bash
docker run -d -p 8000:8000 \
  -v docmcp_data:/app/data \
  -e APP_ENV=production \
  -e LOCAL_AUTH_ENABLED=true \
  zzzevaka/docmcp:latest
```

## Key Use Cases

### 1. Project Documentation Hub

Create documentation for your projects with rich markdown and whiteboard support, organized structure, and easy navigation.

![Project Documentation](docs/screenshots/project-docs.png)

### 2. Template Library

Build reusable documentation templates that maintain consistency across projects. Create templates for common documentation patterns and deploy them instantly to new projects.

![Template Library](docs/screenshots/templates.png)

### 3. MCP Integration

Connect your documentation directly to AI assistants through Model Context Protocol. Your documentation becomes instantly queryable by Claude and other MCP-compatible agents.

![MCP Connection](docs/screenshots/mcp-integration.png)

## Features

- **Rich Markdown Editor**: Write documentation with full markdown support including code blocks, tables, and more
- **Whiteboard Support**: Visual collaboration with diagrams, flowcharts, and sketches embedded in your documentation
- **Project Organization**: Organize docs by projects with hierarchical structure
- **Template System**: Create and reuse documentation templates across projects
- **MCP Integration**: Automatic exposure of documentation through Model Context Protocol
- **Team Collaboration**: Share projects and docs with your team
- **Version Control**: Track changes to your documentation over time
- **Search & Discovery**: Quickly find the documentation you need
- **Flexible Authentication**: Local email/password registration or optional Google OAuth

## Deployment

### Local dev environment

Start the development environment:

```bash
docker-compose up -d
```

Access at:
- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000

### Single container

```bash
docker build -t docmcp:latest .
docker run --rm -p 8002:8000 \
  -v docmcp_data:/app/data \
  -e APP_ENV=production \
  -e LOCAL_AUTH_ENABLED=true \
  docmcp:latest
```

### Authentication
- Local authentication:
  - `LOCAL_AUTH_ENABLED=true`
- Google OAuth2:
  - `GOOGLE_CLIENT_ID=<client>`
  - `GOOGLE_CLIENT_SECRET=<secret>`

## Roadmap

- [ ] Real-time collaboration on documents
- [ ] Document version comparison
- [ ] Custom MCP tool definitions
- [ ] API documentation auto-generation
- [ ] Integration with popular dev tools (GitHub, GitLab, Jira)
- [ ] Advanced permissions and access control
- [ ] Document analytics and insights

