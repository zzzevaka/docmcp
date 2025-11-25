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

function Teams() {
  const navigate = useNavigate()
  const [teams, setTeams] = useState([])
  const [pendingInvitations, setPendingInvitations] = useState([])
  const [loading, setLoading] = useState(true)
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newTeamName, setNewTeamName] = useState('')
  const dataFetched = useRef(false)

  const fetchData = async () => {
    try {
      const [teamsRes, invitationsRes] = await Promise.all([
        axios.get('/api/v1/teams/', { withCredentials: true }),
        axios.get('/api/v1/invitations/me', { withCredentials: true }),
      ])
      setTeams(teamsRes.data)
      setPendingInvitations(invitationsRes.data)
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

  const handleCreateTeam = async (e) => {
    e.preventDefault()
    if (!newTeamName.trim()) return

    try {
      await axios.post(
        '/api/v1/teams/',
        { name: newTeamName },
        { withCredentials: true }
      )
      setNewTeamName('')
      setShowCreateModal(false)
      fetchData()
    } catch (error) {
      console.error('Failed to create team:', error)
      toast.error('Failed to create team')
    }
  }

  const handleAcceptInvitation = async (invitationId) => {
    try {
      await axios.post(
        `/api/v1/invitations/${invitationId}/accept`,
        {},
        { withCredentials: true }
      )
      fetchData()
      toast.success('Invitation accepted!')
    } catch (error) {
      console.error('Failed to accept invitation:', error)
      toast.error('Failed to accept invitation')
    }
  }

  const handleRejectInvitation = async (invitationId) => {
    try {
      await axios.post(
        `/api/v1/invitations/${invitationId}/reject`,
        {},
        { withCredentials: true }
      )
      fetchData()
      toast.info('Invitation rejected')
    } catch (error) {
      console.error('Failed to reject invitation:', error)
      toast.error('Failed to reject invitation')
    }
  }

  if (loading) {
    return (
      <MainLayout activeTab="teams">
        <div className="flex items-center justify-center py-12">
          <div className="text-center">
            <div className="inline-block animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="mt-4 text-muted-foreground">Loading teams...</p>
          </div>
        </div>
      </MainLayout>
    )
  }

  return (
    <MainLayout activeTab="teams">
      <div className="py-6">
        {/* Pending Invitations Section */}
        {pendingInvitations.length > 0 && (
          <div className="mb-8 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <h2 className="text-xl font-semibold text-foreground mb-4">
              Pending Invitations
            </h2>
            <div className="space-y-2">
              {pendingInvitations.map((invitation) => (
                <div
                  key={invitation.id}
                  className="bg-card border border-border p-4 rounded-lg shadow-sm flex justify-between items-center"
                >
                  <div>
                    <p className="font-medium text-card-foreground">
                      {invitation.team_name}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Invited by {invitation.inviter_email}
                    </p>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleRejectInvitation(invitation.id)}
                      className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => handleAcceptInvitation(invitation.id)}
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90"
                    >
                      Accept
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Teams Section */}
        <div className="flex justify-between items-center mb-6 pb-12">
          <Breadcrumb>
            <BreadcrumbList className="text-2xl">
              <BreadcrumbItem>
                <BreadcrumbPage className="font-bold">Teams</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90"
          >
            Create Team
          </button>
        </div>

        {teams.length === 0 ? (
          <div className="text-center py-12">
            <p className="text-muted-foreground mb-4">No teams yet</p>
            <button
              onClick={() => setShowCreateModal(true)}
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90"
            >
              Create Your First Team
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {teams.map((team) => (
              <div
                key={team.id}
                onClick={() => navigate(`/teams/${team.id}`)}
                className="bg-card border border-border p-6 rounded-lg shadow-sm hover:shadow-md transition-shadow cursor-pointer"
              >
                <h3 className="text-lg font-semibold text-card-foreground mb-2">
                  {team.name}
                </h3>
                <p className="text-sm text-muted-foreground mb-2">
                  Created {new Date(team.created_at).toLocaleDateString()}
                </p>
              </div>
            ))}
          </div>
        )}

        {/* Create Team Modal */}
        {showCreateModal && (
          <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
            <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
              <h2 className="text-2xl font-bold mb-4 text-foreground">Create New Team</h2>
              <form onSubmit={handleCreateTeam}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Team Name
                  </label>
                  <input
                    type="text"
                    value={newTeamName}
                    onChange={(e) => setNewTeamName(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Enter team name"
                    autoFocus
                  />
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowCreateModal(false)
                      setNewTeamName('')
                    }}
                    className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90"
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

export default Teams
