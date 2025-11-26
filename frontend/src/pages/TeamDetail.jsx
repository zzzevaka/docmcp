import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import axios from 'axios'
import { toast } from 'sonner'
import { AlertTriangle } from 'lucide-react'
import MainLayout from '../components/layout/MainLayout'
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'

function TeamDetail() {
  const { teamId } = useParams()
  const navigate = useNavigate()
  const [team, setTeam] = useState(null)
  const [members, setMembers] = useState([])
  const [currentUser, setCurrentUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [showInviteModal, setShowInviteModal] = useState(false)
  const [showEditDialog, setShowEditDialog] = useState(false)
  const [showRemoveMemberModal, setShowRemoveMemberModal] = useState(false)
  const [memberToRemove, setMemberToRemove] = useState(null)
  const [isRemoving, setIsRemoving] = useState(false)
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [editedTeamName, setEditedTeamName] = useState('')

  const fetchTeamData = async () => {
    try {
      const [teamRes, userRes] = await Promise.all([
        axios.get(`/api/v1/teams/${teamId}`, { withCredentials: true }),
        axios.get('/api/v1/auth/me', { withCredentials: true })
      ])
      setTeam(teamRes.data)
      setMembers(teamRes.data.members || [])
      setCurrentUser(userRes.data)
    } catch (error) {
      console.error('Failed to fetch team data:', error)
      if (error.response?.status === 404) {
        toast.error('Team not found')
        navigate('/teams')
      }
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchTeamData()
  }, [teamId])

  const handleInviteUser = async (e) => {
    e.preventDefault()
    if (!inviteEmail.trim()) return

    try {
      await axios.post(
        `/api/v1/teams/${teamId}/invitations`,
        { invitee_email: inviteEmail, role: inviteRole },
        { withCredentials: true }
      )
      setInviteEmail('')
      setInviteRole('member')
      setShowInviteModal(false)
      toast.success('Invitation sent successfully!')
    } catch (error) {
      console.error('Failed to send invitation:', error)
      toast.error(error.response?.data?.detail || 'Failed to send invitation')
    }
  }

  const openRemoveMemberModal = (member) => {
    setMemberToRemove(member)
    setShowRemoveMemberModal(true)
  }

  const handleRemoveMember = async () => {
    if (!memberToRemove) return

    setIsRemoving(true)
    try {
      await axios.delete(`/api/v1/teams/${teamId}/members/${memberToRemove.id}`, {
        withCredentials: true,
      })
      setShowRemoveMemberModal(false)
      setMemberToRemove(null)
      fetchTeamData()
      toast.success('Member removed successfully')
    } catch (error) {
      console.error('Failed to remove member:', error)
      toast.error(error.response?.data?.detail || 'Failed to remove member')
    } finally {
      setIsRemoving(false)
    }
  }

  const handleEditTeam = async (e) => {
    e.preventDefault()
    if (!editedTeamName.trim()) return

    try {
      await axios.patch(
        `/api/v1/teams/${teamId}`,
        { name: editedTeamName },
        { withCredentials: true }
      )
      setShowEditDialog(false)
      fetchTeamData()
      toast.success('Team updated successfully!')
    } catch (error) {
      console.error('Failed to update team:', error)
      toast.error(error.response?.data?.detail || 'Failed to update team')
    }
  }

  const openEditDialog = () => {
    setEditedTeamName(team.name)
    setShowEditDialog(true)
  }

  if (loading) {
    return null;
  }

  if (!team) {
    return (
      <MainLayout activeTab="teams">
        <div className="text-center py-12">
          <p className="text-muted-foreground">Team not found</p>
        </div>
      </MainLayout>
    )
  }

  const currentUserMember = members.find(m => m.id === currentUser?.id)
  const isAdmin = currentUserMember?.role === 'administrator'

  return (
    <MainLayout activeTab="teams">
      <div className="py-6">
        {/* Header */}
        <div className="mb-12">
          <div className="flex justify-between items-center">
            <div>
              <Breadcrumb className="mb-4">
                <BreadcrumbList className="text-2xl">
                  <BreadcrumbItem>
                    <BreadcrumbLink href="/teams">Teams</BreadcrumbLink>
                  </BreadcrumbItem>
                  <BreadcrumbSeparator />
                  <BreadcrumbItem>
                    <BreadcrumbPage className="font-bold">{team.name}</BreadcrumbPage>
                  </BreadcrumbItem>
                </BreadcrumbList>
              </Breadcrumb>
            </div>
            {isAdmin && (
              <div className="flex gap-2">
                <button
                  onClick={openEditDialog}
                  className="px-4 py-2 bg-muted text-foreground rounded-md hover:bg-accent"
                >
                  Edit Team
                </button>
                <button
                  onClick={() => setShowInviteModal(true)}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90"
                >
                  Invite Member
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Members List */}
        <div className="bg-card border border-border rounded-lg shadow-sm">
          <div className="px-6 py-4 border-b border-border">
            <h2 className="text-xl font-semibold text-card-foreground">
              Members ({members.length})
            </h2>
          </div>
          <div className="divide-y divide-border">
            {members.length === 0 ? (
              <div className="px-6 py-8 text-center text-muted-foreground">
                No members yet. Invite someone to join this team!
              </div>
            ) : (
              members.map((member) => (
                <div
                  key={member.id}
                  className="px-6 py-4 flex justify-between items-center hover:bg-accent/50"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-primary flex items-center justify-center text-primary-foreground font-medium">
                      {member.username?.charAt(0).toUpperCase() || 'U'}
                    </div>
                    <div>
                      <p className="font-medium text-card-foreground">
                        {member.username}
                      </p>
                      <p className="text-sm text-muted-foreground">{member.email}</p>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    {member.role && (
                      <span className={`px-3 py-1 text-sm rounded-full ${
                        member.role === 'administrator'
                          ? 'bg-primary/10 text-primary'
                          : 'bg-muted text-muted-foreground'
                      }`}>
                        {member.role === 'administrator' ? 'Administrator' : 'Member'}
                      </span>
                    )}
                    {isAdmin && currentUser && member.id !== currentUser.id && (
                      <button
                        onClick={() => openRemoveMemberModal(member)}
                        className="px-3 py-1 text-sm text-destructive hover:bg-destructive/10 rounded-md"
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Invite User Modal */}
        {showInviteModal && (
          <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
            <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
              <h2 className="text-2xl font-bold mb-4 text-foreground">Invite Team Member</h2>
              <form onSubmit={handleInviteUser}>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Email Address
                  </label>
                  <input
                    type="email"
                    value={inviteEmail}
                    onChange={(e) => setInviteEmail(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                    placeholder="Enter email address"
                    autoFocus
                  />
                </div>
                <div className="mb-4">
                  <label className="block text-sm font-medium text-foreground mb-2">
                    Role
                  </label>
                  <select
                    value={inviteRole}
                    onChange={(e) => setInviteRole(e.target.value)}
                    className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  >
                    <option value="member">Member</option>
                    <option value="administrator">Administrator</option>
                  </select>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Administrators can manage team members and settings
                  </p>
                </div>
                <div className="flex gap-2 justify-end">
                  <button
                    type="button"
                    onClick={() => {
                      setShowInviteModal(false)
                      setInviteEmail('')
                      setInviteRole('member')
                    }}
                    className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-white/90"
                  >
                    Send Invitation
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Edit Team Dialog */}
        <Dialog open={showEditDialog} onOpenChange={setShowEditDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Edit Team</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleEditTeam}>
              <div className="mb-4">
                <label className="block text-sm font-medium text-foreground mb-2">
                  Team Name
                </label>
                <input
                  type="text"
                  value={editedTeamName}
                  onChange={(e) => setEditedTeamName(e.target.value)}
                  className="w-full px-3 py-2 bg-background border border-input rounded-md text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
                  placeholder="Enter team name"
                  autoFocus
                />
              </div>
              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setShowEditDialog(false)}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                >
                  Save Changes
                </Button>
              </DialogFooter>
            </form>
          </DialogContent>
        </Dialog>

        {/* Remove Member Confirmation Modal */}
        {showRemoveMemberModal && memberToRemove && (
          <div className="fixed inset-0 bg-black/50 dark:bg-black/80 flex items-center justify-center z-50">
            <div className="bg-background border border-border rounded-lg p-6 w-full max-w-md shadow-lg">
              <div className="flex items-start gap-3 mb-4">
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-red-100 dark:bg-red-900/20 flex items-center justify-center">
                  <AlertTriangle className="w-5 h-5 text-red-600 dark:text-red-400" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-foreground">Remove Member</h2>
                  <p className="mt-1 text-sm text-muted-foreground">
                    Are you sure you want to remove {memberToRemove.username} from this team?
                    They will lose access to all team resources.
                  </p>
                </div>
              </div>
              <div className="flex gap-2 justify-end">
                <button
                  type="button"
                  onClick={() => {
                    setShowRemoveMemberModal(false)
                    setMemberToRemove(null)
                  }}
                  className="px-4 py-2 text-foreground bg-muted rounded-md hover:bg-accent"
                  disabled={isRemoving}
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleRemoveMember}
                  className="px-4 py-2 bg-destructive text-destructive-foreground rounded-md hover:bg-destructive/90 disabled:opacity-50"
                  disabled={isRemoving}
                >
                  {isRemoving ? 'Removing...' : 'Remove'}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </MainLayout>
  )
}

export default TeamDetail
