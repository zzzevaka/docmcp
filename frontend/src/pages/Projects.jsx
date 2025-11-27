import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'
import { toast } from 'sonner'
import MainLayout from '../components/layout/MainLayout'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbList,
  BreadcrumbPage,
} from '@/components/ui/breadcrumb'

function Projects() {
  const navigate = useNavigate()
  const [projects, setProjects] = useState([])
  const [teams, setTeams] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newProjectName, setNewProjectName] = useState('')
  const [selectedTeamId, setSelectedTeamId] = useState('')
  const dataFetched = useRef(false)

  const fetchData = async () => {
    try {
      const [projectsRes, teamsRes] = await Promise.all([
        axios.get('/api/v1/projects/', { withCredentials: true }),
        axios.get('/api/v1/teams/', { withCredentials: true }),
      ])
      setProjects(projectsRes.data)
      setTeams(teamsRes.data)
      if (teamsRes.data.length > 0) {
        setSelectedTeamId(teamsRes.data[0].id)
      }
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    // Prevent double fetch in React StrictMode
    if (dataFetched.current) return
    dataFetched.current = true
    fetchData()
  }, [])

  const handleCreateProject = async (e) => {
    e.preventDefault()
    if (!newProjectName.trim() || !selectedTeamId) return

    try {
      await axios.post(
        '/api/v1/projects/',
        {
          name: newProjectName,
          team_id: selectedTeamId,
        },
        { withCredentials: true }
      )
      setNewProjectName('')
      setShowCreateModal(false)
      fetchData()
    } catch (error) {
      console.error('Failed to create project:', error)
      toast.error('Failed to create project')
    }
  }

  if (loading) {
    return null;
  }

  return (
    <MainLayout>
      <div className="py-6">
        <div className="flex justify-between items-center mb-6 pb-12">
          <Breadcrumb>
            <BreadcrumbList className="text-2xl">
              <BreadcrumbItem>
                <BreadcrumbPage className="font-bold">Projects</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            disabled={teams.length === 0}
          >
            Create Project
          </button>
        </div>

        {teams.length === 0 ? (
          <div className="text-center py-12 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <p className="text-foreground mb-4">
              You need to create a team first before creating projects
            </p>
            <button
              onClick={() => navigate('/teams')}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Go to Teams
            </button>
          </div>
        ) : projects.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No projects yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
            >
              Create Your First Project
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {projects.map((project) => (
              <div
                key={project.id}
                onClick={() => navigate(`/projects/${project.id}`)}
                className="bg-card border border-border p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              >
                <h3 className="text-lg font-semibold text-card-foreground mb-2">
                  {project.name}
                </h3>
                <p className="text-sm text-muted-foreground">
                  Created {new Date(project.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Create Project Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
            <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
              <h2 className="text-2xl font-bold mb-4 text-foreground">Create New Project</h2>
              <form onSubmit={handleCreateProject}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Project Name
                  </label>
                  <input
                    type="text"
                    value={newProjectName}
                    onChange={(e) => setNewProjectName(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Enter project name"
                    autoFocus
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Team
                  </label>
                  <select
                    value={selectedTeamId}
                    onChange={(e) => setSelectedTeamId(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    {teams.map((team) => (
                      <option key={team.id} value={team.id}>
                        {team.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
                    onClick={() => {
                      setShowCreateModal(false)
                      setNewProjectName('')
                    }}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
                  >
                    Create
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}

export default Projects
