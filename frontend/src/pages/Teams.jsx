import { useState, useEffect } from 'react'
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { useTeams, usePendingInvitations } from '../recoil/hooks'

function Teams() {
  const navigate = useNavigate()
  const { teams, loading: teamsLoading, fetchTeams, refreshTeams } = useTeams()
  const { invitations: pendingInvitations, loading: invitationsLoading, fetchInvitations, refreshInvitations } = usePendingInvitations()
  const [showCreateModal, setShowCreateModal] = useState(false)
  const [newTeamName, setNewTeamName] = useState('')

  const loading = teamsLoading || invitationsLoading

  useEffect(() => {
    fetchTeams()
    fetchInvitations()
  }, [fetchTeams, fetchInvitations])

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
      refreshTeams()
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
      refreshTeams()
      refreshInvitations()
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
      refreshInvitations()
      toast.info('Invitation rejected')
    } catch (error) {
      console.error('Failed to reject invitation:', error)
      toast.error('Failed to reject invitation')
    }
  }

  const content = (
    loading || !teams
      ? null
      : teams.length === 0 ? (
      <div className="text-center py-12">
        <p className="text-muted-foreground mb-4">No teams yet</p>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
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
    )
  );

  return (
    <MainLayout activeTab="teams">
      <div className="py-6">
        {/* Pending Invitations Section */}
        {pendingInvitations && pendingInvitations.length > 0 && (
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
                      className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
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
          <Breadcrumb className="mr-6">
            <BreadcrumbList className="text-2xl">
              <BreadcrumbItem>
                <BreadcrumbPage className="font-bold">Teams</BreadcrumbPage>
              </BreadcrumbItem>
            </BreadcrumbList>
          </Breadcrumb>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            Create Team
          </button>
        </div>

        {content}

        {/* Create Team Modal */}
        <Dialog open={showCreateModal} onOpenChange={setShowCreateModal}>
          <DialogContent className="sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>Create New Team</DialogTitle>
            </DialogHeader>
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
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowCreateModal(false)
                    setNewTeamName('')
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit">
                  Create
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>
      </div>
    </MainLayout>
  )
}

export default Teams
